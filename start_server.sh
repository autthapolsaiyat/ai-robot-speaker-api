#!/bin/bash
export HF_HOME=models/hf_cache
export TRANSFORMERS_CACHE=models/hf_cache
export TTS_HOME=models/tts_cache
mkdir -p models/hf_cache
source .venv/bin/activate
python main.py
