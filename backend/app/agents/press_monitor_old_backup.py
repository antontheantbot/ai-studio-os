"""
Press Monitor Agent
Tracks digital art exhibitions, reviews, and news from key publications.
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
    {"url": "https://www.artforum.com/news", "source": "Artforum"},
    {"url": "https://frieze.com/editorial", "source": "Frieze"},
    {"url": "https://www.artnews.com/c/art-news", "source": "ARTnews"},
    {"url": "https://rhizome.org", "source": "Rhizome"},
    {"url": "https://we-make-money-not-art.com", "source": "We Make Money Not Art"},
]

EXTRACT_PROMPT = """Extract press articles and news items from the following page text.
Focus on: exhibitions, digital art, new media, technology in art, artist profiles, reviews.

Return a JSON array with fields:
- title (string)
- summary (string, 2-3 sentences)
- author (string or null)
- published_at (string, ISO datetime or null)
- url (string)
- category (string: "exhibition" | "review" | "news" | "interview")
- tags (array of strings)
- mentioned_artists (array of artist names)

Page text:
{text}"""


class PressMonitor:
    async def run(self) -> int:
        saved = 0
        for source in SOURCES:
            try:
                count = await self._scrape(source)
                saved += count
                logger.info(f"[PressMonitor] {source['source']}: {count} saved")
            except Exception as e:
                logger.error(f"[PressMonitor] Failed {source['source']}: {e}")
        return saved

    async def _scrape(self, source: dict) -> int:
        from scraper.browser import fetch_text
        text_content = await fetch_text(source["url"])
        text_content = text_content[:12000]

        raw = await generate(EXTRACT_PROMPT.format(text=text_content))
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return 0

        items = json.loads(match.group())
        return await self._save_items(items, source["source"])

    async def _save_items(self, items: list[dict], source_name: str) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                if not item.get("title") or not item.get("url"):
                    continue

                exists = await db.execute(
                    text("SELECT id FROM press_items WHERE url = :url"),
                    {"url": item["url"]},
                )
                if exists.first():
                    continue

                embed_text = f"{item['title']}\n{item.get('summary', '')}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"

                await db.execute(
                    text("""
                        INSERT INTO press_items
                            (title, summary, source, author, url, published_at,
                             category, tags, mentioned_artists, embedding)
                        VALUES
                            (:title, :summary, :source, :author, :url, :published_at,
                             :category, :tags, :mentioned_artists, :embedding::vector)
                        ON CONFLICT (url) DO NOTHING
                    """),
                    {
                        "title": item.get("title"),
                        "summary": item.get("summary"),
                        "source": source_name,
                        "author": item.get("author"),
                        "url": item.get("url"),
                        "published_at": item.get("published_at"),
                        "category": item.get("category", "news"),
                        "tags": item.get("tags", []),
                        "mentioned_artists": item.get("mentioned_artists", []),
                        "embedding": embedding_str,
                    },
                )
                saved += 1
            await db.commit()
        return saved
