import json

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect

from audio import generate_speech, transcribe_audio
from llm import get_llm_response

app = FastAPI()


@app.post("/incoming-call")
async def incoming_call(request: Request):
    host = request.headers["host"]
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://{host}/ws"/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    stream_sid = None

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
            text = await transcribe_audio(message["media"]["payload"])
            if not text:
                continue
            reply = await get_llm_response(text)
            speech = await generate_speech(reply)
            await websocket.send_text(json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": speech},
            }))
