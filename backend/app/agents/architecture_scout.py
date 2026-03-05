"""
Architecture Scout Agent
Discovers interesting architectural locations suitable for photography or installations.
Uses Claude to analyze pages and extract structured location data.
"""
import logging
import json
import re
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

SOURCES = [
    "https://www.archdaily.com/search/projects/categories/urban-design",
    "https://www.architectural-review.com/buildings",
    "https://divisare.com/projects",
]

EXTRACT_PROMPT = """Extract architectural locations from the following page text that would be
interesting for artistic photography or site-specific art installations.

Return a JSON array with fields:
- name (string)
- description (string)
- architect (string or null)
- city (string)
- country (string)
- style (string — e.g. brutalist, modernist, industrial, baroque)
- year_built (integer or null)
- suitability (array: choose from ["photography", "installation", "performance", "projection"])
- source_url (string)
- tags (array of strings)

Page text:
{text}"""


class ArchitectureScout:
    async def run(self) -> int:
        saved = 0
        for url in SOURCES:
            try:
                count = await self._scrape(url)
                saved += count
                logger.info(f"[ArchitectureScout] {url}: {count} saved")
            except Exception as e:
                logger.error(f"[ArchitectureScout] Failed {url}: {e}")
        return saved

    async def _scrape(self, url: str) -> int:
        from scraper.browser import fetch_text
        text_content = await fetch_text(url)
        text_content = text_content[:12000]

        raw = await generate(EXTRACT_PROMPT.format(text=text_content))
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return 0

        items = json.loads(match.group())
        return await self._save_items(items)

    async def _save_items(self, items: list[dict]) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                if not item.get("name"):
                    continue

                embed_text = f"{item['name']} {item.get('style', '')} {item.get('description', '')}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"

                await db.execute(
                    text("""
                        INSERT INTO architecture_locations
                            (name, description, architect, city, country, style,
                             year_built, suitability, source_url, embedding)
                        VALUES
                            (:name, :description, :architect, :city, :country, :style,
                             :year_built, :suitability, :source_url, :embedding::vector)
                    """),
                    {
                        "name": item.get("name"),
                        "description": item.get("description"),
                        "architect": item.get("architect"),
                        "city": item.get("city"),
                        "country": item.get("country"),
                        "style": item.get("style"),
                        "year_built": item.get("year_built"),
                        "suitability": item.get("suitability", []),
                        "source_url": item.get("source_url"),
                        "embedding": embedding_str,
                    },
                )
                saved += 1
            await db.commit()
        return saved
