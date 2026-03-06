"""
Telegram command and message handlers.
All intelligence comes from the FastAPI backend.
"""
import os
import httpx
from telegram import Update
from telegram.ext import ContextTypes

API_BASE = os.getenv("API_BASE_URL", "http://api:8000/api/v1")

# Per-user conversation history (in-memory; reset on bot restart)
_history: dict[int, list[dict]] = {}


def _truncate(text: str, limit: int = 200) -> str:
    return text[:limit] + "..." if len(text) > limit else text


async def _api_get(path: str, params: dict = None):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{API_BASE}{path}", params=params or {})
        resp.raise_for_status()
        return resp.json()


async def _api_post(path: str, json: dict = None):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{API_BASE}{path}", json=json or {})
        resp.raise_for_status()
        return resp.json()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*AI Studio OS*\n\n"
        "Your art career assistant. Commands:\n\n"
        "📋 *Opportunities & Grants*\n"
        "/opportunities — open calls, residencies, commissions\n"
        "/grants — funding opportunities\n"
        "/contests — art competitions & prizes\n\n"
        "👥 *People & Contacts*\n"
        "/journalists — press contacts & writers\n"
        "/collectors — art collectors\n"
        "/curators — curators\n\n"
        "📊 *Market Intelligence*\n"
        "/brief — latest art market brief\n"
        "/colors — trending colors & sizes\n\n"
        "🎯 *Daily Action*\n"
        "/daily — today's career action\n\n"
        "🔍 *Search & Scan*\n"
        "/search <query> — search knowledge base\n"
        "/scan — trigger full web scan\n\n"
        "Or just chat naturally.",
        parse_mode="Markdown",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_handler(update, context)


# ── Opportunities ─────────────────────────────────────────────────────────────

async def opportunities_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"upcoming_only": "true", "limit": "50"}
        if query:
            params["q"] = query
        items = await _api_get("/opportunities/", params)
        # exclude grants and contests
        items = [o for o in items if o.get("category") not in ("grant", "contest")][:8]
        if not items:
            await update.message.reply_text("No opportunities found.")
            return
        lines = []
        for o in items:
            line = f"*{o['title']}*"
            meta = [o.get("category", "")]
            if o.get("deadline"):
                meta.append(f"Deadline: {o['deadline']}")
            if o.get("award"):
                meta.append(f"Award: {o['award']}")
            line += f"\n_{', '.join(m for m in meta if m)}_"
            if o.get("url"):
                line += f"\n{o['url']}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def grants_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        items = await _api_get("/opportunities/", {"upcoming_only": "true", "limit": "100"})
        grants = [o for o in items if o.get("category") == "grant"][:8]
        if not grants:
            await update.message.reply_text("No grants found. Try /scan to update.")
            return
        lines = []
        for o in grants:
            line = f"*{o['title']}*"
            if o.get("deadline"):
                line += f"\n_Deadline: {o['deadline']}_"
            if o.get("award"):
                line += f"\n_Award: {o['award']}_"
            if o.get("url"):
                line += f"\n{o['url']}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def contests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        items = await _api_get("/opportunities/", {"upcoming_only": "true", "limit": "100"})
        contests = [o for o in items if o.get("category") == "contest"][:8]
        if not contests:
            await update.message.reply_text("No contests found. Try /scan to update.")
            return
        lines = []
        for o in contests:
            line = f"*{o['title']}*"
            if o.get("award"):
                line += f"\n_Prize: {o['award']}_"
            if o.get("deadline"):
                line += f"\n_Deadline: {o['deadline']}_"
            if o.get("url"):
                line += f"\n{o['url']}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ── People ────────────────────────────────────────────────────────────────────

async def journalists_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {}
        if query:
            params["q"] = query
        items = await _api_get("/journalists/", params)
        if not items:
            await update.message.reply_text("No journalists found. Try /scan to update.")
            return
        lines = []
        for j in items[:8]:
            line = f"*{j['name']}*"
            if j.get("location"):
                line += f" — {j['location']}"
            if j.get("publications"):
                line += f"\n_{', '.join(j['publications'][:3])}_"
            if j.get("beats"):
                line += f"\nBeats: {', '.join(j['beats'][:3])}"
            if j.get("email"):
                line += f"\n{j['email']}"
            elif j.get("social_links"):
                socials = [v for v in j["social_links"].values() if v]
                if socials:
                    line += f"\n{socials[0]}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def collectors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {}
        if query:
            params["q"] = query
        items = await _api_get("/collectors/", params)
        if not items:
            await update.message.reply_text("No collectors found.")
            return
        lines = []
        for c in items[:8]:
            line = f"*{c['name']}*"
            if c.get("location"):
                line += f" — {c['location']}"
            if c.get("interests"):
                line += f"\n_Interests: {', '.join(c['interests'][:3])}_"
            if c.get("bio"):
                line += f"\n{_truncate(c['bio'], 150)}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def curators_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {}
        if query:
            params["q"] = query
        items = await _api_get("/curators/", params)
        if not items:
            await update.message.reply_text("No curators found.")
            return
        lines = []
        for c in items[:8]:
            line = f"*{c['name']}*"
            if c.get("institution"):
                line += f" — {c['institution']}"
            if c.get("role"):
                line += f"\n_{c['role']}_"
            if c.get("focus_areas"):
                line += f"\nFocus: {', '.join(c['focus_areas'][:3])}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ── Market Intelligence ───────────────────────────────────────────────────────

async def brief_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        brief = await _api_get("/briefs/latest")
        if not brief or not brief.get("brief"):
            await update.message.reply_text("No market brief yet. Use /scan to generate one.")
            return
        text = f"*{brief['title']}*\n_Week of {brief['week_of']}_\n\n"
        if brief.get("top_mediums"):
            text += f"Trending: {', '.join(brief['top_mediums'][:4])}\n\n"
        text += _truncate(brief["brief"], 800)
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def colors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        data = await _api_get("/briefs/color-trends/latest")
        if not data:
            await update.message.reply_text("No color trend data yet.")
            return
        lines = [f"*Color & Size Trends — Week of {data['week_of']}*"]
        if data.get("summary"):
            lines.append(f"\n{_truncate(data['summary'], 300)}")
        if data.get("popular_colors"):
            lines.append("\n*Popular Colors:*")
            for c in data["popular_colors"][:5]:
                lines.append(f"• {c['name']} `{c['hex']}` [{c['trend']}]")
        if data.get("popular_sizes"):
            lines.append("\n*Popular Sizes:*")
            for s in data["popular_sizes"][:5]:
                lines.append(f"• {s['label']} {s['dimensions']} · {s['medium']} [{s['trend']}]")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ── Daily Action ──────────────────────────────────────────────────────────────

async def daily_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        action = await _api_get("/daily/today")
        if not action or not action.get("content"):
            await update.message.reply_text("Generating today's action...")
            action = await _api_post("/daily/generate")
        text = f"*Daily Action — {action['date']}*\n"
        if action.get("goal_name"):
            text += f"_Goal: {action['goal_name']}_\n\n"
        text += action["content"]
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ── Search & Scan ─────────────────────────────────────────────────────────────

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <your query>")
        return
    await update.message.chat.send_action("typing")
    try:
        items = await _api_get("/knowledge/search", {"q": query, "limit": "5"})
        if not items:
            await update.message.reply_text("No results found.")
            return
        lines = [f"*{i+1}. {item['title']}*\n{_truncate(item.get('summary', ''), 200)}" for i, item in enumerate(items)]
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Search failed: {e}")


async def scan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Triggering full web scan... check back in ~5 minutes.")
    try:
        await _api_post("/scan/all")
    except Exception as e:
        await update.message.reply_text(f"Failed to trigger scan: {e}")


# ── Chat (fallback) ───────────────────────────────────────────────────────────

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    history = _history.get(user_id, [])
    await update.message.chat.send_action("typing")
    try:
        data = await _api_post("/chat/", {"message": text, "history": history[-10:]})
        response_text = data["response"]
        sources = data.get("sources", [])
        if sources:
            response_text += f"\n\n_Sources: {', '.join(sources[:3])}_"
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": data["response"]})
        _history[user_id] = history[-20:]
        await update.message.reply_text(response_text, parse_mode="Markdown")
    except httpx.HTTPError as e:
        await update.message.reply_text(f"API error: {e}")
    except Exception as e:
        await update.message.reply_text(f"Something went wrong: {e}")
