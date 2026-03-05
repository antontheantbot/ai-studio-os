import json
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()


@router.get("/")
async def list_journalists(
    q: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "journalists", q, limit=limit)
    result = await db.execute(
        sa.text("SELECT * FROM journalists ORDER BY name LIMIT :limit"), {"limit": limit}
    )
    return [dict(r._mapping) for r in result]


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for journalists covering art, culture and architecture."""
    from app.agents.web_ingestor import scan_journalists
    background_tasks.add_task(scan_journalists)
    return {"status": "scanning", "message": "Scanning for journalists — check back in ~2 minutes"}
