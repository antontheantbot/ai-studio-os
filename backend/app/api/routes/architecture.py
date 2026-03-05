from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()


@router.get("/")
async def list_locations(
    q: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "architecture_locations", q, limit=limit)
    result = await db.execute(__import__("sqlalchemy").text("SELECT * FROM architecture_locations ORDER BY created_at DESC LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.post("/scout")
async def trigger_scout():
    """Trigger the architecture scout agent."""
    from workers.celery_app import celery_app
    task = celery_app.send_task("tasks.scout_architecture")
    return {"task_id": task.id, "status": "queued"}


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for new architecture using Tavily."""
    from app.agents.web_ingestor import scan_architecture
    background_tasks.add_task(scan_architecture)
    return {"status": "scanning", "category": "architecture", "message": "Web scan started"}
