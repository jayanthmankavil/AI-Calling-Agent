import asyncio
import json
import logging
import time

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect

from audio import generate_speech, open_asr, read_transcripts, transcribe_audio
from llm import get_llm_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("agent")
app = FastAPI()


@app.post("/incoming-call")
async def incoming_call(request: Request):
    host = request.headers["host"]
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://{host}/ws"/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


async def reply(websocket, call, text):
    start = time.perf_counter()
    first_sentence = None
    first_audio = None
    try:
        async for sentence in get_llm_response(text, call["history"]):
            if first_sentence is None:
                first_sentence = time.perf_counter() - start
                log.info("llm first sentence: %.0f ms", first_sentence * 1000)
            async for payload in generate_speech(sentence):
                if first_audio is None:
                    first_audio = time.perf_counter() - start
                    log.info("first audio sent: %.0f ms after transcript", first_audio * 1000)
                await websocket.send_text(json.dumps({
                    "event": "media",
                    "streamSid": call["sid"],
                    "media": {"payload": payload},
                }))
        log.info("reply done: %.0f ms total", (time.perf_counter() - start) * 1000)
    except asyncio.CancelledError:
        log.info("reply cancelled (caller spoke)")
        raise
    except Exception:
        log.exception("reply failed")


async def listen_asr(asr, websocket, call):
    async for kind, text in read_transcripts(asr):
        task = call["task"]
        if task and not task.done() and text.strip():
            task.cancel()
            await websocket.send_text(json.dumps({"event": "clear", "streamSid": call["sid"]}))
        if kind == "final" and text.strip():
            log.info("caller: %s", text)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
