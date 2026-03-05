"""
Collector Intelligence Agent
Builds and enriches profiles of art collectors and patrons.
Can be seeded with a name or URL; Claude enriches with structured data.
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
Research the following art collector and return structured data as JSON:

Collector: {name}
Additional context: {context}

Return a single JSON object with:
- name (string)
- bio (string, 2-4 sentences)
- location (string)
- country (string)
- interests (array of artistic genres/media they collect)
- known_works (array of notable works they own, if known)
- institutions (array of museums/galleries they support)
- contact_url (string or null)
- social_links (object with platform keys, e.g. {{"instagram": "url"}})
- notes (string — any other relevant intelligence)

Only include factual, publicly available information."""


class CollectorIntel:
    async def enrich(self, name: str, context: str = "") -> str | None:
        """Research and save a collector profile. Returns the new row ID."""
        prompt = ENRICH_PROMPT.format(name=name, context=context)
        raw = await generate(prompt)

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            logger.warning(f"[CollectorIntel] No JSON for {name}")
            return None

        data = json.loads(match.group())
        return await self._save(data)

    async def _save(self, data: dict) -> str | None:
        if not data.get("name"):
            return None

        embed_text = f"{data['name']}\n{data.get('bio', '')}\n{' '.join(data.get('interests', []))}"
        embedding = await embed(embed_text)
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    INSERT INTO collectors
                        (name, bio, location, country, interests, known_works,
                         institutions, contact_url, social_links, notes, embedding)
                    VALUES
                        (:name, :bio, :location, :country, :interests, :known_works,
                         :institutions, :contact_url, :social_links::jsonb, :notes, :embedding::vector)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """),
                {
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "location": data.get("location"),
                    "country": data.get("country"),
                    "interests": data.get("interests", []),
                    "known_works": data.get("known_works", []),
                    "institutions": data.get("institutions", []),
                    "contact_url": data.get("contact_url"),
                    "social_links": json.dumps(data.get("social_links", {})),
                    "notes": data.get("notes"),
                    "embedding": embedding_str,
                },
            )
            await db.commit()
            row = result.first()
            return str(row[0]) if row else None
