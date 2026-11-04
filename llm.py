from openai import AsyncOpenAI

from config import LLM_MODEL, OPENAI_API_BASE, OPENAI_API_KEY

client = AsyncOpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_API_KEY)

SYSTEM = {"role": "system", "content": "You are a phone assistant. Reply in one or two short spoken sentences."}


async def get_llm_response(text, history):
    history.append({"role": "user", "content": text})
    stream = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[SYSTEM] + history[-10:],
        max_tokens=120,
        stream=True,
    )
    pending = ""
    full = ""
    async for chunk in stream:
        if not chunk.choices:
            continue
        pending += chunk.choices[0].delta.content or ""
        while True:
            ends = [pending.find(c) for c in ".!?"]
            ends = [i for i in ends if i != -1]
            if not ends:
                break
            i = min(ends) + 1
            sentence, pending = pending[:i].strip(), pending[i:]
            full += sentence + " "
            yield sentence
    if pending.strip():
        full += pending.strip()
        yield pending.strip()
    history.append({"role": "assistant", "content": full.strip()})
