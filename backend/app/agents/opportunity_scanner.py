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
    {
        "url": "https://www.rhizome.org/opportunities/",
        "category": "open_call",
        "name": "Rhizome",
    },
    {
        "url": "https://www.foundwork.art/opportunities",
        "category": "open_call",
        "name": "Foundwork",
    },
    {
        "url": "https://www.creativecapital.org/funding-opportunities/",
        "category": "commission",
        "name": "Creative Capital",
    },
    {
        "url": "https://www.nyfa.org/awards-grants/",
        "category": "commission",
        "name": "NYFA",
    },
    {
        "url": "https://www.transmediale.de/open-call",
        "category": "festival",
        "name": "Transmediale",
    },
    {
        "url": "https://ars.electronica.art/news/en/open-calls/",
        "category": "festival",
        "name": "Ars Electronica",
    },
    {
        "url": "https://www.siggraph.org/learn/conference-content/",
        "category": "festival",
        "name": "SIGGRAPH",
    },
    {
        "url": "https://www.sundance.org/programs/new-frontier/",
        "category": "open_call",
        "name": "Sundance New Frontier",
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


# ═══════════════════════════════════════════════════════════════════════════
# ENHANCED: Fit Scoring Integration
# ═══════════════════════════════════════════════════════════════════════════

async def scan_with_scoring():
    """Run the opportunity scanner and calculate fit scores for all results."""
    from app.services.fit_scoring import calculate_fit_score, score_and_update_opportunity
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    # First run the normal scan
    await run()

    # Then score all opportunities that don't have a fit_score
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT id, title, description, category, budget, url FROM opportunities WHERE fit_score IS NULL")
        )
        opportunities = result.fetchall()

        for opp in opportunities:
            opp_data = {
                "title": opp.title,
                "description": opp.description,
                "category": opp.category,
                "budget": opp.budget,
            }
            await score_and_update_opportunity(db, str(opp.id), opp_data)

        logger.info(f"Scored {len(opportunities)} opportunities")
