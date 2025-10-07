"""
AI Robot Speaker API - Production Ready
Full-featured TTS + Lip-sync + Face Generation API
Security-hardened, monitored, production-ready
"""

import os
import sys
import uuid
import json
import shutil
import subprocess
import logging
import time
import resource
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Literal, Dict, Any
from contextlib import asynccontextmanager

import torch
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 4187))
DATA_DIR = Path(os.getenv("DATA_DIR", "out"))
ASSETS_DIR = Path(os.getenv("ASSETS_DIR", "assets"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))
WAV2LIP_DIR = Path(os.getenv("WAV2LIP_DIR", "Wav2Lip"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", "static"))

# Defaults
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "thai_male")
DEFAULT_FACE_PRESET = os.getenv("DEFAULT_FACE_PRESET", "robot_mesh_hologram")
DEFAULT_TTS_MODEL_EN = os.getenv("DEFAULT_TTS_MODEL_EN", "tts_models/en/vctk/vits")
DEFAULT_TTS_MODEL_MULTI = os.getenv("DEFAULT_TTS_MODEL_MULTI", "tts_models/multilingual/multi-dataset/vits-multilingual")
DEFAULT_WHISPER_MODEL = os.getenv("DEFAULT_WHISPER_MODEL", "small")
DEFAULT_ROBOT_FACE = Path(os.getenv("DEFAULT_ROBOT_FACE", "assets/robot_face.jpg"))
DEFAULT_TEACHER_VIDEO = Path(os.getenv("DEFAULT_TEACHER_VIDEO", "assets/teacher_raw.mp4"))

# SDXL paths
SDXL_BASE = os.getenv("SDXL_BASE", "/models/sdxl/sd_xl_base_1.0")
SDXL_REFINER = os.getenv("SDXL_REFINER", "/models/sdxl/sd_xl_refiner_1.0")

# Security
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 10000))
MAX_JOB_AGE_HOURS = int(os.getenv("MAX_JOB_AGE_HOURS", 24))
ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# LOGGING & AUDIT
# ============================================================================

# Main logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Audit logger
class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("audit.log")
        handler.setFormatter(logging.Formatter(
            '{"timestamp":"%(asctime)s","job_id":"%(job_id)s","event":"%(event)s","details":%(details)s}'
        ))
        self.logger.addHandler(handler)
    
    def log(self, job_id: str, event: str, **details):
        if ENABLE_AUDIT_LOG:
            self.logger.info("", extra={
                "job_id": job_id,
                "event": event,
                "details": json.dumps(details)
            })

audit = AuditLogger()

# ============================================================================
# SECURITY
# ============================================================================

class SecurityValidator:
    BANNED_FACE_TERMS = [
        "celebrity", "politician", "public figure", "famous person",
        "trump", "biden", "obama", "putin", "xi jinping"
    ]
    
    @staticmethod
    def validate_text(text: str) -> str:
        """Sanitize and validate input text"""
        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long (max {MAX_TEXT_LENGTH} chars)")
        return text.strip()
    
    @staticmethod
    def validate_path(path: str, allowed_dir: Path) -> Path:
        """Prevent path traversal attacks"""
        if not path:
            return None
        resolved = Path(path).resolve()
        allowed_resolved = allowed_dir.resolve()
        if not str(resolved).startswith(str(allowed_resolved)):
            raise ValueError(f"Path must be within {allowed_dir}")
        if not resolved.exists():
            raise ValueError(f"File not found: {path}")
        return resolved
    
    @staticmethod
    def validate_face_prompt(prompt: str) -> bool:
        """Check for banned terms in face generation prompts"""
        if not prompt:
            return True
        lower = prompt.lower()
        for term in SecurityValidator.BANNED_FACE_TERMS:
            if term in lower:
                raise ValueError(
                    f"Cannot generate faces resembling real people. "
                    f"Banned term detected: '{term}'. "
                    f"Please use generic descriptions only."
                )
        return True

security = SecurityValidator()

# ============================================================================
# JOB MANAGEMENT
# ============================================================================

class JobState:
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir
        self.state_file = job_dir / "state.json"
        self.job_dir.mkdir(parents=True, exist_ok=True)
    
    def update(self, **kwargs):
        data = {}
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
        data.update(kwargs)
        data["updated_at"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(data, indent=2))
    
    def step(self, step_name: str, **extra):
        data = json.loads(self.state_file.read_text()) if self.state_file.exists() else {}
        steps = data.get("steps", [])
        steps.append({
            "name": step_name,
            "timestamp": datetime.now().isoformat(),
            **extra
        })
        data["steps"] = steps
        self.state_file.write_text(json.dumps(data, indent=2))
        logger.info(f"Step: {step_name} {extra}")

class JobManager:
    @staticmethod
    def cleanup_old_jobs(max_age_hours: int = MAX_JOB_AGE_HOURS):
        """Remove jobs older than specified hours"""
        cutoff = time.time() - (max_age_hours * 3600)
        cleaned = 0
        for job_dir in DATA_DIR.iterdir():
            if job_dir.is_dir():
                state_file = job_dir / "state.json"
                if state_file.exists():
                    mtime = state_file.stat().st_mtime
                    if mtime < cutoff:
                        try:
                            shutil.rmtree(job_dir)
                            cleaned += 1
                            logger.info(f"Cleaned old job: {job_dir.name}")
                        except Exception as e:
                            logger.error(f"Failed to clean {job_dir.name}: {e}")
        return cleaned
    
    @staticmethod
    def get_job_status(job_id: str) -> Dict:
        state_file = DATA_DIR / job_id / "state.json"
        if not state_file.exists():
            raise HTTPException(404, "Job not found")
        return json.loads(state_file.read_text())
    
    @staticmethod
    def cancel_job(job_id: str):
        state_file = DATA_DIR / job_id / "state.json"
        if not state_file.exists():
            raise HTTPException(404, "Job not found")
        data = json.loads(state_file.read_text())
        data["status"] = "cancelled"
        data["cancelled_at"] = datetime.now().isoformat()
        state_file.write_text(json.dumps(data, indent=2))
        audit.log(job_id, "job_cancelled")

job_manager = JobManager()

# ============================================================================
# MODELS & RESOURCES
# ============================================================================

# Lazy-loaded singletons
_TTS_MODEL = None
_WHISPER_MODEL = None
_FACE_GEN = None

def get_tts_model():
    global _TTS_MODEL
    if _TTS_MODEL is None:
        from TTS.api import TTS
        _TTS_MODEL = TTS(DEFAULT_TTS_MODEL_MULTI)
        logger.info("TTS model loaded")
    return _TTS_MODEL

def get_whisper_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        import whisper
        _WHISPER_MODEL = whisper.load_model(DEFAULT_WHISPER_MODEL)
        logger.info("Whisper model loaded")
    return _WHISPER_MODEL

class FaceGenerator:
    def __init__(self, base_path: str, refiner_path: Optional[str] = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Face generator using device: {self.device}")
        
        from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
        
        self.base = StableDiffusionXLPipeline.from_pretrained(
            base_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            use_safetensors=True
        ).to(self.device)
        
        self.refiner = None
        if refiner_path and Path(refiner_path).exists():
            self.refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                refiner_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True
            ).to(self.device)
        
        logger.info("Face generator initialized")

def get_face_gen():
    global _FACE_GEN
    if _FACE_GEN is None:
        if not Path(SDXL_BASE).exists():
            raise RuntimeError(f"SDXL base model not found at {SDXL_BASE}")
        _FACE_GEN = FaceGenerator(SDXL_BASE, SDXL_REFINER)
    return _FACE_GEN

# ============================================================================
# CONFIG FILES
# ============================================================================

def load_json_config(filename: str, default: dict) -> dict:
    path = Path(filename)
    if path.exists():
        return json.loads(path.read_text())
    return default

VOICE_CONFIG = load_json_config("voice_config.json", {
    "default": {"model": DEFAULT_TTS_MODEL_MULTI, "speaker": None, "speed": 1.0, "pitch": 0.0},
    "thai_male": {"model": DEFAULT_TTS_MODEL_MULTI, "speaker": "p225", "speed": 1.0, "pitch": 0.0},
    "thai_female": {"model": DEFAULT_TTS_MODEL_MULTI, "speaker": "p226", "speed": 1.05, "pitch": 2.0}
})

FACE_PRESETS = load_json_config("face_presets.json", {
    "robot_mesh_hologram": {
        "prompt": "futuristic robot head, translucent polygonal mesh skull, glowing circuits, holographic cheek panels, neutral expression, studio lighting, high detail, ultra sharp, cinematic portrait, centered, looking at camera",
        "negative": "human skin, realistic human, text, watermark, logo, extra limbs, deformed, lowres, blurry",
        "width": 768,
        "height": 1024,
        "steps": 28,
        "guidance": 6.5,
        "seed": 342211
    },
    "robot_carbon_fiber": {
        "prompt": "sleek android head made of carbon fiber and brushed titanium, segmented plates, subtle blue LED seams, neutral expression, studio rim light, product photo, 85mm portrait",
        "negative": "human skin, gore, text, watermark, extra fingers, lowres",
        "width": 768,
        "height": 1024,
        "steps": 28,
        "guidance": 6.5,
        "seed": 775001
    }
})

# ============================================================================
# PROCESSING FUNCTIONS
# ============================================================================

def synthesize_tts(text: str, lang: str, out_wav: Path, model: str = None, 
                   speaker: str = None, speed: float = 1.0, pitch: float = 0.0):
    """Generate speech from text"""
    tts = get_tts_model()
    
    # Try with language parameter first (multi-lingual models)
    try:
        tts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker=speaker,
            language=lang
        )
    except (ValueError, TypeError):
        # Fall back for single-language models
        tts.tts_to_file(
            text=text,
            file_path=str(out_wav),
            speaker=speaker
        )
    
    logger.info(f"TTS completed: {out_wav}")

def lipsync(face_path: Path, audio_path: Path, out_video: Path, checkpoint: Path):
    """Generate lip-synced video using Wav2Lip"""
    # Ensure temp directory exists
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    # Use absolute paths
    face_abs = face_path.resolve()
    audio_abs = audio_path.resolve()
    video_abs = out_video.resolve()
    checkpoint_abs = checkpoint.resolve()
    
    cmd = [
        "python", "inference.py",
        "--checkpoint_path", str(checkpoint_abs),
        "--face", str(face_abs),
        "--audio", str(audio_abs),
        "--outfile", str(video_abs)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WAV2LIP_DIR))
    
    if result.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed: {result.stderr}")
    
    if not out_video.exists():
        raise RuntimeError(f"Output video not created: {out_video}")
    
    logger.info(f"Lip-sync completed: {out_video}")

def make_subtitles(audio_path: Path, job_dir: Path, model_name: str):
    """Generate subtitles using Whisper"""
    model = get_whisper_model()
    result = model.transcribe(str(audio_path))
    
    # Generate SRT
    srt_en = job_dir / "captions_en.srt"
    with open(srt_en, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(result['segments'], 1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    
    logger.info(f"Subtitles generated: {srt_en}")

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def split_and_burn(robot_video: Path, teacher_video: Path, srt_en: Path, 
                   srt_th: Path, out_final: Path):
    """Combine videos side-by-side and burn subtitles"""
    # Simplified ffmpeg command - adjust as needed
    cmd = [
        "ffmpeg", "-y",
        "-i", str(robot_video),
        "-i", str(teacher_video),
        "-filter_complex", "[0:v][1:v]hstack=inputs=2[v]",
        "-map", "[v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        str(out_final)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Video composition failed: {result.stderr}")
    logger.info(f"Final video created: {out_final}")

def ensure_face_from_preset(job_dir: Path, preset_name: str) -> Path:
    """Generate face from preset configuration"""
    preset = FACE_PRESETS.get(preset_name)
    if not preset:
        raise HTTPException(400, f"Unknown face preset: {preset_name}")
    
    security.validate_face_prompt(preset.get("prompt", ""))
    
    out_png = job_dir / "robot_face.png"
    gen = get_face_gen()
    
    g = None
    if preset.get("seed") is not None:
        g = torch.Generator(gen.device).manual_seed(int(preset["seed"]))
    
    img = gen.base(
        prompt=preset.get("prompt", "portrait"),
        negative_prompt=preset.get("negative", ""),
        num_inference_steps=int(preset.get("steps", 28)),
        guidance_scale=float(preset.get("guidance", 6.5)),
        width=int(preset.get("width", 768)),
        height=int(preset.get("height", 1024)),
        generator=g
    ).images[0]
    
    if gen.refiner:
        img = gen.refiner(
            image=img,
            prompt=preset.get("prompt", "portrait"),
            strength=0.25,
            num_inference_steps=15
        ).images[0]
    
    img.save(out_png)
    logger.info(f"Face generated from preset '{preset_name}': {out_png}")
    return out_png

# ============================================================================
# API MODELS
# ============================================================================

class SpeakIn(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)
    lang: Literal["en", "th"] = "th"
    mode: Literal["robot_only", "split_screen"] = "robot_only"
    robot_face: Optional[str] = None
    face_preset: Optional[str] = None
    teacher_video: Optional[str] = None
    voice: Optional[str] = None
    speaker: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0)
    tts_model: Optional[str] = None
    whisper_model: Optional[str] = None
    
    @validator('text')
    def validate_text(cls, v):
        return security.validate_text(v)

class JobOut(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    files: Dict[str, str] = {}
    error: Optional[str] = None

class FaceGenIn(BaseModel):
    prompt: Optional[str] = None
    preset: Optional[str] = None
    negative: Optional[str] = None
    seed: Optional[int] = None
    width: int = Field(default=768, ge=512, le=1024)
    height: int = Field(default=1024, ge=512, le=1024)
    steps: int = Field(default=28, ge=15, le=50)
    guidance: float = Field(default=6.5, ge=1.0, le=15.0)
    
    @validator('prompt')
    def validate_prompt(cls, v, values):
        if v:
            security.validate_face_prompt(v)
        return v

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    checks: Dict[str, Any]

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Robot Speaker API...")
    logger.info(f"GPU available: {torch.cuda.is_available()}")
    logger.info(f"Data directory: {DATA_DIR.resolve()}")
    
    # Cleanup old jobs on startup
    cleaned = job_manager.cleanup_old_jobs()
    logger.info(f"Cleaned {cleaned} old jobs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="AI Robot Speaker API",
    description="Production-ready TTS + Lip-sync + Face Generation API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["General"])
def root():
    """Serve web UI if available, otherwise return API info"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "AI Robot Speaker API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "web_ui": "/static/index.html"
    }
@app.get("/health", response_model=HealthCheck, tags=["General"])
def health_check():
    """System health check"""
    disk_usage = shutil.disk_usage(DATA_DIR)
    
    checks = {
        "gpu_available": torch.cuda.is_available(),
        "cuda_available": torch.cuda.is_available(),
        "wav2lip_model": (MODELS_DIR / "wav2lip_gan.pth").exists(),
        "sdxl_model": Path(SDXL_BASE).exists(),
        "disk_free_gb": round(disk_usage.free / (1024**3), 2),
        "disk_used_percent": round(disk_usage.used / disk_usage.total * 100, 1)
    }
    
    status = "ok" if all([
        checks["wav2lip_model"],
        checks["disk_free_gb"] > 1.0
    ]) else "degraded"
    
    return HealthCheck(
        status=status,
        timestamp=datetime.now().isoformat(),
        checks=checks
    )

@app.get("/api/v1/voices", tags=["Config"])
def list_voices():
    """List available voice presets"""
    return {"voices": list(VOICE_CONFIG.keys())}

@app.get("/api/v1/face/presets", tags=["Config"])
def list_face_presets():
    """List available face presets"""
    return {"presets": list(FACE_PRESETS.keys())}

@app.post("/api/v1/face/generate", response_model=JobOut, tags=["Face Generation"])
def generate_face(req: FaceGenIn):
    """Generate synthetic face from text or preset"""
    job_id = uuid.uuid4().hex[:10]
    job_dir = DATA_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    js = JobState(job_dir)
    js.update(status="processing", progress=0)
    audit.log(job_id, "face_generation_start", preset=req.preset, has_custom_prompt=bool(req.prompt))
    
    try:
        # Resolve parameters
        if req.preset:
            preset = FACE_PRESETS.get(req.preset)
            if not preset:
                raise HTTPException(400, f"Unknown preset: {req.preset}")
            prompt = req.prompt or preset.get("prompt")
            negative = req.negative or preset.get("negative")
            width = req.width if req.width != 768 else preset.get("width", 768)
            height = req.height if req.height != 1024 else preset.get("height", 1024)
            steps = req.steps if req.steps != 28 else preset.get("steps", 28)
            guidance = req.guidance if req.guidance != 6.5 else preset.get("guidance", 6.5)
            seed = req.seed if req.seed is not None else preset.get("seed")
        else:
            if not req.prompt:
                raise HTTPException(400, "Either 'prompt' or 'preset' is required")
            prompt = req.prompt
            negative = req.negative or ""
            width, height, steps, guidance, seed = req.width, req.height, req.steps, req.guidance, req.seed
        
        security.validate_face_prompt(prompt)
        
        out_png = job_dir / "robot_face.png"
        gen = get_face_gen()
        
        g = None
        if seed is not None:
            g = torch.Generator(gen.device).manual_seed(seed)
        
        img = gen.base(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=g
        ).images[0]
        
        if gen.refiner:
            img = gen.refiner(image=img, prompt=prompt, strength=0.25, num_inference_steps=15).images[0]
        
        img.save(out_png)
        
        js.update(status="done", progress=100, files={"image": str(out_png)})
        audit.log(job_id, "face_generation_complete")
        
        return JobOut(job_id=job_id, status="done", progress=100, files={"image": str(out_png)})
    
    except Exception as e:
        logger.error(f"Face generation failed: {e}", exc_info=True)
        js.update(status="error", progress=100, error=str(e))
        audit.log(job_id, "face_generation_error", error=str(e))
        raise HTTPException(500, f"Face generation failed: {e}")

@app.post("/api/v1/speak", response_model=JobOut, tags=["Speech"])
def speak(req: SpeakIn, background_tasks: BackgroundTasks):
    """Generate speech video with optional face generation"""
    job_id = uuid.uuid4().hex[:10]
    job_dir = DATA_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    js = JobState(job_dir)
    js.update(status="queued", progress=0, request=req.dict())
    audit.log(job_id, "job_created", text_length=len(req.text), mode=req.mode, voice=req.voice or DEFAULT_VOICE)
    
    def worker():
        try:
            js.update(status="processing", progress=5)
            
            # 0) Determine face
            if req.robot_face:
                face = security.validate_path(req.robot_face, ASSETS_DIR)
            elif req.face_preset:
                js.step("facegen:start", preset=req.face_preset)
                face = ensure_face_from_preset(job_dir, req.face_preset)
                js.update(progress=20)
            elif DEFAULT_FACE_PRESET:
                js.step("facegen:start", preset=DEFAULT_FACE_PRESET)
                face = ensure_face_from_preset(job_dir, DEFAULT_FACE_PRESET)
                js.update(progress=20)
            else:
                face = DEFAULT_ROBOT_FACE
            
            # Prepare outputs
            out_wav = job_dir / "voice.wav"
            robot_mp4 = job_dir / "robot_talk.mp4"
            out_final = job_dir / ("final.mp4" if req.mode == "robot_only" else "final_split_subbed.mp4")
            
            # 1) TTS
            js.step("tts:start")
            voice_preset = VOICE_CONFIG.get(req.voice or DEFAULT_VOICE, VOICE_CONFIG["default"])
            synthesize_tts(
                req.text, req.lang, out_wav,
                model=req.tts_model or voice_preset.get("model"),
                speaker=req.speaker or voice_preset.get("speaker"),
                speed=req.speed if req.speed != 1.0 else voice_preset.get("speed", 1.0),
                pitch=req.pitch if req.pitch != 0.0 else voice_preset.get("pitch", 0.0)
            )
            js.step("tts:done")
            js.update(progress=40)
            
            # 2) Lip-sync
            js.step("lipsync:start")
            lipsync(face, out_wav, robot_mp4, MODELS_DIR / "wav2lip_gan.pth")
            js.step("lipsync:done")
            js.update(progress=70)
            
            # 3) Final output
            if req.mode == "robot_only":
                shutil.copy(robot_mp4, out_final)
                js.update(status="completed", progress=100, files={"video": str(out_final)}, message="Video ready!")
            else:
                # Generate subtitles
                js.step("subtitles:start")
                make_subtitles(out_wav, job_dir, req.whisper_model or DEFAULT_WHISPER_MODEL)
                js.update(progress=85)
                
                # Composite
                js.step("composite:start")
                teacher = security.validate_path(req.teacher_video, ASSETS_DIR) if req.teacher_video else DEFAULT_TEACHER_VIDEO
                split_and_burn(robot_mp4, teacher, job_dir / "captions_en.srt", None, out_final)
                js.update(status="completed", progress=100, files={"video": str(out_final)}, message="Video ready!")
            
            audit.log(job_id, "job_complete", output=str(out_final))
        
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            js.update(status="failed", progress=100, error=str(e), message=f"Error: {str(e)}")
            audit.log(job_id, "job_error", error=str(e))
    
    background_tasks.add_task(worker)
    return JobOut(job_id=job_id, status="queued", progress=0)

@app.get("/api/v1/jobs/{job_id}", response_model=JobOut, tags=["Jobs"])
def get_job_status(job_id: str):
    """Get job status"""
    data = job_manager.get_job_status(job_id)
    return JobOut(
        job_id=job_id,
        status=data.get("status", "unknown"),
        progress=data.get("progress", 0),
        files=data.get("files", {}),
        error=data.get("error")
    )

@app.delete("/api/v1/jobs/{job_id}", tags=["Jobs"])
def cancel_job(job_id: str):
    """Cancel a job"""
    job_manager.cancel_job(job_id)
    return {"status": "cancelled", "job_id": job_id}

@app.get("/api/v1/jobs/{job_id}/result", tags=["Jobs"])
def get_job_result(job_id: str):
    """Download job result"""
    job_dir = DATA_DIR / job_id
    
    # Try different filenames
    for filename in ["final_split_subbed.mp4", "final.mp4", "robot_talk.mp4", "robot_face.png"]:
        file_path = job_dir / filename
        if file_path.exists():
            return FileResponse(
                str(file_path),
                media_type="video/mp4" if filename.endswith(".mp4") else "image/png",
                filename=filename
            )
    
    raise HTTPException(404, "Result not ready or not found")

@app.post("/api/v1/admin/cleanup", tags=["Admin"])
def cleanup_old_jobs():
    """Manually trigger cleanup of old jobs"""
    cleaned = job_manager.cleanup_old_jobs()
    return {"cleaned": cleaned, "max_age_hours": MAX_JOB_AGE_HOURS}

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
