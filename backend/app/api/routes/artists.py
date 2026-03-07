from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed

router = APIRouter()

_COLS = "id, name, country, city, bio, medium, website, instagram, represented_by, created_at, updated_at"


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
    q: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all artists or search semantically."""
    if q:
        return await vector_search(db, "artists", q, limit, return_cols=_COLS)

    result = await db.execute(
        text(f"SELECT {_COLS} FROM artists ORDER BY created_at DESC LIMIT :limit"),
        {"limit": limit}
    )
    return [dict(row._mapping) for row in result.fetchall()]


@router.post("/")
async def create_artist(a: ArtistCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{a.name} {a.bio or ''} {' '.join(a.medium)}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"
    result = await db.execute(
        text("""
            INSERT INTO artists (name, country, city, bio, medium, website, instagram, represented_by, embedding)
            VALUES (:name, :country, :city, :bio, :medium, :website, :instagram, :represented_by, CAST(:embedding AS vector))
            ON CONFLICT (name) DO NOTHING
            RETURNING id, name, created_at
        """),
        {
            "name": a.name, "country": a.country, "city": a.city, "bio": a.bio,
            "medium": a.medium, "website": a.website, "instagram": a.instagram,
            "represented_by": a.represented_by, "embedding": embedding_str,
        },
    )
    await db.commit()
    row = result.first()
    return dict(row._mapping) if row else {"status": "already exists"}


@router.get("/{artist_id}")
async def get_artist(artist_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single artist with their relationships."""
    result = await db.execute(
        text(f"SELECT {_COLS} FROM artists WHERE id = :id"),
        {"id": artist_id}
    )
    artist = result.fetchone()
    if not artist:
        return {"error": "Artist not found"}

    # Get collector relationships
    collectors = await db.execute(
        text("""
            SELECT c.name, car.relationship_type, car.confidence
            FROM collector_artist_relations car
            JOIN collectors c ON c.id = car.collector_id
            WHERE car.artist_id = :id
        """),
        {"id": artist_id}
    )

    # Get institution relationships
    institutions = await db.execute(
        text("""
            SELECT i.name, air.relationship_type, air.year, air.exhibition_title
            FROM artist_institution_relations air
            JOIN institutions i ON i.id = air.institution_id
            WHERE air.artist_id = :id
        """),
        {"id": artist_id}
    )

    return {
        **dict(artist._mapping),
        "collectors": [dict(r._mapping) for r in collectors.fetchall()],
        "institutions": [dict(r._mapping) for r in institutions.fetchall()],
    }
