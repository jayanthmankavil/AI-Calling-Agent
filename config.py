import os

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepinfra.com/v1/openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-4-26B-A4B-it")

ASR_MODEL = os.getenv("ASR_MODEL", "nvidia/Nemo3-ASR-Streaming")
ASR_URL = f"wss://api.deepinfra.com/v1/realtime?model={ASR_MODEL}"

TTS_URL = os.getenv("TTS_URL", "https://api.deepinfra.com/v1/text-to-speech")
TTS_MODEL = os.getenv("TTS_MODEL", "hexgrad/Kokoro-82M")
TTS_VOICE = os.getenv("TTS_VOICE", "af_bella")
TTS_SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", "24000"))
