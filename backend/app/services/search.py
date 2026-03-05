from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embeddings import embed


async def vector_search(
    db: AsyncSession,
    table: str,
    query: str,
    limit: int = 10,
    embedding_col: str = "embedding",
    return_cols: str = "*",
) -> list[dict]:
    """
    Generic pgvector cosine similarity search.
    Returns rows ordered by similarity to the query string.
    """
    query_embedding = await embed(query)
    embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

    sql = text(f"""
        SELECT {return_cols},
               1 - ({embedding_col} <=> CAST(:embedding AS vector)) AS similarity
        FROM {table}
        ORDER BY {embedding_col} <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    result = await db.execute(sql, {"embedding": embedding_str, "limit": limit})
    return [dict(row._mapping) for row in result]


async def keyword_search(
    db: AsyncSession,
    table: str,
    query: str,
    search_col: str,
    limit: int = 10,
    return_cols: str = "*",
) -> list[dict]:
    """Full-text keyword search using PostgreSQL tsvector."""
    sql = text(f"""
        SELECT {return_cols},
               ts_rank(to_tsvector('english', {search_col}), plainto_tsquery('english', :query)) AS rank
        FROM {table}
        WHERE to_tsvector('english', {search_col}) @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :limit
    """)

    result = await db.execute(sql, {"query": query, "limit": limit})
    return [dict(row._mapping) for row in result]
