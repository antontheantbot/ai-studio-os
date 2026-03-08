import json
import re
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from pydantic import BaseModel

from app.db.session import get_db
from app.services.llm import generate
from app.services.search import vector_search
from app.services.embeddings import embed

router = APIRouter()
logger = logging.getLogger(__name__)

PARSE_PROMPT = """Parse the following pasted text into a list of art collector profiles.
The text may be formatted in any way — a list of names, bios, LinkedIn profiles, press mentions, or any mix.

Return a JSON array where each object has:
- name (string, full name — required)
- bio (string, 2-3 sentences or null)
- location (string, city or null)
- country (string or null)
- interests (array of strings, e.g. "digital art", "photography", "sculpture")
- known_works (array of strings, artists or works they collect)
- institutions (array of strings, museum boards or foundations they are associated with)
- contact_email (string or null)
- contact_url (string, full URL or null)
- social_links (object with any of: twitter, instagram, linkedin, website — full URLs)
- notes (string, any useful context or null)

If you cannot identify a person's name, skip that entry. Return [] if nothing parseable.

Text to parse:
{text}"""


class PasteBody(BaseModel):
    text: str


@router.post("/add")
async def add_from_text(body: PasteBody, db: AsyncSession = Depends(get_db)):
    """Parse pasted text and add any collector profiles found to the database."""
    if not body.text.strip():
        return {"added": 0, "skipped": 0, "message": "No text provided"}

    raw = await generate(PARSE_PROMPT.format(text=body.text[:8000]))
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.error(f"[Collectors/add] No JSON array found: {raw[:300]}")
        return {"added": 0, "skipped": 0, "message": "Could not parse any profiles from the text"}

    try:
        items = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        logger.error(f"[Collectors/add] JSON parse error: {e}")
        return {"added": 0, "skipped": 0, "message": f"JSON parse error: {e}"}

    added, skipped = 0, 0
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            skipped += 1
            continue
        exists = await db.execute(sa.text("SELECT id FROM collectors WHERE name = :name"), {"name": name})
        if exists.first():
            skipped += 1
            continue
        try:
            embed_text = f"{name} {item.get('bio') or ''} {' '.join(item.get('interests') or [])}"
            embedding = await embed(embed_text)
            embedding_str = f"[{','.join(str(x) for x in embedding)}]"
            await db.execute(
                sa.text("""
                    INSERT INTO collectors
                        (name, bio, location, country, interests, known_works,
                         institutions, contact_email, contact_url, social_links, notes, embedding)
                    VALUES
                        (:name, :bio, :location, :country, :interests, :known_works,
                         :institutions, :contact_email, :contact_url, CAST(:social_links AS jsonb),
                         :notes, CAST(:embedding AS vector))
                    ON CONFLICT (name) DO NOTHING
                """),
                {
                    "name": name,
                    "bio": item.get("bio"),
                    "location": item.get("location"),
                    "country": item.get("country"),
                    "interests": item.get("interests") or [],
                    "known_works": item.get("known_works") or [],
                    "institutions": item.get("institutions") or [],
                    "contact_email": item.get("contact_email"),
                    "contact_url": item.get("contact_url"),
                    "social_links": json.dumps(item.get("social_links") or {}),
                    "notes": item.get("notes"),
                    "embedding": embedding_str,
                },
            )
            added += 1
        except Exception as e:
            logger.error(f"[Collectors/add] Insert failed for {name}: {e}")
            skipped += 1

    await db.commit()
    return {"added": added, "skipped": skipped, "message": f"Added {added} collector(s), skipped {skipped} duplicate(s)"}

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
    limit: int = Query(1000, le=5000),
    db: AsyncSession = Depends(get_db),
):
    if q:
        result = await db.execute(sa.text(f"""
            SELECT {_COLS} FROM collectors
            WHERE name ILIKE :q OR location ILIKE :q OR country ILIKE :q
               OR bio ILIKE :q OR notes ILIKE :q
            ORDER BY name LIMIT :limit
        """), {"q": f"%{q}%", "limit": limit})
        return [dict(r._mapping) for r in result]
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
