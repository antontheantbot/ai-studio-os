import json
import re
import logging
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.services.llm import generate
from app.services.search import vector_search

router = APIRouter()
logger = logging.getLogger(__name__)

PARSE_PROMPT = """Parse the following pasted text into a list of institution profiles.
The text may be formatted in any way — a list of names, copy-pasted descriptions, website copy, or any mix.

Return a JSON array where each object has:
- name (string, institution name — required)
- city (string or null)
- country (string or null)
- type (string: one of museum, gallery, kunsthalle, biennial, foundation, residency, university, festival — or null)
- website (string, full URL or null)
- focus_areas (array of strings, e.g. "digital art", "new media", "photography")
- annual_budget (string or null, e.g. "€2M")
- digital_art_program (boolean, true if they have a digital/new media program)
- notes (string, any useful context or null)

If you cannot identify an institution name, skip that entry. Return [] if nothing parseable.

Text to parse:
{text}"""


class PasteBody(BaseModel):
    text: str


@router.post("/add")
async def add_from_text(body: PasteBody, db: AsyncSession = Depends(get_db)):
    """Parse pasted text and add any institution profiles found to the database."""
    if not body.text.strip():
        return {"added": 0, "skipped": 0, "message": "No text provided"}

    raw = await generate(PARSE_PROMPT.format(text=body.text[:8000]))
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.error(f"[Institutions/add] No JSON array found: {raw[:300]}")
        return {"added": 0, "skipped": 0, "message": "Could not parse any profiles from the text"}

    try:
        items = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        logger.error(f"[Institutions/add] JSON parse error: {e}")
        return {"added": 0, "skipped": 0, "message": f"JSON parse error: {e}"}

    added, skipped = 0, 0
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            skipped += 1
            continue
        exists = await db.execute(text("SELECT id FROM institutions WHERE name = :name"), {"name": name})
        if exists.first():
            skipped += 1
            continue
        try:
            await db.execute(
                text("""
                    INSERT INTO institutions
                        (id, name, city, country, type, website, focus_areas,
                         annual_budget, digital_art_program, notes)
                    VALUES
                        (gen_random_uuid(), :name, :city, :country, :type, :website,
                         CAST(:focus_areas AS jsonb), :annual_budget, :digital_art_program, :notes)
                    ON CONFLICT (name) DO NOTHING
                """),
                {
                    "name": name,
                    "city": item.get("city"),
                    "country": item.get("country"),
                    "type": item.get("type"),
                    "website": item.get("website"),
                    "focus_areas": json.dumps(item.get("focus_areas") or []),
                    "annual_budget": item.get("annual_budget"),
                    "digital_art_program": bool(item.get("digital_art_program", False)),
                    "notes": item.get("notes"),
                },
            )
            added += 1
        except Exception as e:
            logger.error(f"[Institutions/add] Insert failed for {name}: {e}")
            skipped += 1

    await db.commit()
    return {"added": added, "skipped": skipped, "message": f"Added {added} institution(s), skipped {skipped} duplicate(s)"}

_COLS = "id, name, city, country, type, website, focus_areas, annual_budget, digital_art_program, notes, created_at, updated_at"


@router.get("/")
async def list_institutions(
    q: str = Query(default=None),
    type: str = Query(default=None),
    digital_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List institutions with optional filters."""
    if q:
        return await vector_search(db, "institutions", q, limit, return_cols=_COLS)

    query = f"SELECT {_COLS} FROM institutions WHERE 1=1"
    params = {"limit": limit}

    if type:
        query += " AND type = :type"
        params["type"] = type

    if digital_only:
        query += " AND digital_art_program = TRUE"

    query += " ORDER BY created_at DESC LIMIT :limit"

    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]


@router.get("/digital-programs")
async def get_digital_art_institutions(
    region: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get institutions with active digital art programs."""
    query = """
        SELECT name, city, country, type, focus_areas, website
        FROM institutions
        WHERE digital_art_program = TRUE
    """
    params = {}

    if region:
        query += " AND (country ILIKE :region OR city ILIKE :region)"
        params["region"] = f"%{region}%"

    query += " ORDER BY name"

    result = await db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]
