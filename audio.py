import audioop
import base64
import json
import logging

import httpx
import websockets

from config import ASR_URL, OPENAI_API_KEY, TTS_MODEL, TTS_SAMPLE_RATE, TTS_URL, TTS_VOICE

log = logging.getLogger("agent")
auth = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
http = httpx.AsyncClient(headers=auth, timeout=30)


async def open_asr():
    asr = await websockets.connect(ASR_URL, additional_headers=auth)
    await asr.send(json.dumps({
        "type": "session.update",
        "session": {"type": "transcription", "audio": {"input": {"format": {"type": "audio/pcm", "rate": 8000}}}},
    }))
    return asr


async def transcribe_audio(asr, base64_chunk):
    pcm = audioop.ulaw2lin(base64.b64decode(base64_chunk), 2)
    await asr.send(json.dumps({"type": "input_audio_buffer.append", "audio": base64.b64encode(pcm).decode()}))


async def read_transcripts(asr):
    async for raw in asr:
        event = json.loads(raw)
        if event["type"] == "error":
            log.error("asr error: %s", event)
        elif event["type"] == "conversation.item.input_audio_transcription.delta":
            yield "delta", event.get("transcript", "")
        elif event["type"] == "conversation.item.input_audio_transcription.completed":
            yield "final", event.get("transcript", "")


async def generate_speech(text):
    url = f"{TTS_URL}/{TTS_VOICE}/stream"
    body = {"text": text, "model_id": TTS_MODEL, "output_format": "pcm"}
    state = None
    leftover = b""
    async with http.stream("POST", url, json=body) as resp:
        resp.raise_for_status()
        async for chunk in resp.aiter_bytes():
            data = leftover + chunk
            usable = len(data) - len(data) % 2
            data, leftover = data[:usable], data[usable:]
            if not data:
                continue
            pcm, state = audioop.ratecv(data, 2, 1, TTS_SAMPLE_RATE, 8000, state)
            yield base64.b64encode(audioop.lin2ulaw(pcm, 2)).decode()
