"""
Knowledge Ingestor Agent
Ingests URLs, raw text, or uploaded content into the knowledge base.
Summarises with Claude, then embeds for semantic search.
"""
import logging
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

SUMMARISE_PROMPT = """Summarise the following article or text for storage in an artist's research knowledge base.

Return:
1. A concise title (if not already provided)
2. A 3-5 sentence summary capturing the key ideas
3. A list of 5-8 relevant tags

Format your response as:
TITLE: <title>
SUMMARY: <summary>
TAGS: <tag1>, <tag2>, ...

Text:
{text}"""


class KnowledgeIngestor:
    async def ingest_url(self, url: str) -> str:
        from scraper.browser import fetch_text
        text_content = await fetch_text(url)
        return await self.ingest_text(
            text=text_content[:8000],
            source_type="url",
            source_url=url,
        )

    async def ingest_text(
        self,
        text: str,
        source_type: str = "note",
        source_url: str | None = None,
        title: str | None = None,
        author: str | None = None,
    ) -> str:
        raw = await generate(SUMMARISE_PROMPT.format(text=text[:8000]))

        parsed_title = title
        summary = ""
        tags: list[str] = []

        for line in raw.splitlines():
            if line.startswith("TITLE:") and not parsed_title:
                parsed_title = line.replace("TITLE:", "").strip()
            elif line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
            elif line.startswith("TAGS:"):
                tags = [t.strip() for t in line.replace("TAGS:", "").split(",")]

        parsed_title = parsed_title or "Untitled"
        embedding = await embed(f"{parsed_title}\n{summary}\n{text[:1000]}")
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    INSERT INTO knowledge_items
                        (title, content, summary, source_type, source_url, author, tags, embedding)
                    VALUES
                        (:title, :content, :summary, :source_type, :source_url, :author, :tags, :embedding::vector)
                    RETURNING id
                """),
                {
                    "title": parsed_title,
                    "content": text,
                    "summary": summary,
                    "source_type": source_type,
                    "source_url": source_url,
                    "author": author,
                    "tags": tags,
                    "embedding": embedding_str,
                },
            )
            await db.commit()
            return str(result.first()[0])
