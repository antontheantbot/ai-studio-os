"""
Unified Contacts API — single contacts table with category field.
"""
import json
import re
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.services.llm import generate
from app.services.embeddings import embed

router = APIRouter()
logger = logging.getLogger(__name__)

PARSE_PROMPT = """You are extracting contact information from pasted text for an art world CRM.

Your job is to find EVERY person or organisation mentioned and return them as structured JSON.

CRITICAL RULES:
1. Extract EVERY name you can find — do not skip anyone
2. Never return [] unless the text is literally empty or gibberish with no names at all
3. If you cannot determine the category, still include the contact with uncertain=true
4. A name alone is enough — you don't need email/role/org to include someone
5. Organisations (galleries, museums, companies) count as contacts too

Return a JSON array where each object has:
- category: "curator" | "journalist" | "institution" | "collector" | "corporation" | "unknown"
- uncertain: true if you are not confident about the category
- name: string (REQUIRED)
- role: string or null
- organization: string or null
- email: string or null
- phone: string or null
- website: string or null
- location: string or null (city)
- country: string or null
- bio: string or null
- social_links: object (twitter/instagram/linkedin/website)
- tags: string[]
- notes: string or null

Category guide:
- curator: works at museum/gallery, curates shows
- journalist: writer/critic/editor for art press
- institution: museum, gallery, foundation, biennial, kunsthalle
- collector: private art collector or patron
- corporation: company, brand, PR agency, sponsor, luxury brand
- unknown: not enough info — still include them

Text to parse:
{text}"""


class ParseBody(BaseModel):
    text: str


class ParsedContact(BaseModel):
    category: str
    uncertain: bool = False
    name: str
    role: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    location: str | None = None
    country: str | None = None
    bio: str | None = None
    social_links: dict = {}
    tags: list[str] = []
    notes: str | None = None


class ConfirmBody(BaseModel):
    contacts: list[ParsedContact]


VALID_CATEGORIES = ("curator", "journalist", "institution", "collector", "corporation", "unknown")


@router.get("/")
async def list_contacts(
    q: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(5000, le=5000),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    params: dict = {"limit": limit}

    if q:
        conditions.append(
            "(name ILIKE :q OR organization ILIKE :q OR email ILIKE :q OR role ILIKE :q OR location ILIKE :q OR bio ILIKE :q OR tags::text ILIKE :q)"
        )
        params["q"] = f"%{q}%"

    if category and category in VALID_CATEGORIES:
        conditions.append("category = :category")
        params["category"] = category

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    result = await db.execute(
        text(f"SELECT * FROM contacts {where} ORDER BY name LIMIT :limit"),
        params,
    )
    return [dict(r._mapping) for r in result]


@router.post("/parse")
async def parse_contacts(body: ParseBody):
    """Parse pasted text and return structured contact previews — does NOT save."""
    if not body.text.strip():
        return {"contacts": []}

    raw = await generate(PARSE_PROMPT.format(text=body.text[:10000]), max_tokens=8192)
    logger.info(f"[Contacts/parse] Raw LLM response (first 500 chars): {raw[:500]}")
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return {"contacts": [], "error": "Could not extract contacts — try rephrasing or adding more detail"}

    try:
        items = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        logger.error(f"[Contacts/parse] JSON decode error: {e}")
        return {"contacts": [], "error": "Parsing failed — try again or simplify the text"}

    contacts = []
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        cat = (item.get("category") or "").lower()
        uncertain = bool(item.get("uncertain")) or cat not in VALID_CATEGORIES
        if cat not in VALID_CATEGORIES:
            cat = "unknown"
        contacts.append({
            "category": cat,
            "uncertain": uncertain,
            "name": name,
            "role": item.get("role"),
            "organization": item.get("organization"),
            "email": item.get("email"),
            "phone": item.get("phone"),
            "website": item.get("website"),
            "location": item.get("location"),
            "country": item.get("country"),
            "bio": item.get("bio"),
            "social_links": item.get("social_links") or {},
            "tags": item.get("tags") or [],
            "notes": item.get("notes"),
        })

    return {"contacts": contacts}


@router.post("/confirm")
async def confirm_contacts(body: ConfirmBody, db: AsyncSession = Depends(get_db)):
    """Save parsed contacts to the unified contacts table."""
    results = {"added": 0, "skipped": 0, "by_category": {}}

    for c in body.contacts:
        cat = c.category if c.category in VALID_CATEGORIES else "unknown"
        name = c.name.strip()
        try:
            exists = await db.execute(
                text("SELECT id FROM contacts WHERE name = :n AND category = :cat"),
                {"n": name, "cat": cat}
            )
            if exists.first():
                results["skipped"] += 1
                continue

            embed_text = f"{name} {c.organization or ''} {c.bio or ''} {' '.join(c.tags)}"
            emb = await embed(embed_text)
            emb_str = f"[{','.join(str(x) for x in emb)}]"

            await db.execute(text("""
                INSERT INTO contacts
                    (category, name, role, organization, email, phone, website,
                     location, country, bio, social_links, tags, notes, embedding)
                VALUES
                    (:category, :name, :role, :organization, :email, :phone, :website,
                     :location, :country, :bio, CAST(:social_links AS jsonb), :tags, :notes,
                     CAST(:embedding AS vector))
                ON CONFLICT (name, category) DO NOTHING
            """), {
                "category": cat, "name": name, "role": c.role, "organization": c.organization,
                "email": c.email, "phone": c.phone, "website": c.website,
                "location": c.location, "country": c.country, "bio": c.bio,
                "social_links": json.dumps(c.social_links), "tags": c.tags,
                "notes": c.notes, "embedding": emb_str,
            })
            await db.commit()
            results["added"] += 1
            results["by_category"][cat] = results["by_category"].get(cat, 0) + 1

        except Exception as e:
            await db.rollback()
            logger.error(f"[Contacts/confirm] Failed saving {name}: {e}")
            results["skipped"] += 1

    parts = [f"{v} {k}" for k, v in results["by_category"].items()]
    msg = f"Added {results['added']} contact(s)" + (f" ({', '.join(parts)})" if parts else "")
    if results["skipped"]:
        msg += f", skipped {results['skipped']} duplicate(s)"

    return {**results, "message": msg}


@router.post("/scan")
async def scan_all_contacts(background_tasks: BackgroundTasks):
    """Trigger web scanning across all contact categories."""
    from app.agents.web_ingestor import run_all
    background_tasks.add_task(run_all)
    return {"status": "scanning", "message": "Scanning all contact categories — check back in ~5 minutes"}
