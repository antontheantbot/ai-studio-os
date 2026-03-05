from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()


@router.get("/")
async def list_curators(
    q: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "curators", q, limit=limit)
    result = await db.execute(__import__("sqlalchemy").text("SELECT * FROM curators ORDER BY name LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.get("/{curator_id}")
async def get_curator(curator_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        __import__("sqlalchemy").text("SELECT * FROM curators WHERE id = :id"),
        {"id": curator_id},
    )
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}
