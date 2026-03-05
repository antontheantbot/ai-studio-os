"""
Tavily Web Search Scanner
Searches the live web for digital art opportunities using Tavily's search API.
Runs queries across multiple topics and saves new results to the database.
"""
import logging
import re
from datetime import date

from sqlalchemy import text
from tavily import AsyncTavilyClient

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "digital art open call 2026",
    "new media art residency 2026",
    "interactive installation open call 2026",
    "AI art prize award 2026",
    "generative art festival open call 2026",
    "immersive art commission 2026",
    "media art residency application 2026",
    "video art open call deadline 2026",
]

GRANT_QUERIES = [
    "digital art grant funding 2026 application",
    "contemporary art grant open 2026",
    "new media art grant award 2026",
    "artist grant technology art 2026",
    "AI art research grant 2026",
    "public art grant commission 2026 apply",
    "experimental art grant foundation 2026",
    "emerging artist grant digital 2026",
]

EXTRACT_PROMPT = """From the following search results about art opportunities, extract structured data.
Return a JSON array of objects with these fields:
- title (string)
- description (string, 2-3 sentences about the opportunity)
- organizer (string, the organization offering it)
- location (string, city/country)
- country (string)
- deadline (string, ISO date YYYY-MM-DD or null if not mentioned)
- fee (string or null, e.g. "Free" or "$25")
- award (string or null, e.g. "$10,000 + exhibition")
- url (string, the direct link to apply or learn more)
- tags (array of strings, e.g. ["digital art", "residency", "AI"])

Only include real, verifiable art opportunities. Skip news articles, listicles, and blog posts.
If no clear opportunities found, return [].

Search results:
{results}"""


class TavilyScanner:
    def __init__(self):
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def run(self) -> int:
        """Run all search queries and save new opportunities."""
        total_saved = 0
        seen_urls: set = set()

        for query in SEARCH_QUERIES:
            try:
                count, urls = await self._search_and_save(query, seen_urls)
                seen_urls.update(urls)
                total_saved += count
                logger.info(f"[TavilyScanner] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[TavilyScanner] Failed query '{query}': {e}")

        for query in GRANT_QUERIES:
            try:
                count, urls = await self._search_and_save(query, seen_urls, force_category="grant")
                seen_urls.update(urls)
                total_saved += count
                logger.info(f"[TavilyScanner] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[TavilyScanner] Failed grant query '{query}': {e}")

        logger.info(f"[TavilyScanner] Total saved: {total_saved}")
        return total_saved

    async def _search_and_save(self, query: str, seen_urls: set, force_category: str | None = None) -> tuple[int, list]:
        response = await self.client.search(
            query=query,
            search_depth="advanced",
            max_results=7,
            include_answer=False,
        )

        results = response.get("results", [])
        if not results:
            return 0, []

        # Format results for Claude extraction
        formatted = "\n\n".join(
            f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nContent: {r.get('content', '')[:600]}"
            for r in results
        )

        raw = await generate(EXTRACT_PROMPT.format(results=formatted))

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return 0, []

        import json
        try:
            items = json.loads(match.group())
        except json.JSONDecodeError:
            return 0, []

        # Infer category from query
        if force_category:
            category = force_category
        elif "residency" in query:
            category = "residency"
        elif "commission" in query:
            category = "commission"
        elif "festival" in query or "prize" in query or "award" in query:
            category = "festival"
        else:
            category = "open_call"

        saved_urls = []
        saved = await self._save_items(items, category, seen_urls, saved_urls)
        return saved, saved_urls

    async def _save_items(
        self, items: list[dict], category: str, seen_urls: set, saved_urls: list
    ) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                url = item.get("url")
                if not item.get("title") or not url:
                    continue
                if url in seen_urls:
                    continue

                exists = await db.execute(
                    text("SELECT id FROM opportunities WHERE url = :url"),
                    {"url": url},
                )
                if exists.first():
                    seen_urls.add(url)
                    continue

                deadline = _parse_deadline(item.get("deadline"))

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
                        "deadline": deadline,
                        "fee": item.get("fee"),
                        "award": item.get("award"),
                        "url": url,
                        "tags": item.get("tags", []),
                        "embedding": embedding_str,
                    },
                )
                saved += 1
                seen_urls.add(url)
                saved_urls.append(url)

            await db.commit()
        return saved


def _parse_deadline(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        return None


_scanner = TavilyScanner()


async def run() -> int:
    return await _scanner.run()
