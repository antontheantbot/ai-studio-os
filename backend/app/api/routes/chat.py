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
    Retrieves context from all sections: knowledge, opportunities, collectors,
    curators, institutions, journalists, press, and market briefs.
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
        db, "opportunities", req.message, limit=4,
        return_cols="title, category, deadline, description, url, award"
    )
    if opps:
        block = "OPPORTUNITIES IN DATABASE:\n" + "\n".join(
            f"- {o['title']} ({o['category']}), deadline: {o['deadline']}, award: {o.get('award')}, url: {o['url']}"
            for o in opps
        )
        context_parts.append(block)
        all_sources.extend(o["title"] for o in opps)

    # Journalists
    journalists = await vector_search(
        db, "journalists", req.message, limit=3,
        return_cols="name, publications, beats, email, location"
    )
    if journalists:
        block = "JOURNALISTS IN DATABASE:\n" + "\n".join(
            f"- {j['name']} ({j.get('location', '')}): writes for {j.get('publications', [])}, beats: {j.get('beats', [])}, email: {j.get('email', 'n/a')}"
            for j in journalists
        )
        context_parts.append(block)
        all_sources.extend(j["name"] for j in journalists)

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

    # Curators
    curators = await vector_search(
        db, "curators", req.message, limit=3,
        return_cols="name, institution, role, focus_areas, location"
    )
    if curators:
        block = "CURATORS IN DATABASE:\n" + "\n".join(
            f"- {c['name']}, {c.get('role', '')} at {c.get('institution', '')} ({c.get('location', '')}): {c.get('focus_areas', [])}"
            for c in curators
        )
        context_parts.append(block)
        all_sources.extend(c["name"] for c in curators)

    # Institutions
    institutions = await vector_search(
        db, "institutions", req.message, limit=2,
        return_cols="name, city, country, type, focus_areas"
    )
    if institutions:
        block = "INSTITUTIONS IN DATABASE:\n" + "\n".join(
            f"- {i['name']} ({i['city']}, {i['country']}): {i['focus_areas']}"
            for i in institutions
        )
        context_parts.append(block)
        all_sources.extend(i["name"] for i in institutions)

    # Press items
    press = await vector_search(
        db, "press_items", req.message, limit=2,
        return_cols="title, summary, source, author"
    )
    if press:
        block = "RECENT PRESS:\n" + "\n".join(
            f"- {p['title']} ({p['source']}, by {p.get('author', 'unknown')}): {p.get('summary', '')[:200]}"
            for p in press
        )
        context_parts.append(block)

    # Latest market brief (always include a summary)
    try:
        brief_result = await db.execute(
            text("SELECT title, week_of, brief, top_mediums FROM market_briefs ORDER BY week_of DESC LIMIT 1")
        )
        brief_row = brief_result.first()
        if brief_row:
            b = dict(brief_row._mapping)
            context_parts.append(
                f"LATEST MARKET BRIEF ({b['week_of']}):\n{b['title']}\n{(b.get('brief') or '')[:400]}"
            )
    except Exception:
        pass

    # Today's daily action
    try:
        daily_result = await db.execute(
            text("SELECT goal_name, content FROM daily_actions ORDER BY date DESC LIMIT 1")
        )
        daily_row = daily_result.first()
        if daily_row:
            d = dict(daily_row._mapping)
            context_parts.append(
                f"TODAY'S DAILY ACTION (Goal: {d['goal_name']}):\n{(d.get('content') or '')[:400]}"
            )
    except Exception:
        pass

    context_block = ("\n\n" + "\n\n".join(context_parts)) if context_parts else ""

    system = f"""You are the AI assistant for Ryan Koopmans and Alice Wexell's art studio OS. Today is {today}.

You have direct access to the studio's live database, which includes:
- Opportunities: open calls, residencies, commissions, festivals, grants, contests
- Journalists: press contacts, writers covering art, culture, photography and architecture
- Collectors: art collectors and their interests
- Curators: curators and their focus areas
- Institutions: galleries, museums, foundations
- Press: recent coverage and articles
- Market intelligence: weekly art market briefs and color/size trends
- Daily action: today's recommended career action

When answering, draw on the database context below. Be specific, concise, and actionable. Do not say you lack access to data — you have it.{context_block}"""

    messages = req.history + [{"role": "user", "content": req.message}]
    response = await llm_chat(messages, system=system)

    return {
        "response": response,
        "sources": all_sources,
    }
