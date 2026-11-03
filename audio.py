import httpx

from config import STT_API_KEY, STT_API_URL, TTS_API_KEY, TTS_API_URL


async def transcribe_audio(base64_chunk):
    headers = {"Authorization": f"Bearer {STT_API_KEY}"}
    body = {"audio": base64_chunk, "encoding": "mulaw", "sample_rate": 8000}
    async with httpx.AsyncClient() as client:
        resp = await client.post(STT_API_URL, json=body, headers=headers)
    resp.raise_for_status()
    return resp.json().get("text", "")


async def generate_speech(text):
    headers = {"Authorization": f"Bearer {TTS_API_KEY}"}
    body = {"text": text, "encoding": "mulaw", "sample_rate": 8000}
    async with httpx.AsyncClient() as client:
        resp = await client.post(TTS_API_URL, json=body, headers=headers)
    resp.raise_for_status()
    return resp.json()["audio"]
