# AI Robot Speaker API

Text-to-Speech API with Lip-sync for automatic video narration generation.

## 🎯 Features

- **Text-to-Speech**: English (Coqui TTS), Thai (gTTS)
- **Lip-sync**: Wav2Lip for realistic mouth movements
- **Video Generation**: Automatic robot face video creation
- **FastAPI Backend**: RESTful API with async processing
- **GPU Acceleration**: CUDA support for faster processing

## 🖥️ Server Specs

- **OS**: Ubuntu 22.04
- **GPU**: RTX 3060 12GB VRAM
- **Python**: 3.10+
- **API Port**: 4188

## 🚀 Quick Start

### Prerequisites
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3.10 python3-pip python3-venv ffmpeg espeak-ng
# 🤖 AI Robot Speaker API

API สำหรับสร้างวิดีโอหุ่นยนต์พูดภาษาไทยและอังกฤษ พร้อมระบบ Text-to-Speech และ Lip Sync

## 📋 สารบัญ

- [คุณสมบัติ](#-คุณสมบัติ)
- [ข้อมูลเซิร์ฟเวอร์](#️-ข้อมูลเซิร์ฟเวอร์)
- [การติดตั้ง](#-การติดตั้ง)
- [API Endpoints](#-api-endpoints)
- [การใช้งาน](#-การใช้งาน)
- [อัปเดตล่าสุด](#-อัปเดตล่าสุด)
- [Quick Commands](#-quick-commands)
- [Troubleshooting](#-troubleshooting)

## ✨ คุณสมบัติ

- 🎙️ **Text-to-Speech** - แปลงข้อความเป็นเสียงพูด (ไทย/อังกฤษ)
- 🎬 **Video Generation** - สร้างวิดีโอหุ่นยนต์พูดพร้อม Lip Sync
- 🔊 **Multiple Voices** - รองรับหลายเสียง (th-TH-PremwadeeNeural, en-US-JennyNeural)
- 📱 **Web UI** - อินเทอร์เฟซเว็บสำหรับสร้างและจัดการวิดีโอ
- 🖼️ **Gallery System** - ระบบแกลเลอรี่แสดงผลงานทั้งหมด
- ♻️ **Auto Refresh** - โหลดข้อมูลอัตโนมัติทุก 30 วินาที
- 🌐 **Remote Access** - เข้าถึงได้ผ่าน Internet ด้วย ZeroTier

## 🖥️ ข้อมูลเซิร์ฟเวอร์

### Network Configuration

| ประเภท | ข้อมูล |
|--------|---------|
| **LAN IP** | `192.168.1.59` |
| **ZeroTier IP** | `10.147.19.244` |
| **API Port** | `4188` |
| **ZeroTier Network ID** | `1d71939404df6249` |
| **Network Name** | `adoring_tattam` |

### Server Specs

- **OS**: Ubuntu Linux
- **Python**: 3.10+
- **Virtual Environment**: `.venv`
- **Working Directory**: `~/ai-robot-speaker-api`

## 🚀 การติดตั้ง

### 1. Clone Repository

```bash
git clone https://github.com/autthapolsaiyat/ai-robot-speaker-api.git
cd ai-robot-speaker-api
```

### 2. ติดตั้ง Dependencies

```bash
# สร้าง Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# ติดตั้ง packages
pip install -r requirements.txt
```

### 3. เริ่มต้น Server

```bash
# ใช้ start script
./start_server.sh

# หรือรันแบบ manual
python main.py
```

## 📡 API Endpoints

### Health Check

```http
GET /health
```

ตรวจสอบสถานะเซิร์ฟเวอร์

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-08T10:30:00Z"
}
```

### สร้างงานใหม่

```http
POST /api/v1/jobs
Content-Type: application/json
```

สร้างงานสร้างวิดีโอใหม่

**Request Body:**
```json
{
  "text": "สวัสดีครับ ยินดีต้อนรับ",
  "lang": "th",
  "voice": "th-TH-PremwadeeNeural"
}
```

**Response:**
```json
{
  "job_id": "job_20251008_103045_abc123",
  "status": "created"
}
```

### ดึงรายการงานทั้งหมด ⭐ NEW

```http
GET /api/v1/jobs/list?limit=100&sort=desc
```

ดึงรายการวิดีโอทั้งหมดที่สร้างเสร็จแล้ว

**Parameters:**
- `limit` (optional): จำนวนผลลัพธ์สูงสุด (default: 100)
- `sort` (optional): `asc` หรือ `desc` (default: desc)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_20251008_103045_abc123",
      "text": "สวัสดีครับ ยินดีต้อนรับ",
      "lang": "th",
      "voice": "th-TH-PremwadeeNeural",
      "created_at": "2025-10-08T10:30:45Z",
      "video_file": "final_split_subbed.mp4"
    }
  ],
  "count": 1
}
```

### ดูสถานะงาน

```http
GET /api/v1/jobs/{job_id}/state
```

ตรวจสอบสถานะการทำงาน

**Response:**
```json
{
  "job_id": "job_20251008_103045_abc123",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-10-08T10:30:45Z",
  "updated_at": "2025-10-08T10:32:15Z"
}
```

### ดาวน์โหลดวิดีโอ

```http
GET /api/v1/jobs/{job_id}/download
```

ดาวน์โหลดไฟล์วิดีโอที่สร้างเสร็จแล้ว

## 💻 การใช้งาน

### ผ่าน Web UI

เปิดเบราว์เซอร์และเข้าที่:

```
http://10.147.19.244:4188/static/appindex.html
```

**คุณสมบัติ Web UI:**
- ✍️ กรอกข้อความที่ต้องการให้หุ่นยนต์พูด
- 🌍 เลือกภาษา (ไทย/อังกฤษ)
- 🎤 เลือกเสียงที่ต้องการ
- 📹 ดูแกลเลอรี่วิดีโอทั้งหมด
- 🔄 Auto-refresh ทุก 30 วินาที
- ⬇️ ดาวน์โหลดวิดีโอ

### ผ่าน Command Line

```bash
# สร้างวิดีโอภาษาไทย
curl -X POST http://10.147.19.244:4188/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "text": "สวัสดีครับ วันนี้อากาศดีมาก",
    "lang": "th",
    "voice": "th-TH-PremwadeeNeural"
  }'

# สร้างวิดีโอภาษาอังกฤษ
curl -X POST http://10.147.19.244:4188/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello World, this is a test",
    "lang": "en",
    "voice": "en-US-JennyNeural"
  }'

# ดูรายการทั้งหมด
curl http://10.147.19.244:4188/api/v1/jobs/list

# Health check
curl http://10.147.19.244:4188/health
```

### SSH เข้า Server

```bash
ssh ai-roboot@10.147.19.244
```

## 🔄 อัปเดตล่าสุด (8 ต.ค. 2568)

### ✅ สิ่งที่ทำสำเร็จวันนี้

| ลำดับ | งาน | สถานะ |
|-------|-----|--------|
| 1 | แก้ไข Port Conflict (4188) | ✅ |
| 2 | ตั้งค่า Static IP (192.168.1.59) | ✅ |
| 3 | ติดตั้ง ZeroTier Network | ✅ |
| 4 | เชื่อมต่อ Mac-Server ผ่าน Internet | ✅ |
| 5 | ทดสอบระบบภาษาไทยสำเร็จ | ✅ |
| 6 | Backup โปรเจกต์ขึ้น GitHub | ✅ |

### 🆕 Backend Changes

**เพิ่ม API Endpoint: `GET /api/v1/jobs/list`**

```python
@app.get("/api/v1/jobs/list", tags=["Jobs"])
def list_jobs(limit: int = 100, sort: str = "desc"):
    """List all available jobs sorted by date"""
    try:
        jobs = []
        
        if not DATA_DIR.exists():
            return {"jobs": []}
        
        for job_dir in DATA_DIR.iterdir():
            if not job_dir.is_dir():
                continue
                
            state_file = job_dir / "state.json"
            if not state_file.exists():
                continue
            
            try:
                state_data = json.loads(state_file.read_text())
                
                video_file = None
                for filename in ["final_split_subbed.mp4", "final.mp4", "robot_talk.mp4"]:
                    potential_file = job_dir / filename
                    if potential_file.exists():
                        video_file = filename
                        break
                
                if video_file and state_data.get("status") == "completed":
                    jobs.append({
                        "job_id": job_dir.name,
                        "text": state_data.get("request", {}).get("text", "No text"),
                        "lang": state_data.get("request", {}).get("lang", "unknown"),
                        "voice": state_data.get("request", {}).get("voice", "default"),
                        "created_at": state_data.get("updated_at", state_data.get("created_at", "")),
                        "video_file": video_file
                    })
            except Exception as e:
                logger.error(f"Failed to read job {job_dir.name}: {e}")
                continue
        
        jobs.sort(key=lambda x: x["created_at"], reverse=(sort == "desc"))
        jobs = jobs[:limit]
        
        return {"jobs": jobs, "count": len(jobs)}
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(500, f"Failed to list jobs: {e}")
```

**คุณสมบัติ:**
- 🔍 สแกนโฟลเดอร์ `out/` หา jobs ทั้งหมด
- 📊 ส่งข้อมูล: job_id, text, lang, voice, created_at
- 🎯 Filter เฉพาะงานที่ status = "completed"
- 📹 ตรวจสอบไฟล์วิดีโอหลายรูปแบบ
- 📑 รองรับ pagination และ sorting

### 🎨 Frontend Changes

**ปรับปรุง Web UI:**
- ❌ ลบการใช้ localStorage
- 🔗 โหลด Gallery จาก API โดยตรง
- 🔄 Auto-refresh ทุก 30 วินาที
- 🖱️ เพิ่มปุ่ม 🔄 Refresh แบบ manual
- ⏳ แสดง Loading state
- 📱 ใช้งานได้ทุกอุปกรณ์ (Desktop, Mobile, Tablet)
- 💬 แสดงข้อความ text ของแต่ละวิดีโอ
- 🎤 แสดงภาษาและเสียงที่ใช้

**ผลลัพธ์:**
- ✅ ไม่ต้องพึ่ง localStorage อีกต่อไป
- ✅ เห็นวิดีโอทั้งหมดที่มีใน Server
- ✅ ข้อมูล sync กันทุกเครื่อง
- ✅ UX ดีขึ้น มี feedback ชัดเจน

## 📝 Quick Commands

### Server Management

```bash
# เริ่ม server
cd ~/ai-robot-speaker-api && source .venv/bin/activate && ./start_server.sh

# Restart server
pkill -f "python main.py" && cd ~/ai-robot-speaker-api && nohup python main.py > server.log 2>&1 &

# ตรวจสอบ log
tail -f ~/ai-robot-speaker-api/server.log

# ตรวจสอบว่า server ทำงานหรือไม่
ps aux | grep "python main.py"
```

### API Testing

```bash
# Health check
curl http://10.147.19.244:4188/health

# ดูรายการงาน
curl http://10.147.19.244:4188/api/v1/jobs/list

# สร้างงานทดสอบ
curl -X POST http://10.147.19.244:4188/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"text":"ทดสอบระบบ","lang":"th","voice":"th-TH-PremwadeeNeural"}'
```

### Git Operations

```bash
# Pull ล่าสุด
git pull origin main

# Push changes
git add .
git commit -m "Update: your message"
git push origin main

# ตรวจสอบสถานะ
git status
git log -3
```

### Network Testing

```bash
# ทดสอบ ZeroTier
sudo zerotier-cli status
sudo zerotier-cli listnetworks

# ทดสอบ connectivity
ping 10.147.19.244
```

## 🔧 Troubleshooting

### Port Already in Use

```bash
# หา process ที่ใช้ port 4188
sudo lsof -i :4188

# Kill process
sudo kill -9 <PID>

# หรือ kill ทุก python process
pkill -f "python main.py"
```

### Server ไม่ทำงาน

```bash
# ตรวจสอบ log
tail -50 ~/ai-robot-speaker-api/server.log

# ตรวจสอบ process
ps aux | grep python

# Restart server
cd ~/ai-robot-speaker-api
source .venv/bin/activate
./start_server.sh
```

### ติดต่อไม่ได้ผ่าน ZeroTier

```bash
# ตรวจสอบ ZeroTier status
sudo zerotier-cli status

# ตรวจสอบ network
sudo zerotier-cli listnetworks

# Restart ZeroTier
sudo service zerotier-one restart

# ตรวจสอบ IP
ifconfig | grep 10.147
```

### Git Push ไม่ผ่าน

```bash
# Pull ก่อน push
git pull origin main

# ถ้ามี conflict ให้แก้แล้ว
git add .
git commit -m "Merge conflicts"
git push origin main

# Force push (ระวัง!)
git push -f origin main
```

### Virtual Environment ไม่ทำงาน

```bash
# สร้างใหม่
cd ~/ai-robot-speaker-api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🎯 API Response Examples

### สร้างงานสำเร็จ

```json
{
  "job_id": "job_20251008_143022_a1b2c3",
  "status": "created",
  "message": "Job created successfully"
}
```

### ดูสถานะงาน

```json
{
  "job_id": "job_20251008_143022_a1b2c3",
  "status": "processing",
  "progress": 45,
  "current_step": "Generating video",
  "created_at": "2025-10-08T14:30:22Z",
  "updated_at": "2025-10-08T14:31:05Z"
}
```

### รายการงานทั้งหมด

```json
{
  "jobs": [
    {
      "job_id": "job_20251008_150000_xyz789",
      "text": "สวัสดีตอนเย็น ยินดีต้อนรับทุกคน",
      "lang": "th",
      "voice": "th-TH-PremwadeeNeural",
      "created_at": "2025-10-08T15:00:00Z",
      "video_file": "final_split_subbed.mp4"
    },
    {
      "job_id": "job_20251008_143022_a1b2c3",
      "text": "Hello everyone, welcome to our presentation",
      "lang": "en",
      "voice": "en-US-JennyNeural",
      "created_at": "2025-10-08T14:30:22Z",
      "video_file": "final_split_subbed.mp4"
    }
  ],
  "count": 2
}
```

## 📚 เอกสารเพิ่มเติม

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ZeroTier Documentation](https://docs.zerotier.com/)
- [Azure TTS Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/)

## 🔐 Security Notes

- Server ใช้ Static IP: `192.168.1.59`
- Remote access ผ่าน ZeroTier VPN
- ไม่มี authentication (ใช้สำหรับ internal only)
- ควรเพิ่ม API key หากต้องการ expose ออก internet

## 🚀 Performance Tips

- ใช้ `limit` parameter ใน `/api/v1/jobs/list` เพื่อลดข้อมูล
- Auto-refresh ตั้งไว้ 30 วินาที เพื่อไม่ให้ load server มากเกินไป
- วิดีโอจะถูกเก็บในโฟลเดอร์ `out/`
- ควร cleanup วิดีโอเก่าเป็นระยะ

## 👨‍💻 Author

**Autthapolsaiyat**

## 📄 License

MIT License

---

**Last Updated**: 8 ตุลาคม 2568  
**Version**: 1.0.0  
**Server**: Ubuntu Linux (192.168.1.59)  
**ZeroTier**: 10.147.19.244
