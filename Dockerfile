# Multi-stage build for AI Robot Speaker API
# Support both CPU and GPU deployment

# Stage 1: Base image with system dependencies
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Application
FROM base AS app

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Clone Wav2Lip
RUN git clone https://github.com/Rudrabha/Wav2Lip.git

# Copy application code
COPY main.py .
COPY .env.example .env
COPY voice_config.json .
COPY face_presets.json .

# Create necessary directories
RUN mkdir -p models assets out logs

# Download Wav2Lip checkpoint (you can also mount this as a volume)
RUN cd models && \
    wget -q https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth

# Expose port
EXPOSE 4187

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4187/health || exit 1

# Run as non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Start command
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4187"]
