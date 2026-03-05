from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.services.search import vector_search

router = APIRouter()


@router.get("/")
async def list_artists(
    q: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all artists or search semantically."""
    if q:
        return await vector_search(db, "artists", q, limit)

    result = await db.execute(
        text("SELECT * FROM artists ORDER BY created_at DESC LIMIT :limit"),
        {"limit": limit}
    )
    return [dict(row._mapping) for row in result.fetchall()]


@router.get("/{artist_id}")
async def get_artist(artist_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single artist with their relationships."""
    result = await db.execute(
        text("SELECT * FROM artists WHERE id = :id"),
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
