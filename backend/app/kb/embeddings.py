import os
import aiohttp
import asyncio
from typing import List, Optional

OPENAI_EMBEDDINGS_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")

async def openai_embedding(text: str) -> Optional[List[float]]:
    if not OPENAI_API_KEY:
        return None
    try:
        # OpenAI expects no newlines-only whitespace issues
        input_text = text.replace("\n", " ")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_EMBEDDINGS_MODEL,
                    "input": input_text,
                },
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                vec = data.get("data", [{}])[0].get("embedding")
                if isinstance(vec, list):
                    return [float(x) for x in vec]
                return None
    except Exception:
        return None

def to_pgvector_literal(vec: List[float]) -> str:
    # pgvector textual format: [v1, v2, ...]
    return "[" + ", ".join(f"{x:.6f}" for x in vec) + "]"
