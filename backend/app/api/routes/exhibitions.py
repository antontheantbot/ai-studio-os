from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()


@router.get("/")
async def list_exhibitions(
    q: str = Query(default=None),
    upcoming: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List exhibitions."""
    if q:
        return await vector_search(db, "exhibitions", q, limit)

    query = "SELECT e.*, i.name as institution_name FROM exhibitions e LEFT JOIN institutions i ON e.institution_id = i.id"
    params = {"limit": limit}

    if upcoming:
        query += " WHERE e.start_date >= CURRENT_DATE"

    query += " ORDER BY e.start_date DESC NULLS LAST LIMIT :limit"

    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]
