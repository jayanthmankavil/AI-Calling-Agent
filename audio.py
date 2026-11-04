import audioop
import base64
import io
import wave

import httpx

from config import OPENAI_API_KEY, STT_API_URL, TTS_API_URL, TTS_SAMPLE_RATE

client = httpx.AsyncClient(headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}, timeout=30)


async def transcribe_audio(mulaw_bytes):
    pcm = audioop.ulaw2lin(mulaw_bytes, 2)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(pcm)
    resp = await client.post(STT_API_URL, files={"audio": ("audio.wav", buf.getvalue(), "audio/wav")})
    resp.raise_for_status()
    return resp.json().get("text", "").strip()


async def generate_speech(text):
    resp = await client.post(TTS_API_URL, json={"text": text, "output_format": "pcm"})
    resp.raise_for_status()
    audio = resp.json()["audio"]
    if audio.startswith("data:"):
        audio = audio.split(",", 1)[1]
    pcm = base64.b64decode(audio)
    pcm, _ = audioop.ratecv(pcm, 2, 1, TTS_SAMPLE_RATE, 8000, None)
    return base64.b64encode(audioop.lin2ulaw(pcm, 2)).decode()
