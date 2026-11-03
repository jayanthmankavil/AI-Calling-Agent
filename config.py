import os

STT_API_URL = os.getenv("STT_API_URL", "https://api.example-stt.com/v1/transcribe")
STT_API_KEY = os.getenv("STT_API_KEY", "")

TTS_API_URL = os.getenv("TTS_API_URL", "https://api.example-tts.com/v1/speech")
TTS_API_KEY = os.getenv("TTS_API_KEY", "")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepinfra.com/v1/openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
