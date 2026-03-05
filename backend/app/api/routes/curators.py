from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from pydantic import BaseModel

from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed

router = APIRouter()


class CuratorCreate(BaseModel):
    name: str
    bio: str | None = None
    institution: str | None = None
    role: str | None = None
    location: str | None = None
    country: str | None = None
    focus_areas: list[str] = []
    notable_shows: list[str] = []
    contact_email: str | None = None
    contact_url: str | None = None
    social_links: dict = {}
    notes: str | None = None


@router.get("/")
async def list_curators(
    q: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "curators", q, limit=limit)
    result = await db.execute(sa.text("SELECT * FROM curators ORDER BY name LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.get("/{curator_id}")
async def get_curator(curator_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(sa.text("SELECT * FROM curators WHERE id = :id"), {"id": curator_id})
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}


@router.post("/")
async def create_curator(c: CuratorCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{c.name} {c.institution or ''} {c.bio or ''} {' '.join(c.focus_areas)}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    import json
    result = await db.execute(
        sa.text("""
            INSERT INTO curators
                (name, bio, institution, role, location, country,
                 focus_areas, notable_shows, contact_email, contact_url, social_links, notes, embedding)
            VALUES
                (:name, :bio, :institution, :role, :location, :country,
                 :focus_areas, :notable_shows, :contact_email, :contact_url, CAST(:social_links AS jsonb), :notes, CAST(:embedding AS vector))
            RETURNING id, name, created_at
        """),
        {
            "name": c.name, "bio": c.bio, "institution": c.institution, "role": c.role,
            "location": c.location, "country": c.country, "focus_areas": c.focus_areas,
            "notable_shows": c.notable_shows, "contact_email": c.contact_email,
            "contact_url": c.contact_url, "social_links": json.dumps(c.social_links),
            "notes": c.notes, "embedding": embedding_str,
        },
    )
    await db.commit()
    return dict(result.first()._mapping)


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for new curators using Tavily."""
    from app.agents.web_ingestor import scan_curators
    background_tasks.add_task(scan_curators)
    return {"status": "scanning", "category": "curators", "message": "Web scan started"}
