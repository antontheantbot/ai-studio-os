"""
Shared persistence helpers for scanner agents.
Centralises the opportunity INSERT so schema changes only need one edit.
"""
import logging
from datetime import date

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed

logger = logging.getLogger(__name__)


def parse_deadline(raw: str | None) -> date | None:
    """Parse an ISO date string to a date, returning None on failure."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        return None


async def save_opportunities(
    items: list[dict],
    default_category: str = "open_call",
    seen_urls: set | None = None,
) -> int:
    """
    Insert opportunity dicts into the database.

    - Skips items missing title or url.
    - Skips urls already in seen_urls or already in the DB.
    - Updates seen_urls in place with every url processed (hit or saved).
    - Returns the number of rows inserted.
    """
    if seen_urls is None:
        seen_urls = set()

    saved = 0
    async with AsyncSessionLocal() as db:
        for item in items:
            url = item.get("url")
            if not item.get("title") or not url:
                continue
            if url in seen_urls:
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
                    "category": item.get("category", default_category),
                    "organizer": item.get("organizer"),
                    "location": item.get("location"),
                    "country": item.get("country"),
                    "deadline": parse_deadline(item.get("deadline")),
                    "fee": item.get("fee"),
                    "award": item.get("award"),
                    "url": url,
                    "tags": item.get("tags", []),
                    "embedding": embedding_str,
                },
            )
            saved += 1
            seen_urls.add(url)

        await db.commit()
    return saved
