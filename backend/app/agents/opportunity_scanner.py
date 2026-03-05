"""
Opportunity Scanner Agent
Scrapes art open calls, residencies, commissions, and festivals.
Sources: ResArtis, CaFÉ, Artdeadline-style pages, Submittable.
"""
import logging
from bs4 import BeautifulSoup
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

SOURCES = [
    {
        "url": "https://www.resartis.org/residencies",
        "category": "residency",
        "name": "ResArtis",
    },
    {
        "url": "https://artistcommunities.org/residencies",
        "category": "residency",
        "name": "Artist Communities Alliance",
    },
    {
        "url": "https://callforentry.org",
        "category": "open_call",
        "name": "CaFÉ",
    },
]

EXTRACT_PROMPT = """Extract structured opportunity data from the following web page text.
Return a JSON array of objects with these fields:
- title (string)
- description (string, 2-3 sentences)
- organizer (string)
- location (string)
- country (string)
- deadline (string, ISO date YYYY-MM-DD or null)
- fee (string or null)
- award (string or null)
- url (string)
- tags (array of strings)

Only include clearly identifiable art opportunities. If no opportunities found, return [].

Page text:
{text}"""


class OpportunityScanner:
    async def run(self) -> int:
        saved = 0
        for source in SOURCES:
            try:
                count = await self._scrape_source(source)
                saved += count
                logger.info(f"[OpportunityScanner] {source['name']}: {count} saved")
            except Exception as e:
                logger.error(f"[OpportunityScanner] Failed {source['name']}: {e}")
        return saved

    async def _scrape_source(self, source: dict) -> int:
        from scraper.browser import fetch_text
        text_content = await fetch_text(source["url"])
        text_content = text_content[:12000]  # token limit

        raw = await generate(EXTRACT_PROMPT.format(text=text_content))

        import json, re
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return 0

        items = json.loads(match.group())
        return await self._save_items(items, source["category"])

    async def _save_items(self, items: list[dict], category: str) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                if not item.get("title") or not item.get("url"):
                    continue
                # Skip duplicates
                exists = await db.execute(
                    text("SELECT id FROM opportunities WHERE url = :url"),
                    {"url": item["url"]},
                )
                if exists.first():
                    continue

                embed_text = f"{item['title']}\n{item.get('description', '')}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"

                await db.execute(
                    text("""
                        INSERT INTO opportunities
                            (title, description, category, organizer, location, country,
                             deadline, fee, award, url, tags, embedding)
                        VALUES
                            (:title, :description, :category, :organizer, :location, :country,
                             :deadline, :fee, :award, :url, :tags, :embedding::vector)
                        ON CONFLICT (url) DO NOTHING
                    """),
                    {
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "category": category,
                        "organizer": item.get("organizer"),
                        "location": item.get("location"),
                        "country": item.get("country"),
                        "deadline": item.get("deadline"),
                        "fee": item.get("fee"),
                        "award": item.get("award"),
                        "url": item.get("url"),
                        "tags": item.get("tags", []),
                        "embedding": embedding_str,
                    },
                )
                saved += 1
            await db.commit()
        return saved
