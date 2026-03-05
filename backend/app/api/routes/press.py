from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.search import vector_search, keyword_search

router = APIRouter()


@router.get("/")
async def list_press(
    q: str | None = Query(None),
    mode: str = Query("semantic", regex="^(semantic|keyword)$"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q and mode == "semantic":
        return await vector_search(db, "press_items", q, limit=limit)
    if q and mode == "keyword":
        return await keyword_search(db, "press_items", q, search_col="title || ' ' || content", limit=limit)
    result = await db.execute(__import__("sqlalchemy").text("SELECT * FROM press_items ORDER BY published_at DESC LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]
