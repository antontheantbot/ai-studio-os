from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from pydantic import BaseModel

from app.db.session import get_db
from app.services.search import vector_search, keyword_search
from app.services.embeddings import embed

router = APIRouter()

_COLS = "id, title, content, summary, source, author, url, published_at, category, tags, mentioned_artists, created_at, updated_at"


class PressCreate(BaseModel):
    title: str
    content: str | None = None
    summary: str | None = None
    source: str | None = None
    author: str | None = None
    url: str | None = None
    published_at: str | None = None
    category: str | None = None
    tags: list[str] = []
    mentioned_artists: list[str] = []


@router.get("/")
async def list_press(
    q: str | None = Query(None),
    mode: str = Query("semantic", regex="^(semantic|keyword)$"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q and mode == "semantic":
        return await vector_search(db, "press_items", q, limit=limit, return_cols=_COLS)
    if q and mode == "keyword":
        return await keyword_search(db, "press_items", q, search_col="title || ' ' || COALESCE(content, '')", limit=limit, return_cols=_COLS)
    result = await db.execute(sa.text(f"SELECT {_COLS} FROM press_items ORDER BY published_at DESC LIMIT :limit"), {"limit": limit})
    return [dict(r._mapping) for r in result]


@router.post("/")
async def create_press(p: PressCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{p.title} {p.summary or p.content or ''}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO press_items
                (title, content, summary, source, author, url, published_at,
                 category, tags, mentioned_artists, embedding)
            VALUES
                (:title, :content, :summary, :source, :author, :url, :published_at,
                 :category, :tags, :mentioned_artists, CAST(:embedding AS vector))
            ON CONFLICT (url) DO NOTHING
            RETURNING id, title, created_at
        """),
        {
            "title": p.title, "content": p.content, "summary": p.summary,
            "source": p.source, "author": p.author, "url": p.url,
            "published_at": datetime.fromisoformat(p.published_at.replace("Z", "+00:00")) if p.published_at else None, "category": p.category,
            "tags": p.tags, "mentioned_artists": p.mentioned_artists,
            "embedding": embedding_str,
        },
    )
    await db.commit()
    row = result.first()
    return dict(row._mapping) if row else {"status": "already exists"}


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for new press using Tavily."""
    from app.agents.web_ingestor import scan_press
    background_tasks.add_task(scan_press)
    return {"status": "scanning", "category": "press", "message": "Web scan started"}
