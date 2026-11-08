# AI Calling Agent

A small voice agent you can phone. Twilio picks up the call, streams the audio to a FastAPI app, and the app does speech-to-text, runs an LLM, and speaks the reply back. Everything runs on DeepInfra, so there's one API key to manage.

I kept the code flat on purpose: four small files, no classes.

## How it works

```
phone -> Twilio -> /ws (FastAPI) -> DeepInfra ASR (websocket)
                                         |
phone <- Twilio <- /ws (FastAPI) <- DeepInfra TTS <- DeepInfra LLM
```

1. Twilio hits `POST /incoming-call` and gets TwiML that opens a media stream to `/ws`.
2. Every 20 ms audio frame from the caller is forwarded straight to DeepInfra's streaming ASR.
3. When ASR returns a final transcript, the text goes to the LLM.
4. The LLM reply is streamed and split by sentence. Each sentence is sent to TTS right away, so you hear the first sentence while the rest is still being written.
5. If the caller talks over the agent, the reply is cancelled and Twilio's audio buffer is cleared.

## Files

| File | What it does |
|---|---|
| `main.py` | FastAPI app: the TwiML endpoint and the `/ws` stream handler |
| `audio.py` | ASR websocket, TTS streaming, and the μ-law / PCM conversion |
| `llm.py` | Streams the LLM reply and yields it one sentence at a time |
| `config.py` | Reads settings from environment variables |

## Models (all on DeepInfra)

- ASR: `nvidia/Nemo3-ASR-Streaming`
- LLM: `google/gemma-4-26B-A4B-it`
- TTS: `hexgrad/Kokoro-82M`

I picked the LLM by timing a handful of them on the same prompt. Gemma was the quickest to first token, though only by a bit.

## Setup

You need Python 3.12 or newer (3.13 works too, it pulls in `audioop-lts`) and a DeepInfra API key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your key in `.env`:

```
OPENAI_API_KEY=your_deepinfra_key
```

The variable is called `OPENAI_API_KEY` because the LLM part uses the OpenAI client pointed at DeepInfra. The same key is used for ASR and TTS.

Run it:

```bash
python main.py
```

Or with Docker:

```bash
docker compose up --build
```

The app listens on port 8000.

## Connecting Twilio

Twilio needs a public HTTPS URL, so for local testing use a tunnel such as ngrok or cloudflared:

```bash
ngrok http 8000
```

Then point your Twilio number's voice webhook at `https://<your-tunnel>/incoming-call` (HTTP POST) and call the number.


## Configuration

Only `OPENAI_API_KEY` is required. The rest have defaults in `config.py`.

| Variable | Default |
|---|---|
| `OPENAI_API_KEY` | none |
| `OPENAI_API_BASE` | `https://api.deepinfra.com/v1/openai` |
| `LLM_MODEL` | `google/gemma-4-26B-A4B-it` |
| `ASR_MODEL` | `nvidia/Nemo3-ASR-Streaming` |
| `TTS_URL` | `https://api.deepinfra.com/v1/text-to-speech` |
| `TTS_MODEL` | `hexgrad/Kokoro-82M` |
| `TTS_VOICE` | `af_bella` |
| `TTS_SAMPLE_RATE` | `24000` |

## Latency

The app logs timings for every turn:

```
caller: hi can you hear me
llm first sentence: 310 ms
first audio sent: 520 ms after transcript
reply done: 1400 ms total
```

## Known limitations

- No Twilio request signature check, so don't leave it open on a public URL for long. Anyone who finds `/ws` could use up your DeepInfra credit.
- Conversation history is short (the last 10 messages) and lives in memory per call.