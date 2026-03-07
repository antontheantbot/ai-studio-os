from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.services.search import vector_search
from app.services.embeddings import embed
import sqlalchemy as sa

router = APIRouter()


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []


@router.get("/search")
async def search_knowledge(
    q: str = Query(..., description="Semantic search query"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await vector_search(db, "knowledge_items", q, limit=limit)


@router.post("/notes")
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db)):
    """Save a note and embed it for semantic search."""
    embedding = await embed(f"{note.title}\n{note.content}")
    embedding_str = f"[{','.join(str(x) for x in embedding)}]"

    result = await db.execute(
        sa.text("""
            INSERT INTO knowledge_items (title, content, tags, embedding, source_type)
            VALUES (:title, :content, :tags, CAST(:embedding AS vector), 'note')
            RETURNING id, title, created_at
        """),
        {
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "embedding": embedding_str,
        },
    )
    return dict(result.first()._mapping)


@router.get("/")
async def list_knowledge(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.text("SELECT id, title, content, summary, tags, source_type, created_at FROM knowledge_items ORDER BY created_at DESC LIMIT :limit"),
        {"limit": limit},
    )
    return [dict(r._mapping) for r in result]


@router.delete("/{item_id}")
async def delete_knowledge(item_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        sa.text("DELETE FROM knowledge_items WHERE id = :id"),
        {"id": item_id},
    )
    await db.commit()
    return {"deleted": item_id}


@router.post("/scan")
async def scan(background_tasks: BackgroundTasks):
    """Trigger a live web scan for new knowledge using Tavily."""
    from app.agents.web_ingestor import scan_knowledge
    background_tasks.add_task(scan_knowledge)
    return {"status": "scanning", "category": "knowledge", "message": "Web scan started"}
