"""
Opportunity Scanner Agent
Scrapes art open calls, residencies, commissions, and festivals.
Uses httpx + BeautifulSoup for fetching, Claude for structured extraction.
"""
import json
import logging
import re
from datetime import date

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

SOURCES = [
    # Residencies
    {"url": "https://resartis.org/residencies/", "category": "residency", "name": "ResArtis"},
    {"url": "https://artistcommunities.org/residencies", "category": "residency", "name": "Artist Communities Alliance"},
    # Open calls
    {"url": "https://callforentry.org", "category": "open_call", "name": "CaFÉ"},
    {"url": "https://www.foundwork.art/opportunities", "category": "open_call", "name": "Foundwork"},
    {"url": "https://www.sundance.org/apply/", "category": "open_call", "name": "Sundance"},
    # Commissions / Grants
    {"url": "https://www.creativecapital.org/funding-opportunities/", "category": "commission", "name": "Creative Capital"},
    # Festivals
    {"url": "https://transmediale.de/en", "category": "festival", "name": "Transmediale"},
    {"url": "https://ars.electronica.art/news/", "category": "festival", "name": "Ars Electronica"},
    {"url": "https://www.siggraph.org/learn/conference-content/", "category": "festival", "name": "SIGGRAPH"},
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
- url (string, full URL to the specific opportunity)
- tags (array of strings relevant to digital/media art)

Focus on opportunities relevant to digital art, new media, installations, and technology-based art.
Only include clearly identifiable art opportunities with real deadlines in the future.
If no opportunities found, return [].

Page text:
{text}"""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def fetch_text(url: str, timeout: int = 25) -> str:
    """Fetch and extract visible text from a URL using httpx + BeautifulSoup."""
    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=timeout, verify=False
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Collapse blank lines
        lines = [ln for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)


def parse_deadline(raw: str | None) -> date | None:
    """Convert ISO date string to Python date, return None on failure."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        return None


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
        text_content = await fetch_text(source["url"])
        text_content = text_content[:12000]  # stay within token limits

        raw = await generate(EXTRACT_PROMPT.format(text=text_content))

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return 0

        try:
            items = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning(f"[OpportunityScanner] JSON parse failed for {source['name']}")
            return 0

        return await self._save_items(items, source["category"])

    async def _save_items(self, items: list[dict], category: str) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                if not item.get("title") or not item.get("url"):
                    continue

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
                             :deadline, :fee, :award, :url, :tags, CAST(:embedding AS vector))
                        ON CONFLICT (url) DO NOTHING
                    """),
                    {
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "category": category,
                        "organizer": item.get("organizer"),
                        "location": item.get("location"),
                        "country": item.get("country"),
                        "deadline": parse_deadline(item.get("deadline")),
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


# Module-level instance for Celery tasks and direct calls
_scanner = OpportunityScanner()


async def run() -> int:
    """Run the full opportunity scan."""
    return await _scanner.run()


# ═══════════════════════════════════════════════════════════════════════════
# ENHANCED: Fit Scoring Integration
# ═══════════════════════════════════════════════════════════════════════════

async def scan_with_scoring() -> int:
    """Run the opportunity scanner and calculate fit scores for all results."""
    from app.services.fit_scoring import score_and_update_opportunity

    total = await run()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT id, title, description, category, url FROM opportunities WHERE fit_score IS NULL")
        )
        opportunities = result.fetchall()

        for opp in opportunities:
            opp_data = {
                "title": opp.title,
                "description": opp.description,
                "category": opp.category,
            }
            await score_and_update_opportunity(db, str(opp.id), opp_data)

        logger.info(f"[OpportunityScanner] Scored {len(opportunities)} opportunities")

    return total
