from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from pydantic import BaseModel

from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed

router = APIRouter()

_COLS = "id, name, bio, location, country, interests, known_works, institutions, contact_email, contact_url, social_links, notes, created_at, updated_at, price_range, museum_boards"


class CollectorCreate(BaseModel):
    name: str
    bio: str | None = None
    location: str | None = None
    country: str | None = None
    interests: list[str] = []
    known_works: list[str] = []
    institutions: list[str] = []
    contact_email: str | None = None
    contact_url: str | None = None
    social_links: dict = {}
    notes: str | None = None


@router.get("/")
async def list_collectors(
    q: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "collectors", q, limit=limit, return_cols=_COLS)
    result = await db.execute(sa.text(f"SELECT {_COLS} FROM collectors ORDER BY name LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.get("/{collector_id}")
async def get_collector(collector_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(sa.text(f"SELECT {_COLS} FROM collectors WHERE id = :id"), {"id": collector_id})
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}


@router.post("/")
async def create_collector(c: CollectorCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{c.name} {c.bio or ''} {' '.join(c.interests)}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    import json
    result = await db.execute(
        sa.text("""
            INSERT INTO collectors
                (name, bio, location, country, interests, known_works,
                 institutions, contact_email, contact_url, social_links, notes, embedding)
            VALUES
                (:name, :bio, :location, :country, :interests, :known_works,
                 :institutions, :contact_email, :contact_url, CAST(:social_links AS jsonb), :notes, CAST(:embedding AS vector))
            RETURNING id, name, created_at
        """),
        {
            "name": c.name, "bio": c.bio, "location": c.location, "country": c.country,
            "interests": c.interests, "known_works": c.known_works, "institutions": c.institutions,
            "contact_email": c.contact_email, "contact_url": c.contact_url,
            "social_links": json.dumps(c.social_links), "notes": c.notes,
            "embedding": embedding_str,
        },
    )
    await db.commit()
    return dict(result.first()._mapping)


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for new collectors using Tavily."""
    from app.agents.web_ingestor import scan_collectors
    background_tasks.add_task(scan_collectors)
    return {"status": "scanning", "category": "collectors", "message": "Web scan started"}
