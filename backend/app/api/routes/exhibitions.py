from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed
from pydantic import BaseModel

router = APIRouter()


class ExhibitionCreate(BaseModel):
    title: str
    institution_id: str | None = None
    curator_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    type: str | None = None
    artists: list[str] = []
    description: str | None = None
    url: str | None = None


@router.get("/")
async def list_exhibitions(
    q: str | None = Query(None),
    institution_id: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "exhibitions", q, limit=limit)
    if institution_id:
        result = await db.execute(
            sa.text("SELECT * FROM exhibitions WHERE institution_id = :iid ORDER BY start_date DESC LIMIT :limit"),
            {"iid": institution_id, "limit": limit},
        )
    else:
        result = await db.execute(
            sa.text("SELECT * FROM exhibitions ORDER BY start_date DESC LIMIT :limit"),
            {"limit": limit},
        )
    return [dict(r._mapping) for r in result]


@router.get("/{exhibition_id}")
async def get_exhibition(exhibition_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        sa.text("SELECT * FROM exhibitions WHERE id = :id"),
        {"id": exhibition_id},
    )
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}


@router.post("/")
async def create_exhibition(ex: ExhibitionCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{ex.title} {ex.type or ''} {' '.join(ex.artists)} {ex.description or ''}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO exhibitions
                (title, institution_id, curator_id, start_date, end_date,
                 type, artists, description, url, embedding)
            VALUES
                (:title, :institution_id, :curator_id, :start_date, :end_date,
                 :type, :artists, :description, :url, :embedding::vector)
            RETURNING id, title, created_at
        """),
        {
            "title": ex.title,
            "institution_id": ex.institution_id,
            "curator_id": ex.curator_id,
            "start_date": ex.start_date,
            "end_date": ex.end_date,
            "type": ex.type,
            "artists": ex.artists,
            "description": ex.description,
            "url": ex.url,
            "embedding": embedding_str,
        },
    )
    await db.commit()
    return dict(result.first()._mapping)
