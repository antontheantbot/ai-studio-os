from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.search import vector_search, keyword_search

router = APIRouter()


@router.get("/")
async def list_opportunities(
    q: str | None = Query(None, description="Semantic search query"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "opportunities", q, limit=limit)
    result = await db.execute(__import__("sqlalchemy").text("SELECT * FROM opportunities ORDER BY created_at DESC LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.post("/scan")
async def trigger_scan(db: AsyncSession = Depends(get_db)):
    """Trigger the opportunity scanner agent."""
    from workers.celery_app import celery_app
    task = celery_app.send_task("tasks.scan_opportunities")
    return {"task_id": task.id, "status": "queued"}
