"""
Tavily Web Search Scanner
Searches the live web for art opportunities across all contemporary art forms.
Runs queries per category and saves new results to the database.
"""
import asyncio
import json
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

# One list of (query, category) pairs — covers all 6 categories across all art forms
QUERIES: list[tuple[str, str]] = [
    # open_call
    ("contemporary art open call 2026 submissions deadline", "open_call"),
    ("photography open call 2026 apply submissions", "open_call"),
    ("painting drawing printmaking open call 2026", "open_call"),
    ("digital new media video art open call 2026", "open_call"),
    ("interdisciplinary mixed media open call 2026", "open_call"),
    # residency
    ("art residency open applications 2026 all media", "residency"),
    ("photography artist residency 2026 apply", "residency"),
    ("international art residency 2026 contemporary", "residency"),
    # commission
    ("public art commission opportunity 2026 artists", "commission"),
    ("contemporary art commission call 2026", "commission"),
    # grant
    ("art grant funding 2026 application open", "grant"),
    ("contemporary art grant award 2026 apply", "grant"),
    ("photography artist grant 2026 funding", "grant"),
    ("emerging artist grant 2026 all disciplines", "grant"),
    # festival
    ("art festival open call submissions 2026", "festival"),
    ("international film video art festival 2026 submissions", "festival"),
    # contest
    ("art contest competition 2026 cash prize open", "contest"),
    ("photography contest prize 2026 submit", "contest"),
    ("contemporary art competition award 2026 enter", "contest"),
    ("digital art video contest prize 2026", "contest"),
]

_INCLUSION_RULE = """
INCLUSION RULE — include an opportunity if ANY of these apply:
  • Open to all or multiple art forms (interdisciplinary, open media, any medium)
  • Explicitly welcomes digital art, new media, or technology-based work
  • Covers a broad contemporary category: photography, video, installation, print,
    performance, drawing, painting, mixed media

EXCLUSION RULE — skip if BOTH are true:
  • Restricted to a single traditional medium (e.g. "oil painting only",
    "ceramics only", "sculpture only", "jewellery only")
  • Makes no mention of digital, new media, photography, video, or contemporary practice

If ambiguous, include it."""

EXTRACT_PROMPT = """From the following search results about art opportunities, extract structured data.
Return a JSON array of objects with these fields:
- title (string)
- description (string, 2-3 sentences about the opportunity)
- organizer (string, the organisation offering it)
- location (string, city/country)
- country (string)
- deadline (string, ISO date YYYY-MM-DD or null if not mentioned)
- fee (string or null, e.g. "Free" or "$25")
- award (string or null, e.g. "$10,000 + exhibition")
- url (string, the direct link to apply or learn more)
- tags (array of strings)
{inclusion_rule}
Only include real, verifiable art opportunities. Skip news articles and blog posts.
If no clear opportunities found, return [].

Search results:
{{results}}"""

EXTRACT_PROMPT = EXTRACT_PROMPT.format(inclusion_rule=_INCLUSION_RULE)


class TavilyScanner:
    def __init__(self):
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def run(self) -> int:
        total = 0
        seen_urls: set = set()

        for query, category in QUERIES:
            try:
                count, urls = await self._search_and_save(query, category, seen_urls)
                seen_urls.update(urls)
                total += count
                logger.info(f"[TavilyScanner] '{query}' [{category}]: {count} saved")
            except Exception as e:
                logger.error(f"[TavilyScanner] Failed '{query}': {e}")
            await asyncio.sleep(5)

        logger.info(f"[TavilyScanner] Total saved: {total}")
        return total

    async def _search_and_save(self, query: str, category: str, seen_urls: set) -> tuple[int, list]:
        response = await self.client.search(
            query=query,
            search_depth="advanced",
            max_results=7,
            include_answer=False,
        )

        results = response.get("results", [])
        if not results:
            return 0, []

        formatted = "\n\n".join(
            f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nContent: {r.get('content', '')[:600]}"
            for r in results
        )

        raw = await generate(EXTRACT_PROMPT.format(results=formatted))
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return 0, []

        try:
            items = json.loads(match.group())
        except json.JSONDecodeError:
            return 0, []

        saved_urls: list = []
        saved = await self._save_items(items, category, seen_urls, saved_urls)
        return saved, saved_urls

    async def _save_items(self, items: list[dict], category: str, seen_urls: set, saved_urls: list) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                url = item.get("url")
                if not item.get("title") or not url or url in seen_urls:
                    continue

                exists = await db.execute(
                    text("SELECT id FROM opportunities WHERE url = :url"), {"url": url}
                )
                if exists.first():
                    seen_urls.add(url)
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
                        "deadline": _parse_deadline(item.get("deadline")),
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
