import json
import re
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.llm import generate
from app.services.embeddings import embed
from app.services.search import vector_search

router = APIRouter()
logger = logging.getLogger(__name__)

_COLS = "id, name, type, contact_name, contact_role, email, phone, website, city, country, focus_areas, tags, notes, source, social_links, created_at"

PARSE_PROMPT = """Parse the following pasted text into a list of corporate/organisational contacts relevant to an art world CRM.
This includes: brands, PR agencies, art foundations, tech companies, luxury brands, galleries (as organisations), corporate sponsors.

Return a JSON array where each object has:
- name (string, organisation name — required)
- type (string: one of brand, agency, foundation, tech, gallery, luxury, sponsor, other — or null)
- contact_name (string, primary contact person at the org or null)
- contact_role (string, their title/role or null)
- email (string or null)
- phone (string or null)
- website (string, full URL or null)
- city (string or null)
- country (string or null)
- focus_areas (array of strings, e.g. "digital art", "new media", "photography")
- notes (string, any useful context or null)
- social_links (object with any of: twitter, instagram, linkedin, website — full URLs)

If you cannot identify an organisation name, skip that entry. Return [] if nothing parseable.

Text to parse:
{text}"""


class PasteBody(BaseModel):
    text: str


@router.get("/")
async def list_corporations(
    q: str | None = Query(None),
    limit: int = Query(5000, le=5000),
    db: AsyncSession = Depends(get_db),
):
    if q:
        result = await db.execute(
            sa.text(f"""
                SELECT {_COLS} FROM corporations
                WHERE name ILIKE :q OR type ILIKE :q OR contact_name ILIKE :q
                   OR city ILIKE :q OR country ILIKE :q OR notes ILIKE :q
                ORDER BY name LIMIT :limit
            """), {"q": f"%{q}%", "limit": limit}
        )
        return [dict(r._mapping) for r in result]
    result = await db.execute(
        sa.text(f"SELECT {_COLS} FROM corporations ORDER BY name LIMIT :limit"), {"limit": limit}
    )
    return [dict(r._mapping) for r in result]


@router.post("/add")
async def add_from_text(body: PasteBody, db: AsyncSession = Depends(get_db)):
    """Parse pasted text and add any corporation/organisation profiles found."""
    if not body.text.strip():
        return {"added": 0, "skipped": 0, "message": "No text provided"}

    raw = await generate(PARSE_PROMPT.format(text=body.text[:8000]))
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.error(f"[Corporations/add] No JSON array found: {raw[:300]}")
        return {"added": 0, "skipped": 0, "message": "Could not parse any profiles from the text"}

    try:
        items = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        logger.error(f"[Corporations/add] JSON parse error: {e}")
        return {"added": 0, "skipped": 0, "message": f"JSON parse error: {e}"}

    added, skipped = 0, 0
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            skipped += 1
            continue
        exists = await db.execute(sa.text("SELECT id FROM corporations WHERE name = :name"), {"name": name})
        if exists.first():
            skipped += 1
            continue
        try:
            embed_text = f"{name} {item.get('type') or ''} {item.get('contact_name') or ''} {' '.join(item.get('focus_areas') or [])}"
            embedding = await embed(embed_text)
            embedding_str = f"[{','.join(str(x) for x in embedding)}]"
            await db.execute(
                sa.text("""
                    INSERT INTO corporations
                        (name, type, contact_name, contact_role, email, phone, website,
                         city, country, focus_areas, tags, notes, social_links, embedding)
                    VALUES
                        (:name, :type, :contact_name, :contact_role, :email, :phone, :website,
                         :city, :country, :focus_areas, :tags, :notes, CAST(:social_links AS jsonb),
                         CAST(:embedding AS vector))
                    ON CONFLICT (name) DO NOTHING
                """),
                {
                    "name": name,
                    "type": item.get("type"),
                    "contact_name": item.get("contact_name"),
                    "contact_role": item.get("contact_role"),
                    "email": item.get("email"),
                    "phone": item.get("phone"),
                    "website": item.get("website"),
                    "city": item.get("city"),
                    "country": item.get("country"),
                    "focus_areas": item.get("focus_areas") or [],
                    "tags": item.get("tags") or [],
                    "notes": item.get("notes"),
                    "social_links": json.dumps(item.get("social_links") or {}),
                    "embedding": embedding_str,
                },
            )
            added += 1
        except Exception as e:
            logger.error(f"[Corporations/add] Insert failed for {name}: {e}")
            skipped += 1

    await db.commit()
    return {"added": added, "skipped": skipped, "message": f"Added {added} corporation(s), skipped {skipped} duplicate(s)"}


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for new corporate art contacts using Tavily."""
    from app.agents.web_ingestor import scan_corporations
    background_tasks.add_task(scan_corporations)
    return {"status": "scanning", "category": "corporations", "message": "Web scan started"}
