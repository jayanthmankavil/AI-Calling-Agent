import asyncio
import json

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect

from audio import generate_speech, open_asr, read_transcripts, transcribe_audio
from llm import get_llm_response

app = FastAPI()


@app.post("/incoming-call")
async def incoming_call(request: Request):
    host = request.headers["host"]
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://{host}/ws"/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


async def reply(websocket, call, text):
    async for sentence in get_llm_response(text, call["history"]):
        async for payload in generate_speech(sentence):
            await websocket.send_text(json.dumps({
                "event": "media",
                "streamSid": call["sid"],
                "media": {"payload": payload},
            }))


async def listen_asr(asr, websocket, call):
    async for kind, text in read_transcripts(asr):
        task = call["task"]
        if task and not task.done() and text.strip():
            task.cancel()
            await websocket.send_text(json.dumps({"event": "clear", "streamSid": call["sid"]}))
        if kind == "final" and text.strip():
            call["task"] = asyncio.create_task(reply(websocket, call, text))


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    call = {"sid": None, "history": [], "task": None}
    asr = await open_asr()
    listener = asyncio.create_task(listen_asr(asr, websocket, call))

    while True:
        try:
            message = json.loads(await websocket.receive_text())
        except WebSocketDisconnect:
            break

        event = message["event"]

        if event == "start":
            call["sid"] = message["start"]["streamSid"]
        elif event == "stop":
            break
        elif event == "media":
            await transcribe_audio(asr, message["media"]["payload"])

    listener.cancel()
    if call["task"]:
        call["task"].cancel()
    await asr.close()
