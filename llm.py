from openai import AsyncOpenAI

from config import LLM_MODEL, OPENAI_API_BASE, OPENAI_API_KEY

client = AsyncOpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_API_KEY)


async def get_llm_response(text):
    resp = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a phone assistant. Reply in one or two short spoken sentences."},
            {"role": "user", "content": text},
        ],
    )
    return resp.choices[0].message.content
