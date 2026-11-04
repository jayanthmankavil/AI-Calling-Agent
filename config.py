import os

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepinfra.com/v1/openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")

STT_API_URL = os.getenv("STT_API_URL", "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3-turbo")
TTS_API_URL = os.getenv("TTS_API_URL", "https://api.deepinfra.com/v1/inference/hexgrad/Kokoro-82M")
TTS_SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", "24000"))

SPEECH_RMS = int(os.getenv("SPEECH_RMS", "500"))
END_SILENCE_FRAMES = int(os.getenv("END_SILENCE_FRAMES", "15"))
