import asyncio
import audioop
import base64
import json

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect

from audio import generate_speech, transcribe_audio
from config import END_SILENCE_FRAMES, SPEECH_RMS
from llm import get_llm_response

app = FastAPI()


@app.post("/incoming-call")
async def incoming_call(request: Request):
    host = request.headers["host"]
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://{host}/ws"/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


async def reply(websocket, stream_sid, text, history):
    async for sentence in get_llm_response(text, history):
        speech = await generate_speech(sentence)
        await websocket.send_text(json.dumps({
            "event": "media",
            "streamSid": stream_sid,
            "media": {"payload": speech},
        }))


async def handle_utterance(websocket, stream_sid, mulaw_bytes, history):
    text = await transcribe_audio(mulaw_bytes)
    if text:
        await reply(websocket, stream_sid, text, history)


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    stream_sid = None
    history = []
    frames = []
    speaking = False
    silence = 0
    task = None

    while True:
        try:
            message = json.loads(await websocket.receive_text())
        except WebSocketDisconnect:
            break

        event = message["event"]

        if event == "start":
            stream_sid = message["start"]["streamSid"]
        elif event == "stop":
            break
        elif event == "media":
            if task and not task.done():
                continue
            frame = base64.b64decode(message["media"]["payload"])
            loud = audioop.rms(audioop.ulaw2lin(frame, 2), 2) > SPEECH_RMS
            frames.append(frame)
            if loud:
                speaking = True
                silence = 0
            elif speaking:
                silence += 1
            else:
                frames = frames[-5:]
            if speaking and silence >= END_SILENCE_FRAMES:
                task = asyncio.create_task(handle_utterance(websocket, stream_sid, b"".join(frames), history))
                frames = []
                speaking = False
                silence = 0
