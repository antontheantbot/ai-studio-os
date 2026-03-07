"""
Opportunity Scanner Agent
Scans art open calls, residencies, commissions, grants, and festivals.
Uses Tavily for live web search + httpx/BeautifulSoup for targeted scraping.
Covers digital art, new media, photography, painting, printmaking, and
all forms of contemporary art.
"""
import asyncio
import json
import logging
from datetime import date

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import text
from tavily import AsyncTavilyClient

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

# ── Hardcoded sources (scraped directly) ─────────────────────────────────────

SOURCES = [
    # Residencies
    {"url": "https://resartis.org/residencies/", "category": "residency", "name": "ResArtis"},
    {"url": "https://artistcommunities.org/residencies", "category": "residency", "name": "Artist Communities Alliance"},
    # Open calls — digital / new media
    {"url": "https://callforentry.org", "category": "open_call", "name": "CaFÉ"},
    {"url": "https://www.foundwork.art/opportunities", "category": "open_call", "name": "Foundwork"},
    {"url": "https://www.sundance.org/apply/", "category": "open_call", "name": "Sundance"},
    # Open calls — photography
    {"url": "https://www.lensculture.com/competitions", "category": "contest", "name": "LensCulture"},
    {"url": "https://www.photolucida.org/calls-for-entry/", "category": "open_call", "name": "Photolucida"},
    # Contests
    {"url": "https://www.artaward.org", "category": "contest", "name": "Art Award"},
    {"url": "https://www.1x.com/contest", "category": "contest", "name": "1x Photography Contest"},
    {"url": "https://www.creativeboom.com/competitions/", "category": "contest", "name": "Creative Boom"},
    {"url": "https://www.photoawards.com", "category": "contest", "name": "IPA Photo Awards"},
    {"url": "https://www.worldpressphoto.org/apply", "category": "contest", "name": "World Press Photo"},
    {"url": "https://www.artconnect.com/opportunities?category=competition", "category": "contest", "name": "ArtConnect Competitions"},
    # Open calls — contemporary art (broad)
    {"url": "https://www.artsy.net/articles?tag=open-calls", "category": "open_call", "name": "Artsy Open Calls"},
    {"url": "https://www.e-flux.com/announcements/", "category": "open_call", "name": "e-flux Announcements"},
    {"url": "https://aestheticamagazine.com/opportunities/", "category": "open_call", "name": "Aesthetica"},
    # Commissions / Grants
    {"url": "https://www.creativecapital.org/funding-opportunities/", "category": "commission", "name": "Creative Capital"},
    {"url": "https://www.artadia.org/apply/", "category": "grant", "name": "Artadia"},
    # Festivals — digital / media art
    {"url": "https://transmediale.de/en", "category": "festival", "name": "Transmediale"},
    {"url": "https://ars.electronica.art/news/", "category": "festival", "name": "Ars Electronica"},
    {"url": "https://www.siggraph.org/learn/conference-content/", "category": "festival", "name": "SIGGRAPH"},
]

# ── Tavily queries (live internet search for new opportunities) ────────────────

TAVILY_QUERIES = [
    "contemporary art open call 2026 deadline submissions",
    "photography open call competition 2026 apply",
    "art residency open call 2026 applications",
    "painting drawing printmaking open call 2026",
    "art grant funding opportunity 2026 artists apply",
    "digital art new media open call 2026",
    "contemporary art prize award 2026 submissions open",
    "emerging artist opportunity residency grant 2026",
    "international art festival open call 2026",
    "photography prize competition award 2026",
    "art contest 2026 cash prize open submissions",
    "contemporary art competition 2026 enter apply",
    "digital photography video art contest prize 2026",
]

# ── Prompts ───────────────────────────────────────────────────────────────────

_INCLUSION_RULE = """
INCLUSION RULE — include an opportunity if ANY of these apply:
  • It is open to all or multiple art forms (interdisciplinary, open media, any medium)
  • It explicitly welcomes digital art, new media, or technology-based work
  • It covers a broad category that digital artists commonly work in (photography, video,
    installation, print, performance, drawing, painting, mixed media)

EXCLUSION RULE — skip an opportunity if BOTH of these are true:
  • It is restricted to a single traditional medium (e.g. "oil painting only",
    "watercolour only", "ceramics only", "sculpture only", "jewellery only")
  • It makes no mention of digital, new media, photography, video, or contemporary practice

In other words: if it explicitly says "no digital art" or is narrowly for one non-digital
craft medium, skip it. If there is any ambiguity, include it."""

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
- tags (array of strings relevant to the opportunity)
{inclusion_rule}
Only include clearly identifiable art opportunities with real deadlines in the future.
If no opportunities found, return [].

Page text:
{{text}}"""

TAVILY_EXTRACT_PROMPT = """From these web search results, extract art opportunities (open calls, residencies, commissions, grants, festivals, prizes).
Return a JSON array of objects with these fields:
- title (string)
- description (string, 2-3 sentences about the opportunity)
- organizer (string, who is running it)
- location (string)
- country (string)
- deadline (string, ISO date YYYY-MM-DD or null if not found)
- fee (string or null)
- award (string or null, prize money or stipend if mentioned)
- url (string, the direct URL to apply or learn more)
- category (string: "open_call" | "residency" | "commission" | "grant" | "festival" | "contest")
- tags (array of strings: art forms, themes, or keywords)
{inclusion_rule}
Only include opportunities with upcoming deadlines (future dates). Return [] if none found.

Search results:
{{results}}"""

EXTRACT_PROMPT = EXTRACT_PROMPT.format(inclusion_rule=_INCLUSION_RULE)
TAVILY_EXTRACT_PROMPT = TAVILY_EXTRACT_PROMPT.format(inclusion_rule=_INCLUSION_RULE)

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
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)


def parse_deadline(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        return None


class OpportunityScanner:
    def __init__(self):
        self._tavily = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def run(self) -> int:
        saved = 0

        # 1. Scrape hardcoded sources
        for source in SOURCES:
            try:
                count = await self._scrape_source(source)
                saved += count
                logger.info(f"[OpportunityScanner] {source['name']}: {count} saved")
            except Exception as e:
                logger.error(f"[OpportunityScanner] Failed {source['name']}: {e}")

        # 2. Tavily live web search
        try:
            count = await self._tavily_scan()
            saved += count
            logger.info(f"[OpportunityScanner] Tavily scan: {count} saved")
        except Exception as e:
            logger.error(f"[OpportunityScanner] Tavily scan failed: {e}")

        return saved

    async def _scrape_source(self, source: dict) -> int:
        text_content = await fetch_text(source["url"])
        text_content = text_content[:12000]

        raw = await generate(EXTRACT_PROMPT.format(text=text_content))

        start, end = raw.find("["), raw.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return 0

        try:
            items = json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            logger.warning(f"[OpportunityScanner] JSON parse failed for {source['name']}")
            return 0

        for item in items:
            item.setdefault("category", source["category"])

        return await self._save_items(items)

    async def _tavily_scan(self) -> int:
        all_results = []
        seen_urls: set = set()

        for query in TAVILY_QUERIES:
            try:
                response = await self._tavily.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_answer=False,
                )
                for r in response.get("results", []):
                    if r.get("url") not in seen_urls:
                        all_results.append(r)
                        seen_urls.add(r.get("url", ""))
                logger.info(f"[OpportunityScanner] Tavily '{query}': {len(response.get('results', []))} results")
            except Exception as e:
                logger.error(f"[OpportunityScanner] Tavily query failed '{query}': {e}")
            await asyncio.sleep(5)

        if not all_results:
            return 0

        formatted = "\n\n".join(
            f"Source: {r.get('url', '')}\nTitle: {r.get('title', '')}\nContent: {r.get('content', '')[:500]}"
            for r in all_results[:50]
        )

        try:
            raw = await generate(TAVILY_EXTRACT_PROMPT.format(results=formatted))
            start, end = raw.find("["), raw.rfind("]")
            if start == -1 or end == -1 or end <= start:
                return 0
            items = json.loads(raw[start:end + 1])
            return await self._save_items(items)
        except Exception as e:
            logger.error(f"[OpportunityScanner] Tavily extraction failed: {e}")
            return 0

    async def _save_items(self, items: list[dict]) -> int:
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
                        "category": item.get("category", "open_call"),
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


_scanner = OpportunityScanner()


async def run() -> int:
    return await _scanner.run()


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
