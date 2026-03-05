from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()


@router.get("/")
async def list_artworks(
    q: str = Query(default=None),
    artist_id: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List artworks."""
    if q:
        return await vector_search(db, "artworks", q, limit)

    query = "SELECT aw.*, a.name as artist_name FROM artworks aw LEFT JOIN artists a ON aw.artist_id = a.id"
    params = {"limit": limit}

    if artist_id:
        query += " WHERE aw.artist_id = :artist_id"
        params["artist_id"] = artist_id

    query += " ORDER BY aw.year DESC NULLS LAST LIMIT :limit"

    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]
