"""
Unified Contacts API — parse free-form text into structured contacts across all categories,
with a confirm step before saving to the appropriate underlying table.
"""
import json
import re
import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.llm import generate
from app.services.embeddings import embed

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Parse prompt ─────────────────────────────────────────────────────────────

PARSE_PROMPT = """You are parsing contact information for an art world CRM used by a professional artist studio.

Analyze the pasted text and extract ALL contacts found. For each contact determine the category and extract all available fields.

Return a JSON array. Each object must have:
- category: one of "curator", "journalist", "institution", "collector", "corporation", or "unknown" if you genuinely cannot tell
- uncertain: boolean — true if you are not confident about the category assignment
- name: string (required — person name or organisation name)
- role: string or null (job title, e.g. "Senior Curator", "Director", "Editor")
- organization: string or null (employer / gallery / publication / institution)
- email: string or null
- phone: string or null
- website: string or null
- location: string or null (city)
- country: string or null
- bio: string or null (2–3 sentences)
- social_links: object (any of: twitter, instagram, linkedin, website — full URLs)
- tags: array of strings (topics, interests, focus areas)
- notes: string or null

Categorisation rules:
- curator: works at a museum/gallery, curates exhibitions
- journalist: writer/critic/editor for art publications or press
- institution: museum, gallery, kunsthalle, foundation, biennial (use org name)
- collector: private art collector or patron
- corporation: company, brand, PR agency, sponsor, tech firm, luxury brand
- unknown: use this if there is genuinely not enough information to determine the category

IMPORTANT: Never drop a contact because you are unsure of the category. Always include it with uncertain=true and category="unknown" (or your best guess).

If the text contains multiple contacts return all of them. Return [] if nothing parseable.

Text to parse:
{text}"""

# ─── Schemas ──────────────────────────────────────────────────────────────────

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


# ─── Parse (no save) ─────────────────────────────────────────────────────────

@router.post("/parse")
async def parse_contacts(body: ParseBody):
    """Parse pasted text and return structured contact previews — does NOT save."""
    if not body.text.strip():
        return {"contacts": []}

    raw = await generate(PARSE_PROMPT.format(text=body.text[:10000]))
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.error(f"[Contacts/parse] No JSON array: {raw[:300]}")
        return {"contacts": []}

    try:
        items = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        logger.error(f"[Contacts/parse] JSON decode error: {e}")
        return {"contacts": []}

    # Normalise and validate
    contacts = []
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        cat = (item.get("category") or "").lower()
        uncertain = bool(item.get("uncertain")) or cat not in ("curator", "journalist", "institution", "collector", "corporation")
        if cat not in ("curator", "journalist", "institution", "collector", "corporation"):
            cat = "curator"
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


# ─── Confirm (save) ──────────────────────────────────────────────────────────

@router.post("/confirm")
async def confirm_contacts(body: ConfirmBody, db: AsyncSession = Depends(get_db)):
    """Save the (user-reviewed) parsed contacts to the appropriate tables."""
    results = {"added": 0, "skipped": 0, "by_category": {}}

    for c in body.contacts:
        cat = c.category
        try:
            saved = await _save_contact(c, db)
            if saved:
                results["added"] += 1
                results["by_category"][cat] = results["by_category"].get(cat, 0) + 1
            else:
                results["skipped"] += 1
        except Exception as e:
            logger.error(f"[Contacts/confirm] Failed saving {c.name}: {e}")
            results["skipped"] += 1

    await db.commit()

    parts = [f"{v} {k}" for k, v in results["by_category"].items()]
    msg = f"Added {results['added']} contact(s)" + (f" ({', '.join(parts)})" if parts else "")
    if results["skipped"]:
        msg += f", skipped {results['skipped']} duplicate(s)"

    return {**results, "message": msg}


async def _save_contact(c: ParsedContact, db: AsyncSession) -> bool:
    """Route contact to the correct table. Returns True if inserted."""
    from sqlalchemy import text

    name = c.name.strip()

    if c.category == "journalist":
        exists = await db.execute(text("SELECT id FROM journalists WHERE name = :n"), {"n": name})
        if exists.first():
            return False
        await db.execute(text("""
            INSERT INTO journalists
                (id, name, bio, publications, beats, email, social_links, location, country, notes)
            VALUES
                (gen_random_uuid(), :name, :bio, CAST(:publications AS jsonb), CAST(:beats AS jsonb),
                 :email, CAST(:social_links AS jsonb), :location, :country, :notes)
            ON CONFLICT (name) DO NOTHING
        """), {
            "name": name,
            "bio": c.bio,
            "publications": json.dumps([c.organization] if c.organization else []),
            "beats": json.dumps(c.tags),
            "email": c.email,
            "social_links": json.dumps(c.social_links),
            "location": c.location,
            "country": c.country,
            "notes": c.notes,
        })
        return True

    elif c.category == "curator":
        exists = await db.execute(text("SELECT id FROM curators WHERE name = :n"), {"n": name})
        if exists.first():
            return False
        embed_text = f"{name} {c.organization or ''} {c.bio or ''} {' '.join(c.tags)}"
        emb = await embed(embed_text)
        emb_str = f"[{','.join(str(x) for x in emb)}]"
        await db.execute(text("""
            INSERT INTO curators
                (name, bio, institution, role, location, country,
                 focus_areas, notable_shows, contact_email, contact_url, social_links, notes, embedding)
            VALUES
                (:name, :bio, :institution, :role, :location, :country,
                 :focus_areas, :notable_shows, :contact_email, :contact_url,
                 CAST(:social_links AS jsonb), :notes, CAST(:embedding AS vector))
            ON CONFLICT DO NOTHING
        """), {
            "name": name, "bio": c.bio, "institution": c.organization, "role": c.role,
            "location": c.location, "country": c.country, "focus_areas": c.tags,
            "notable_shows": [], "contact_email": c.email, "contact_url": c.website,
            "social_links": json.dumps(c.social_links), "notes": c.notes, "embedding": emb_str,
        })
        return True

    elif c.category == "institution":
        exists = await db.execute(text("SELECT id FROM institutions WHERE name = :n"), {"n": name})
        if exists.first():
            return False
        await db.execute(text("""
            INSERT INTO institutions
                (id, name, city, country, type, website, focus_areas, notes)
            VALUES
                (gen_random_uuid(), :name, :city, :country, :type, :website, CAST(:focus_areas AS jsonb), :notes)
            ON CONFLICT (name) DO NOTHING
        """), {
            "name": name, "city": c.location, "country": c.country,
            "type": c.role, "website": c.website,
            "focus_areas": json.dumps(c.tags), "notes": c.notes,
        })
        return True

    elif c.category == "collector":
        exists = await db.execute(text("SELECT id FROM collectors WHERE name = :n"), {"n": name})
        if exists.first():
            return False
        embed_text = f"{name} {c.bio or ''} {' '.join(c.tags)}"
        emb = await embed(embed_text)
        emb_str = f"[{','.join(str(x) for x in emb)}]"
        await db.execute(text("""
            INSERT INTO collectors
                (name, bio, location, country, interests, known_works, institutions,
                 contact_email, contact_url, social_links, notes, embedding)
            VALUES
                (:name, :bio, :location, :country, :interests, :known_works, :institutions,
                 :contact_email, :contact_url, CAST(:social_links AS jsonb), :notes, CAST(:embedding AS vector))
            ON CONFLICT (name) DO NOTHING
        """), {
            "name": name, "bio": c.bio, "location": c.location, "country": c.country,
            "interests": c.tags, "known_works": [], "institutions": [c.organization] if c.organization else [],
            "contact_email": c.email, "contact_url": c.website,
            "social_links": json.dumps(c.social_links), "notes": c.notes, "embedding": emb_str,
        })
        return True

    elif c.category == "corporation":
        exists = await db.execute(text("SELECT id FROM corporations WHERE name = :n"), {"n": name})
        if exists.first():
            return False
        embed_text = f"{name} {c.role or ''} {' '.join(c.tags)}"
        emb = await embed(embed_text)
        emb_str = f"[{','.join(str(x) for x in emb)}]"
        await db.execute(text("""
            INSERT INTO corporations
                (name, type, contact_name, contact_role, email, phone, website,
                 city, country, focus_areas, tags, notes, social_links, embedding)
            VALUES
                (:name, :type, :contact_name, :contact_role, :email, :phone, :website,
                 :city, :country, :focus_areas, :tags, :notes, CAST(:social_links AS jsonb), CAST(:embedding AS vector))
            ON CONFLICT (name) DO NOTHING
        """), {
            "name": name, "type": c.role, "contact_name": None, "contact_role": None,
            "email": c.email, "phone": c.phone, "website": c.website,
            "city": c.location, "country": c.country, "focus_areas": c.tags, "tags": [],
            "notes": c.notes, "social_links": json.dumps(c.social_links), "embedding": emb_str,
        })
        return True

    return False


# ─── Scan all ─────────────────────────────────────────────────────────────────

@router.post("/scan")
async def scan_all_contacts(background_tasks: BackgroundTasks):
    """Trigger web scanning across all contact categories."""
    from app.agents.web_ingestor import run_all
    background_tasks.add_task(run_all)
    return {"status": "scanning", "message": "Scanning all contact categories — check back in ~5 minutes"}
