from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed
from pydantic import BaseModel

router = APIRouter()


class ArtworkCreate(BaseModel):
    title: str
    artist_id: str | None = None
    year: int | None = None
    medium: str | None = None
    dimensions: str | None = None
    description: str | None = None
    image_urls: list[str] = []
    collection: str | None = None
    exhibition_history: list[str] = []


@router.get("/")
async def list_artworks(
    q: str | None = Query(None),
    artist_id: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "artworks", q, limit=limit)
    if artist_id:
        result = await db.execute(
            sa.text("SELECT * FROM artworks WHERE artist_id = :artist_id ORDER BY year DESC LIMIT :limit"),
            {"artist_id": artist_id, "limit": limit},
        )
    else:
        result = await db.execute(
            sa.text("SELECT * FROM artworks ORDER BY created_at DESC LIMIT :limit"),
            {"limit": limit},
        )
    return [dict(r._mapping) for r in result]


@router.get("/:artwork_id")
async def get_artwork(artwork_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        sa.text("SELECT * FROM artworks WHERE id = :id"),
        {"id": artwork_id},
    )
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}


@router.post("/")
async def create_artwork(artwork: ArtworkCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{artwork.title} {artwork.medium or ''} {artwork.description or ''}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO artworks
                (title, artist_id, year, medium, dimensions, description,
                 image_urls, collection, exhibition_history, embedding)
            VALUES
                (:title, :artist_id, :year, :medium, :dimensions, :description,
                 :image_urls, :collection, :exhibition_history, :embedding::vector)
            RETURNING id, title, created_at
        """),
        {
            "title": artwork.title,
            "artist_id": artwork.artist_id,
            "year": artwork.year,
            "medium": artwork.medium,
            "dimensions": artwork.dimensions,
            "description": artwork.description,
            "image_urls": artwork.image_urls,
            "collection": artwork.collection,
            "exhibition_history": artwork.exhibition_history,
            "embedding": embedding_str,
        },
    )
    await db.commit()
    return dict(result.first()._mapping)
