from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, Query
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
    upcoming_only: bool = Query(True),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "opportunities", q, limit=limit)
    query = "SELECT * FROM opportunities"
    params = {"limit": limit}
    if upcoming_only:
        query += " WHERE deadline IS NULL OR deadline >= CURRENT_DATE"
    query += " ORDER BY deadline ASC NULLS LAST LIMIT :limit"
    result = await db.execute(sa.text(query), params)
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


async def _run_all_scanners():
    import logging
    logger = logging.getLogger(__name__)
    from app.agents.opportunity_scanner import scan_with_scoring
    from app.agents.tavily_scanner import run as tavily_run
    try:
        url_count = await scan_with_scoring()
        logger.info(f"[Scan] URL scanner done: {url_count} saved")
    except Exception as e:
        logger.error(f"[Scan] URL scanner failed: {e}")
    try:
        tavily_count = await tavily_run()
        logger.info(f"[Scan] Tavily scanner done: {tavily_count} saved")
    except Exception as e:
        logger.error(f"[Scan] Tavily scanner failed: {e}")


@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan — scrapes known sources and searches the open web."""
    background_tasks.add_task(_run_all_scanners)
    return {"status": "scanning", "message": "Scanning known sources + searching the web — check back in ~3 minutes"}
