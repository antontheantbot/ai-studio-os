from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()

_COLS = "id, name, city, country, type, website, focus_areas, annual_budget, digital_art_program, notes, created_at, updated_at"


@router.get("/")
async def list_institutions(
    q: str = Query(default=None),
    type: str = Query(default=None),
    digital_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List institutions with optional filters."""
    if q:
        return await vector_search(db, "institutions", q, limit, return_cols=_COLS)

    query = f"SELECT {_COLS} FROM institutions WHERE 1=1"
    params = {"limit": limit}

    if type:
        query += " AND type = :type"
        params["type"] = type

    if digital_only:
        query += " AND digital_art_program = TRUE"

    query += " ORDER BY created_at DESC LIMIT :limit"

    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]


@router.get("/digital-programs")
async def get_digital_art_institutions(
    region: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get institutions with active digital art programs."""
    query = """
        SELECT name, city, country, type, focus_areas, website
        FROM institutions
        WHERE digital_art_program = TRUE
    """
    params = {}

    if region:
        query += " AND (country ILIKE :region OR city ILIKE :region)"
        params["region"] = f"%{region}%"

    query += " ORDER BY name"

    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]
