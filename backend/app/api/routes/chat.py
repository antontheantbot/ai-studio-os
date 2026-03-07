import asyncio
from datetime import date
from fastapi import APIRouter
from sqlalchemy import text
from pydantic import BaseModel
from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import chat as llm_chat

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []


async def _fetch_vector(table: str, embedding_str: str, limit: int, return_cols: str) -> list[dict]:
    """Vector similarity search with its own DB session."""
    sql = text(f"""
        SELECT {return_cols},
               1 - (embedding <=> CAST(:emb AS vector)) AS similarity
        FROM {table}
        ORDER BY embedding <=> CAST(:emb AS vector)
        LIMIT :limit
    """)
    async with AsyncSessionLocal() as db:
        result = await db.execute(sql, {"emb": embedding_str, "limit": limit})
        return [dict(r._mapping) for r in result]


async def _fetch_journalists(message: str) -> list[dict]:
    """ILIKE search on journalists (no embedding column) with its own session."""
    words = [w for w in message.split() if len(w) > 3]
    pattern = f"%{words[0]}%" if words else "%%"
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                text("""
                    SELECT name, publications, beats, email, location
                    FROM journalists
                    WHERE name ILIKE :q OR bio ILIKE :q
                       OR publications::text ILIKE :q OR beats::text ILIKE :q
                    ORDER BY name LIMIT 3
                """),
                {"q": pattern},
            )
            rows = [dict(r._mapping) for r in result]
            if not rows:
                result = await db.execute(
                    text("SELECT name, publications, beats, email, location FROM journalists ORDER BY created_at DESC LIMIT 3")
                )
                rows = [dict(r._mapping) for r in result]
            return rows
        except Exception:
            return []


async def _fetch_brief() -> dict | None:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                text("SELECT title, week_of, brief, top_mediums FROM market_briefs ORDER BY week_of DESC LIMIT 1")
            )
            row = result.first()
            return dict(row._mapping) if row else None
        except Exception:
            return None


async def _fetch_daily() -> dict | None:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                text("SELECT goal_name, content FROM daily_actions ORDER BY date DESC LIMIT 1")
            )
            row = result.first()
            return dict(row._mapping) if row else None
        except Exception:
            return None


@router.post("/")
async def chat(req: ChatMessage):
    """
    RAG-powered chat endpoint.
    Computes the query embedding once, then fetches all context concurrently.
    """
    today = date.today().strftime("%B %d, %Y")

    # Compute the query embedding once — reused by all vector searches
    query_embedding = await embed(req.message)
    embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

    # Run all DB lookups concurrently, each with its own session
    (
        knowledge,
        opps,
        collectors,
        curators,
        institutions,
        press,
        journalists,
        brief_row,
        daily_row,
    ) = await asyncio.gather(
        _fetch_vector("knowledge_items", embedding_str, 3, "title, content"),
        _fetch_vector("opportunities", embedding_str, 4, "title, category, deadline, description, url, award"),
        _fetch_vector("collectors", embedding_str, 3, "name, interests, country, location"),
        _fetch_vector("curators", embedding_str, 3, "name, institution, role, focus_areas, location"),
        _fetch_vector("institutions", embedding_str, 2, "name, city, country, type, focus_areas"),
        _fetch_vector("press_items", embedding_str, 2, "title, summary, source, author"),
        _fetch_journalists(req.message),
        _fetch_brief(),
        _fetch_daily(),
    )

    context_parts = []
    all_sources = []

    if knowledge:
        context_parts.append("KNOWLEDGE BASE:\n" + "\n".join(
            f"- {k['title']}: {k['content'][:400]}" for k in knowledge
        ))
        all_sources.extend(k["title"] for k in knowledge)

    if opps:
        context_parts.append("OPPORTUNITIES IN DATABASE:\n" + "\n".join(
            f"- {o['title']} ({o['category']}), deadline: {o['deadline']}, award: {o.get('award')}, url: {o['url']}"
            for o in opps
        ))
        all_sources.extend(o["title"] for o in opps)

    if journalists:
        context_parts.append("JOURNALISTS IN DATABASE:\n" + "\n".join(
            f"- {j['name']} ({j.get('location', '')}): writes for {j.get('publications', [])}, beats: {j.get('beats', [])}, email: {j.get('email', 'n/a')}"
            for j in journalists
        ))
        all_sources.extend(j["name"] for j in journalists)

    if collectors:
        context_parts.append("COLLECTORS IN DATABASE:\n" + "\n".join(
            f"- {c['name']} ({c['location']}, {c['country']}): {c['interests']}"
            for c in collectors
        ))
        all_sources.extend(c["name"] for c in collectors)

    if curators:
        context_parts.append("CURATORS IN DATABASE:\n" + "\n".join(
            f"- {c['name']}, {c.get('role', '')} at {c.get('institution', '')} ({c.get('location', '')}): {c.get('focus_areas', [])}"
            for c in curators
        ))
        all_sources.extend(c["name"] for c in curators)

    if institutions:
        context_parts.append("INSTITUTIONS IN DATABASE:\n" + "\n".join(
            f"- {i['name']} ({i['city']}, {i['country']}): {i['focus_areas']}"
            for i in institutions
        ))
        all_sources.extend(i["name"] for i in institutions)

    if press:
        context_parts.append("RECENT PRESS:\n" + "\n".join(
            f"- {p['title']} ({p['source']}, by {p.get('author', 'unknown')}): {p.get('summary', '')[:200]}"
            for p in press
        ))

    if brief_row:
        b = brief_row
        context_parts.append(
            f"LATEST MARKET BRIEF ({b['week_of']}):\n{b['title']}\n{(b.get('brief') or '')[:400]}"
        )

    if daily_row:
        d = daily_row
        context_parts.append(
            f"TODAY'S DAILY ACTION (Goal: {d['goal_name']}):\n{(d.get('content') or '')[:400]}"
        )

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
