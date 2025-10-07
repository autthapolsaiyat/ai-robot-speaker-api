#!/bin/bash
set -e

echo "=================================================="
echo "  AI Robot Speaker API - Automated Installation"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/8] Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python $required_version or higher is required (found $python_version)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"

# Check CUDA
echo -e "${YELLOW}[2/8] Checking CUDA availability...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name --format=csv,noheader
    echo -e "${GREEN}✓ CUDA available${NC}"
else
    echo -e "${YELLOW}⚠ CUDA not detected - will use CPU mode (slower)${NC}"
fi

# Check ffmpeg
echo -e "${YELLOW}[3/8] Checking ffmpeg...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg is required but not installed${NC}"
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  MacOS: brew install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    exit 1
fi
echo -e "${GREEN}✓ ffmpeg installed${NC}"

# Create virtual environment
echo -e "${YELLOW}[4/8] Creating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}[5/8] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install requirements
echo -e "${YELLOW}[6/8] Installing Python dependencies (this may take a while)...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Clone Wav2Lip
echo -e "${YELLOW}[7/8] Setting up Wav2Lip...${NC}"
if [ ! -d "Wav2Lip" ]; then
    git clone https://github.com/Rudrabha/Wav2Lip.git
    echo -e "${GREEN}✓ Wav2Lip cloned${NC}"
else
    echo -e "${GREEN}✓ Wav2Lip already exists${NC}"
fi

# Create directories
echo -e "${YELLOW}[8/8] Creating project directories...${NC}"
mkdir -p models assets out
echo -e "${GREEN}✓ Directories created${NC}"

# Download models
echo ""
echo -e "${YELLOW}=================================================${NC}"
echo -e "${YELLOW}  IMPORTANT: Manual Model Download Required${NC}"
echo -e "${YELLOW}=================================================${NC}"
echo ""
echo "Please download the following models manually:"
echo ""
echo "1. Wav2Lip GAN checkpoint:"
echo "   URL: https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth"
echo "   Save to: ./models/wav2lip_gan.pth"
echo ""
echo "2. Stable Diffusion XL Base (for face generation):"
echo "   URL: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
echo "   Save to: /models/sdxl/sd_xl_base_1.0"
echo "   (Use: git lfs clone or download manually)"
echo ""
echo "3. (Optional) SDXL Refiner:"
echo "   URL: https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0"
echo "   Save to: /models/sdxl/sd_xl_refiner_1.0"
echo ""

# Quick download helper
cat > download_models.sh << 'EOF'
#!/bin/bash
echo "Downloading Wav2Lip checkpoint..."
cd models
wget -c https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth
echo "✓ Wav2Lip model downloaded"
cd ..

echo ""
echo "For SDXL models, install git-lfs first:"
echo "  sudo apt-get install git-lfs"
echo "  git lfs install"
echo ""
echo "Then clone SDXL models:"
echo "  cd /models"
echo "  mkdir -p sdxl && cd sdxl"
echo "  git lfs clone https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
EOF
chmod +x download_models.sh

echo -e "${GREEN}Run './download_models.sh' to download Wav2Lip model${NC}"
echo ""

# Create sample assets
echo "Creating sample configuration files..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# FastAPI server
HOST=0.0.0.0
PORT=4187

# Paths
DATA_DIR=out
ASSETS_DIR=assets
MODELS_DIR=models
WAV2LIP_DIR=Wav2Lip

# Defaults
DEFAULT_VOICE=thai_male
DEFAULT_FACE_PRESET=robot_mesh_hologram

# TTS models (Coqui)
DEFAULT_TTS_MODEL_EN=tts_models/en/vctk/vits
DEFAULT_TTS_MODEL_MULTI=tts_models/multilingual/multi-dataset/ bark

# Whisper
DEFAULT_WHISPER_MODEL=small

# Default assets
DEFAULT_ROBOT_FACE=assets/robot_face.jpg
DEFAULT_TEACHER_VIDEO=assets/teacher_raw.mp4

# SDXL (adjust paths as needed)
SDXL_BASE=/models/sdxl/sd_xl_base_1.0
SDXL_REFINER=/models/sdxl/sd_xl_refiner_1.0

# Security
MAX_TEXT_LENGTH=10000
MAX_JOB_AGE_HOURS=24
ENABLE_AUDIT_LOG=true
EOF
    echo -e "${GREEN}✓ .env created${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

if [ ! -f "voice_config.json" ]; then
    cat > voice_config.json << 'EOF'
{
  "default": {
    "model": "tts_models/multilingual/multi-dataset/bark",
    "speaker": null,
    "speed": 1.0,
    "pitch": 0.0
  },
  "thai_male": {
    "model": "tts_models/multilingual/multi-dataset/bark",
    "speaker": "v2/th_speaker_0",
    "speed": 1.0,
    "pitch": 0.0
  },
  "thai_female": {
    "model": "tts_models/multilingual/multi-dataset/bark",
    "speaker": "v2/th_speaker_1",
    "speed": 1.05,
    "pitch": 2.0
  },
  "en_male": {
    "model": "tts_models/en/vctk/vits",
    "speaker": "p225",
    "speed": 1.0,
    "pitch": 0.0
  },
  "en_female": {
    "model": "tts_models/en/vctk/vits",
    "speaker": "p226",
    "speed": 1.0,
    "pitch": 0.0
  }
}
EOF
    echo -e "${GREEN}✓ voice_config.json created${NC}"
fi

if [ ! -f "face_presets.json" ]; then
    cat > face_presets.json << 'EOF'
{
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
  },
  "robot_police_unit": {
    "prompt": "law enforcement service robot head, matte dark navy shell with white accents, abstract motif, soft visor, respectful and trustworthy look, studio lighting, portrait",
    "negative": "real police badge, real logos, human face, text, watermark",
    "width": 768,
    "height": 1024,
    "steps": 30,
    "guidance": 7.0,
    "seed": 91542
  },
  "robot_holo_wireframe": {
    "prompt": "holographic wireframe robot head, neon edges, volumetric glow, translucent, grid nodes, neutral expression, black background, high contrast, sci-fi UI aesthetic",
    "negative": "human face, text, watermark, lowres, noisy",
    "width": 896,
    "height": 896,
    "steps": 26,
    "guidance": 6.0,
    "seed": 60333
  },
  "robot_medical_clean": {
    "prompt": "clean white medical assistant android head, smooth ceramic shell, subtle cyan diagnostic LEDs, calm neutral expression, softbox lighting, clinical background bokeh",
    "negative": "human skin, text, watermark, lowres",
    "width": 768,
    "height": 1024,
    "steps": 28,
    "guidance": 6.5,
    "seed": 44110
  }
}
EOF
    echo -e "${GREEN}✓ face_presets.json created${NC}"
fi

echo ""
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Download required models:"
echo "   ./download_models.sh"
echo ""
echo "2. (Optional) Add sample robot face image:"
echo "   cp your_robot_face.jpg assets/robot_face.jpg"
echo ""
echo "3. Start the server:"
echo "   source .venv/bin/activate"
echo "   python main.py"
echo ""
echo "4. Or use uvicorn directly:"
echo "   uvicorn main:app --host 0.0.0.0 --port 4187 --reload"
echo ""
echo "5. Test the API:"
echo "   curl http://localhost:4187/health"
echo ""
echo "6. Access documentation:"
echo "   http://localhost:4187/docs"
echo ""
echo -e "${YELLOW}Note: First run will download TTS models (~500MB)${NC}"
echo ""
