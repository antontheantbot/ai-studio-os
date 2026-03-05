from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
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
    Retrieves context from knowledge base, opportunities, collectors, and institutions.
    """
    today = date.today().strftime("%B %d, %Y")
    context_parts = []
    all_sources = []

    # Knowledge base
    knowledge = await vector_search(
        db, "knowledge_items", req.message, limit=3,
        return_cols="title, content"
    )
    if knowledge:
        block = "KNOWLEDGE BASE:\n" + "\n".join(
            f"- {k['title']}: {k['content'][:400]}" for k in knowledge
        )
        context_parts.append(block)
        all_sources.extend(k["title"] for k in knowledge)

    # Opportunities (upcoming only)
    opps = await vector_search(
        db, "opportunities", req.message, limit=3,
        return_cols="title, category, deadline, description, url"
    )
    if opps:
        block = "OPPORTUNITIES IN DATABASE:\n" + "\n".join(
            f"- {o['title']} ({o['category']}), deadline: {o['deadline']}, url: {o['url']}"
            for o in opps
        )
        context_parts.append(block)
        all_sources.extend(o["title"] for o in opps)

    # Collectors
    collectors = await vector_search(
        db, "collectors", req.message, limit=3,
        return_cols="name, interests, country, location"
    )
    if collectors:
        block = "COLLECTORS IN DATABASE:\n" + "\n".join(
            f"- {c['name']} ({c['location']}, {c['country']}): {c['interests']}"
            for c in collectors
        )
        context_parts.append(block)
        all_sources.extend(c["name"] for c in collectors)

    # Institutions
    institutions = await vector_search(
        db, "institutions", req.message, limit=3,
        return_cols="name, city, country, type, focus_areas"
    )
    if institutions:
        block = "INSTITUTIONS IN DATABASE:\n" + "\n".join(
            f"- {i['name']} ({i['city']}, {i['country']}): {i['focus_areas']}"
            for i in institutions
        )
        context_parts.append(block)
        all_sources.extend(i["name"] for i in institutions)

    context_block = ("\n\n" + "\n\n".join(context_parts)) if context_parts else ""

    system = f"""You are the AI assistant for a digital artist's studio OS. Today is {today}.

You have direct access to the studio's live database, which contains:
- Opportunities (open calls, residencies, commissions, festivals)
- Collectors and their interests
- Curators and institutions
- Press coverage and artists
- Knowledge base and templates

When answering, draw on the database context provided below. Do not say you lack access to data — you have it.
Be specific, concise, and actionable.{context_block}"""

    messages = req.history + [{"role": "user", "content": req.message}]
    response = await llm_chat(messages, system=system)

    return {
        "response": response,
        "sources": all_sources,
    }
