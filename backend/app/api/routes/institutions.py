from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed
from pydantic import BaseModel

router = APIRouter()


class InstitutionCreate(BaseModel):
    name: str
    city: str | None = None
    country: str | None = None
    type: str | None = None
    website: str | None = None
    focus_areas: list[str] = []
    annual_budget: str | None = None
    digital_art_program: bool = False
    notes: str | None = None


@router.get("/")
async def list_institutions(
    q: str | None = Query(None),
    digital_only: bool = Query(False),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await vector_search(db, "institutions", q, limit=limit)
    where = "WHERE digital_art_program = TRUE" if digital_only else ""
    result = await db.execute(
        sa.text(f"SELECT * FROM institutions {where} ORDER BY name LIMIT :limit"),
        {"limit": limit},
    )
    return [dict(r._mapping) for r in result]


@router.get("/{institution_id}")
async def get_institution(institution_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        sa.text("SELECT * FROM institutions WHERE id = :id"),
        {"id": institution_id},
    )
    row = result.first()
    return dict(row._mapping) if row else {"error": "not found"}


@router.post("/")
async def create_institution(inst: InstitutionCreate, db: AsyncSession = Depends(get_db)):
    embed_text = f"{inst.name} {inst.type or ''} {' '.join(inst.focus_areas)} {inst.notes or ''}"
    embedding = await embed(embed_text)
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO institutions
                (name, city, country, type, website, focus_areas,
                 annual_budget, digital_art_program, notes, embedding)
            VALUES
                (:name, :city, :country, :type, :website, :focus_areas,
                 :annual_budget, :digital_art_program, :notes, :embedding::vector)
            RETURNING id, name, created_at
        """),
        {
            "name": inst.name,
            "city": inst.city,
            "country": inst.country,
            "type": inst.type,
            "website": inst.website,
            "focus_areas": inst.focus_areas,
            "annual_budget": inst.annual_budget,
            "digital_art_program": inst.digital_art_program,
            "notes": inst.notes,
            "embedding": embedding_str,
        },
    )
    await db.commit()
    return dict(result.first()._mapping)
