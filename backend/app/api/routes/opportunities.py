from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from pydantic import BaseModel

from app.db.session import get_db
from app.services.search import vector_search, keyword_search
from app.services.embeddings import embed

router = APIRouter()


class OpportunityCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    organizer: str | None = None
    location: str | None = None
    country: str | None = None
    deadline: str | None = None
    fee: str | None = None
    award: str | None = None
    url: str | None = None
    tags: list[str] = []


@router.get("/")
async def list_opportunities(
    q: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "opportunities", q, limit=limit)
    result = await db.execute(sa.text("SELECT * FROM opportunities ORDER BY created_at DESC LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.post("/")
async def create_opportunity(opp: OpportunityCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{opp.title} {opp.description or ''} {' '.join(opp.tags)}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO opportunities
                (title, description, category, organizer, location, country,
                 deadline, fee, award, url, tags, embedding)
            VALUES
                (:title, :description, :category, :organizer, :location, :country,
                 :deadline, :fee, :award, :url, :tags, CAST(:embedding AS vector))
            ON CONFLICT (url) DO NOTHING
            RETURNING id, title, created_at
        """),
        {
            "title": opp.title, "description": opp.description, "category": opp.category,
            "organizer": opp.organizer, "location": opp.location, "country": opp.country,
            "deadline": date.fromisoformat(opp.deadline) if opp.deadline else None, "fee": opp.fee, "award": opp.award,
            "url": opp.url, "tags": opp.tags, "embedding": embedding_str,
        },
    )
    await db.commit()
    row = result.first()
    return dict(row._mapping) if row else {"status": "already exists"}


@router.post("/scan")
async def trigger_scan():
    from workers.celery_app import celery_app
    task = celery_app.send_task("tasks.scan_opportunities")
    return {"task_id": task.id, "status": "queued"}
