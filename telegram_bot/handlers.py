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
        "👥 *Contacts*\n"
        "/contacts — all contacts (search across all categories)\n"
        "/curators — curators\n"
        "/journalists — press contacts & writers\n"
        "/institutions — museums, galleries, foundations\n"
        "/collectors — art collectors\n"
        "/corporations — companies, brands, sponsors\n\n"
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


# ── Contacts (unified) ────────────────────────────────────────────────────────

async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"q": query} if query else {}
        curators     = await _api_get("/curators/",     params)
        journalists  = await _api_get("/journalists/",  params)
        institutions = await _api_get("/institutions/", params)
        collectors   = await _api_get("/collectors/",   params)
        corporations = await _api_get("/corporations/", params)

        sections = [
            ("Curators",     curators),
            ("Journalists",  journalists),
            ("Institutions", institutions),
            ("Collectors",   collectors),
            ("Corporations", corporations),
        ]
        lines = []
        for label, items in sections:
            if items:
                lines.append(f"*{label} ({len(items)})*")
                for c in items[:3]:
                    name = c.get("name", "")
                    role = c.get("role") or c.get("type") or ""
                    org  = c.get("institution") or c.get("organization") or c.get("contact_name") or ""
                    email = c.get("email") or c.get("contact_email") or ""
                    detail = " · ".join(x for x in [role, org] if x)
                    line = f"• *{name}*" + (f" — {detail}" if detail else "")
                    if email:
                        line += f"\n  {email}"
                    lines.append(line)
                if len(items) > 3:
                    lines.append(f"  _...and {len(items)-3} more_")
        if not lines:
            await update.message.reply_text("No contacts found.")
            return
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def institutions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"q": query} if query else {}
        items = await _api_get("/institutions/", params)
        if not items:
            await update.message.reply_text("No institutions found.")
            return
        lines = []
        for i in items[:8]:
            line = f"*{i['name']}*"
            loc = ", ".join(x for x in [i.get("city"), i.get("country")] if x)
            if loc:
                line += f" — {loc}"
            if i.get("type"):
                line += f"\n_{i['type']}_"
            if i.get("website"):
                line += f"\n{i['website']}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def corporations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"q": query} if query else {}
        items = await _api_get("/corporations/", params)
        if not items:
            await update.message.reply_text("No corporations found.")
            return
        lines = []
        for c in items[:8]:
            line = f"*{c['name']}*"
            loc = ", ".join(x for x in [c.get("city"), c.get("country")] if x)
            if loc:
                line += f" — {loc}"
            if c.get("contact_name"):
                line += f"\n_{c['contact_name']}"
                if c.get("contact_role"):
                    line += f", {c['contact_role']}"
                line += "_"
            if c.get("email"):
                line += f"\n{c['email']}"
            lines.append(line)
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
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

# Keyword → API endpoint mapping. Extend this dict as new sections are added.
_SECTION_ROUTES = {
    ("curator", "curators"):                        "/curators/",
    ("journalist", "journalists", "press", "media"): "/journalists/",
    ("institution", "institutions", "museum", "gallery"): "/institutions/",
    ("collector", "collectors"):                    "/collectors/",
    ("corporation", "corporations", "company", "brand", "sponsor"): "/corporations/",
    ("opportunity", "opportunities", "open call"):  "/opportunities/",
    ("grant", "grants", "funding"):                 "/opportunities/",
    ("contest", "contests", "prize", "award"):      "/opportunities/",
}


def _detect_section(text: str) -> tuple[str, str] | None:
    """Return (endpoint, label) if the message matches a known section."""
    lower = text.lower()
    for keywords, endpoint in _SECTION_ROUTES.items():
        if any(kw in lower for kw in keywords):
            return endpoint, keywords[0]
    return None


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    history = _history.get(user_id, [])
    await update.message.chat.send_action("typing")

    # Extract search query — anything after "find"/"search"/"show me" etc.
    import re
    q_match = re.search(r'(?:find|search|show|list|get)\s+(?:me\s+)?(.+)', text, re.I)
    query = q_match.group(1).strip() if q_match else None

    # Auto-route to the right section if recognised
    route = _detect_section(text)
    if route:
        endpoint, label = route
        try:
            params = {"q": query} if query else {}
            if "opportunities" in endpoint:
                params["upcoming_only"] = "true"
                params["limit"] = "20"
            items = await _api_get(endpoint, params)
            if items:
                lines = [f"*{label.title()}s found: {len(items)}*"]
                for item in items[:6]:
                    name = item.get("name") or item.get("title", "")
                    detail = " · ".join(x for x in [
                        item.get("role") or item.get("type") or item.get("category") or "",
                        item.get("institution") or item.get("organization") or item.get("contact_name") or item.get("organizer") or "",
                    ] if x)
                    email = item.get("email") or item.get("contact_email") or ""
                    line = f"• *{name}*" + (f" — {detail}" if detail else "")
                    if email:
                        line += f"\n  {email}"
                    lines.append(line)
                if len(items) > 6:
                    lines.append(f"_...and {len(items)-6} more. Use the app to see all._")
                history.append({"role": "user", "content": text})
                history.append({"role": "assistant", "content": "\n".join(lines)})
                _history[user_id] = history[-20:]
                await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
                return
        except Exception:
            pass  # fall through to chat

    # Default: send to AI chat endpoint
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
