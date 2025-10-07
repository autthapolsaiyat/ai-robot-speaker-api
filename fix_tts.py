import re

with open('main.py', 'r') as f:
    content = f.read()

# Find and replace the synthesize_tts function
old_func = r'''def synthesize_tts\(text: str, lang: str, out_wav: Path, model: str = None, 
                   speaker: str = None, speed: float = 1\.0, pitch: float = 0\.0\):
    """Generate speech from text"""
    tts = get_tts_model\(\)
    tts\.tts_to_file\(
        text=text,
        file_path=str\(out_wav\),
        speaker=speaker,
        language=lang
    \)
    logger\.info\(f"TTS completed: \{out_wav\}"\)'''

new_func = '''def synthesize_tts(text: str, lang: str, out_wav: Path, model: str = None, 
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
    
    logger.info(f"TTS completed: {out_wav}")'''

content = re.sub(old_func, new_func, content, flags=re.MULTILINE)

with open('main.py', 'w') as f:
    f.write(content)

print("✓ Fixed synthesize_tts function")
