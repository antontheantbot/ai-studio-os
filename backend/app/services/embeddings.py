from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# In-process LRU cache — embeddings are deterministic so no TTL needed.
# Evicts the oldest entry when full (dict preserves insertion order, Python 3.7+).
_cache: dict[str, list[float]] = {}
_CACHE_MAX = 512


async def embed(text: str) -> list[float]:
    """Return an embedding vector for the given text, using the in-process cache."""
    key = text.replace("\n", " ")
    if key in _cache:
        return _cache[key]

    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=key,
    )
    vec = response.data[0].embedding

    if len(_cache) >= _CACHE_MAX:
        _cache.pop(next(iter(_cache)))  # evict oldest
    _cache[key] = vec
    return vec


async def embed_many(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts, skipping any that are already cached."""
    keys = [t.replace("\n", " ") for t in texts]

    # Split into cached hits and uncached misses
    uncached_keys = [k for k in keys if k not in _cache]

    if uncached_keys:
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=uncached_keys,
        )
        for key, item in zip(uncached_keys, response.data):
            if len(_cache) >= _CACHE_MAX:
                _cache.pop(next(iter(_cache)))
            _cache[key] = item.embedding

    return [_cache[k] for k in keys]
