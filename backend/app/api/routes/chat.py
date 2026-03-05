from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.services.search import vector_search
from app.services.llm import chat as llm_chat

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/")
async def chat(req: ChatMessage, db: AsyncSession = Depends(get_db)):
    """
    RAG-powered chat endpoint.
    1. Embed the user query
    2. Retrieve relevant knowledge items
    3. Send context + query to Claude
    """
    # Retrieve context from knowledge base
    context_items = await vector_search(
        db, "knowledge_items", req.message, limit=5,
        return_cols="title, content"
    )

    context_block = ""
    if context_items:
        context_block = "\n\nRelevant knowledge from your studio database:\n"
        for item in context_items:
            context_block += f"\n--- {item['title']} ---\n{item['content'][:500]}\n"

    system = f"""You are the AI assistant for an artist's studio OS.
You help with research, finding opportunities, collector and curator intelligence,
press monitoring, and proposal writing.{context_block}
Answer based on the context above when relevant. Be concise and helpful."""

    messages = req.history + [{"role": "user", "content": req.message}]
    response = await llm_chat(messages, system=system)

    return {
        "response": response,
        "sources": [item["title"] for item in context_items],
    }
