#!/bin/bash
set -e

echo "Downloading Wav2Lip checkpoint..."
mkdir -p models
cd models

# ดาวน์โหลด Wav2Lip GAN checkpoint (~150MB)
if [ ! -f "wav2lip_gan.pth" ]; then
    wget -c https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth
    echo "✓ Wav2Lip model downloaded"
else
    echo "✓ Wav2Lip model already exists"
fi

cd ..

echo ""
echo "Model download complete!"
echo ""
echo "Note: SDXL models for face generation need to be downloaded separately:"
echo "  1. Install git-lfs: sudo apt-get install git-lfs"
echo "  2. Clone SDXL: cd /models && git lfs clone https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
