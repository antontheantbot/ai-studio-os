"""
Curator Intelligence Agent
Builds and enriches profiles of curators and institutions.
"""
import logging
import json
import re
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

ENRICH_PROMPT = """You are a research assistant for an art studio.
Research the following art curator and return structured data as JSON:

Curator: {name}
Institution: {institution}
Additional context: {context}

Return a single JSON object with:
- name (string)
- bio (string, 2-4 sentences)
- institution (string)
- role (string, e.g. "Chief Curator", "Artistic Director")
- location (string)
- country (string)
- focus_areas (array of strings — artistic genres, media, themes they work with)
- notable_shows (array of exhibition titles they curated)
- contact_url (string or null)
- social_links (object)
- notes (string)

Only include factual, publicly available information."""


class CuratorIntel:
    async def enrich(self, name: str, institution: str = "", context: str = "") -> str | None:
        prompt = ENRICH_PROMPT.format(name=name, institution=institution, context=context)
        raw = await generate(prompt)

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            logger.warning(f"[CuratorIntel] No JSON for {name}")
            return None

        data = json.loads(match.group())
        return await self._save(data)

    async def _save(self, data: dict) -> str | None:
        if not data.get("name"):
            return None

        embed_text = (
            f"{data['name']} {data.get('institution', '')}\n"
            f"{data.get('bio', '')}\n"
            f"{' '.join(data.get('focus_areas', []))}"
        )
        embedding = await embed(embed_text)
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    INSERT INTO curators
                        (name, bio, institution, role, location, country,
                         focus_areas, notable_shows, contact_url, social_links, notes, embedding)
                    VALUES
                        (:name, :bio, :institution, :role, :location, :country,
                         :focus_areas, :notable_shows, :contact_url, :social_links::jsonb, :notes, :embedding::vector)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """),
                {
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "institution": data.get("institution"),
                    "role": data.get("role"),
                    "location": data.get("location"),
                    "country": data.get("country"),
                    "focus_areas": data.get("focus_areas", []),
                    "notable_shows": data.get("notable_shows", []),
                    "contact_url": data.get("contact_url"),
                    "social_links": json.dumps(data.get("social_links", {})),
                    "notes": data.get("notes"),
                    "embedding": embedding_str,
                },
            )
            await db.commit()
            row = result.first()
            return str(row[0]) if row else None
