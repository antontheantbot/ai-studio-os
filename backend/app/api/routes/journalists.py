import json
import re
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.llm import generate

router = APIRouter()
logger = logging.getLogger(__name__)

PARSE_PROMPT = """Parse the following pasted text into a list of journalist profiles.
The text may be formatted in any way — a list of names, copy-pasted bios, LinkedIn profiles, email signatures, or any mix.

Return a JSON array where each object has:
- name (string, full name — required)
- bio (string, 2-3 sentences or null)
- publications (array of strings, publications/outlets mentioned)
- beats (array of strings, topics they cover e.g. "contemporary art", "architecture", "photography")
- email (string, email address if present or null)
- social_links (object with any of: twitter, instagram, linkedin, website — use full URLs)
- location (string, city or null)
- country (string or null)
- notes (string, any useful context or null)

If you cannot identify a person's name, skip that entry. Return [] if nothing parseable.

Text to parse:
{text}"""


@router.get("/")
async def list_journalists(
    q: str | None = Query(None),
    limit: int = Query(500, le=10000),
    db: AsyncSession = Depends(get_db),
):
    if q:
        pattern = f"%{q}%"
        result = await db.execute(
            sa.text("""
                SELECT * FROM journalists
                WHERE name ILIKE :q
                   OR bio ILIKE :q
                   OR email ILIKE :q
                   OR publications::text ILIKE :q
                   OR beats::text ILIKE :q
                   OR location ILIKE :q
                ORDER BY name LIMIT :limit
            """),
            {"q": pattern, "limit": limit},
        )
    else:
        result = await db.execute(
            sa.text("SELECT * FROM journalists ORDER BY name LIMIT :limit"), {"limit": limit}
        )
    return [dict(r._mapping) for r in result]


class PasteBody(BaseModel):
    text: str


@router.post("/add")
async def add_from_text(body: PasteBody, db: AsyncSession = Depends(get_db)):
    """Parse pasted text and add any journalist profiles found to the database."""
    if not body.text.strip():
        return {"added": 0, "skipped": 0, "message": "No text provided"}

    raw = await generate(PARSE_PROMPT.format(text=body.text[:8000]))

    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    # Find the JSON array — grab from first [ to last ]
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.error(f"[Journalists/add] No JSON array found in LLM response: {raw[:300]}")
        return {"added": 0, "skipped": 0, "message": "Could not parse any profiles from the text"}

    try:
        items = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        logger.error(f"[Journalists/add] JSON parse error: {e} — raw: {raw[start:start+300]}")
        return {"added": 0, "skipped": 0, "message": f"JSON parse error: {e}"}

    added, skipped = 0, 0
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            skipped += 1
            continue
        exists = await db.execute(
            sa.text("SELECT id FROM journalists WHERE name = :name"), {"name": name}
        )
        if exists.first():
            skipped += 1
            continue
        try:
            await db.execute(
                sa.text("""
                    INSERT INTO journalists
                        (id, name, bio, publications, beats, email, social_links, location, country, notes)
                    VALUES
                        (gen_random_uuid(), :name, :bio, CAST(:publications AS jsonb), CAST(:beats AS jsonb),
                         :email, CAST(:social_links AS jsonb), :location, :country, :notes)
                    ON CONFLICT (name) DO NOTHING
                """),
                {
                    "name": name,
                    "bio": item.get("bio"),
                    "publications": json.dumps(item.get("publications") or []),
                    "beats": json.dumps(item.get("beats") or []),
                    "email": item.get("email"),
                    "social_links": json.dumps(item.get("social_links") or {}),
                    "location": item.get("location"),
                    "country": item.get("country"),
                    "notes": item.get("notes"),
                },
            )
            added += 1
        except Exception as e:
            logger.error(f"[Journalists/add] Insert failed for {name}: {e}")
            skipped += 1

    await db.commit()
    return {"added": added, "skipped": skipped, "message": f"Added {added} journalist(s), skipped {skipped} duplicate(s)"}


@router.post("/scan")
async def scan():
    """Scan the web for new journalists, then search for email addresses on any newly added ones."""
    from app.agents.web_ingestor import scan_journalists, enrich_recent_journalists
    added = await scan_journalists()
    emails_found = await enrich_recent_journalists(minutes=10, batch_size=added or 10)
    return {"status": "done", "added": added, "emails_found": emails_found}


@router.post("/enrich")
async def enrich(background_tasks: BackgroundTasks):
    """Search for email/contact info for journalists missing it (up to 20 per run)."""
    from app.agents.web_ingestor import enrich_journalists
    background_tasks.add_task(enrich_journalists)
    return {"status": "enriching", "message": "Enriching journalist contacts — check back in ~3 minutes"}
