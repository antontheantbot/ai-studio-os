from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed
from pydantic import BaseModel

router = APIRouter()


class ArtistCreate(BaseModel):
    name: str
    country: str | None = None
    city: str | None = None
    bio: str | None = None
    medium: list[str] = []
    website: str | None = None
    instagram: str | None = None
    represented_by: list[str] = []


@router.get("/")
async def list_artists(
    q: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "artists", q, limit=limit)
    result = await db.execute(
        sa.text("SELECT * FROM artists ORDER BY name LIMIT :limit"),
        {"limit": limit},
    )
    return [dict(r._mapping) for r in result]


@router.get("/:artist_id")
async def get_artist(artist_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        sa.text("SELECT * FROM artists WHERE id = :id"),
        {"id": artist_id},
    )
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}


@router.post("/")
async def create_artist(artist: ArtistCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{artist.name} {' '.join(artist.medium)} {artist.bio or ''}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO artists (name, country, city, bio, medium, website, instagram, represented_by, embedding)
            VALUES (:name, :country, :city, :bio, :medium, :website, :instagram, :represented_by, :embedding::vector)
            RETURNING id, name, created_at
        """),
        {
            "name": artist.name,
            "country": artist.country,
            "city": artist.city,
            "bio": artist.bio,
            "medium": artist.medium,
            "website": artist.website,
            "instagram": artist.instagram,
            "represented_by": artist.represented_by,
            "embedding": embedding_str,
        },
    )
    await db.commit()
    return dict(result.first()._mapping)
