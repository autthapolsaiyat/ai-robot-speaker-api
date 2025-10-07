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
