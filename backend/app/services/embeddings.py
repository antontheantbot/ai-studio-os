from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def embed(text: str) -> list[float]:
    """Return an embedding vector for the given text."""
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text.replace("\n", " "),
    )
    return response.data[0].embedding


async def embed_many(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts."""
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=[t.replace("\n", " ") for t in texts],
    )
    return [item.embedding for item in response.data]
