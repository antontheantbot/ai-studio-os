"""
Telegram command and message handlers.
All intelligence comes from the FastAPI backend.
"""
import os
import re
import html
import httpx
from telegram import Update
from telegram.ext import ContextTypes

API_BASE = os.getenv("API_BASE_URL", "http://api:8000/api/v1")

# Per-user conversation history (in-memory; reset on bot restart)
_history: dict[int, list[dict]] = {}


def _h(text) -> str:
    """Escape a value for safe use in HTML Telegram messages."""
    return html.escape(str(text)) if text else ""


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


async def _send_html(update: Update, text: str, preview: bool = False):
    """Send an HTML-formatted message, splitting if over Telegram's 4096 char limit."""
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="HTML", disable_web_page_preview=not preview)


# ── Start / Help ──────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_html(update,
        "<b>AI Studio OS</b>\n\n"
        "Your art career assistant. Commands:\n\n"
        "📋 <b>Opportunities &amp; Grants</b>\n"
        "/opportunities — open calls, residencies, commissions\n"
        "/grants — funding opportunities\n"
        "/contests — art competitions &amp; prizes\n\n"
        "👥 <b>Contacts</b>\n"
        "/contacts — all contacts overview\n"
        "/curators — curators\n"
        "/journalists — press contacts &amp; writers\n"
        "/institutions — museums, galleries, foundations\n"
        "/collectors — art collectors\n"
        "/corporations — companies, brands, sponsors\n\n"
        "📊 <b>Market Intelligence</b>\n"
        "/brief — latest art market brief\n"
        "/colors — trending colors &amp; sizes\n\n"
        "🎯 <b>Daily Action</b>\n"
        "/daily — today's career action\n\n"
        "🔍 <b>Search &amp; Scan</b>\n"
        "/search &lt;query&gt; — search knowledge base\n"
        "/scan — trigger full web scan\n\n"
        "Or just chat naturally."
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
        items = [o for o in items if o.get("category") not in ("grant", "contest")][:8]
        if not items:
            await update.message.reply_text("No opportunities found.")
            return
        lines = []
        for o in items:
            line = f"<b>{_h(o['title'])}</b>"
            meta = [_h(o.get("category", ""))]
            if o.get("deadline"):
                meta.append(f"Deadline: {_h(o['deadline'])}")
            if o.get("award"):
                meta.append(f"Award: {_h(o['award'])}")
            line += f"\n<i>{', '.join(m for m in meta if m)}</i>"
            if o.get("url"):
                line += f"\n{_h(o['url'])}"
            lines.append(line)
        await _send_html(update, "\n\n".join(lines))
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
            line = f"<b>{_h(o['title'])}</b>"
            if o.get("deadline"):
                line += f"\n<i>Deadline: {_h(o['deadline'])}</i>"
            if o.get("award"):
                line += f"\n<i>Award: {_h(o['award'])}</i>"
            if o.get("url"):
                line += f"\n{_h(o['url'])}"
            lines.append(line)
        await _send_html(update, "\n\n".join(lines))
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
            line = f"<b>{_h(o['title'])}</b>"
            if o.get("award"):
                line += f"\n<i>Prize: {_h(o['award'])}</i>"
            if o.get("deadline"):
                line += f"\n<i>Deadline: {_h(o['deadline'])}</i>"
            if o.get("url"):
                line += f"\n{_h(o['url'])}"
            lines.append(line)
        await _send_html(update, "\n\n".join(lines))
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
        lines = [f"<b>Contacts{' matching &quot;' + _h(query) + '&quot;' if query else ''}</b>\n"]
        for label, items in sections:
            if items:
                lines.append(f"<b>{label} ({len(items)})</b>")
                for c in items[:3]:
                    name = _h(c.get("name", ""))
                    role = _h(c.get("role") or c.get("type") or "")
                    org  = _h(c.get("institution") or c.get("organization") or c.get("contact_name") or "")
                    email = _h(c.get("email") or c.get("contact_email") or "")
                    detail = " · ".join(x for x in [role, org] if x)
                    line = f"• <b>{name}</b>" + (f" — {detail}" if detail else "")
                    if email:
                        line += f"\n  {email}"
                    lines.append(line)
                if len(items) > 3:
                    lines.append(f"  <i>...and {len(items)-3} more</i>")
        if len(lines) == 1:
            await update.message.reply_text("No contacts found.")
            return
        await _send_html(update, "\n".join(lines))
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
        total = len(items)
        lines = [f"<b>Institutions ({total} total){' matching &quot;' + _h(query) + '&quot;' if query else ''}</b>\n"]
        for i in items[:8]:
            line = f"• <b>{_h(i['name'])}</b>"
            loc = ", ".join(x for x in [i.get("city"), i.get("country")] if x)
            if loc:
                line += f" — {_h(loc)}"
            if i.get("type"):
                line += f"\n  <i>{_h(i['type'])}</i>"
            if i.get("website"):
                line += f"\n  {_h(i['website'])}"
            lines.append(line)
        if total > 8:
            lines.append(f"\n<i>...and {total - 8} more. Use /institutions &lt;name&gt; to search.</i>")
        await _send_html(update, "\n".join(lines))
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
        total = len(items)
        lines = [f"<b>Corporations ({total} total){' matching &quot;' + _h(query) + '&quot;' if query else ''}</b>\n"]
        for c in items[:8]:
            line = f"• <b>{_h(c['name'])}</b>"
            loc = ", ".join(x for x in [c.get("city"), c.get("country")] if x)
            if loc:
                line += f" — {_h(loc)}"
            if c.get("contact_name"):
                role_str = _h(c['contact_name'])
                if c.get("contact_role"):
                    role_str += f", {_h(c['contact_role'])}"
                line += f"\n  <i>{role_str}</i>"
            if c.get("email"):
                line += f"\n  {_h(c['email'])}"
            lines.append(line)
        if total > 8:
            lines.append(f"\n<i>...and {total - 8} more. Use /corporations &lt;name&gt; to search.</i>")
        await _send_html(update, "\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ── People ────────────────────────────────────────────────────────────────────

async def journalists_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"q": query} if query else {}
        items = await _api_get("/journalists/", params)
        if not items:
            await update.message.reply_text("No journalists found. Try /scan to update.")
            return
        total = len(items)
        lines = [f"<b>Journalists ({total} total){' matching &quot;' + _h(query) + '&quot;' if query else ''}</b>\n"]
        for j in items[:8]:
            line = f"• <b>{_h(j['name'])}</b>"
            if j.get("location"):
                line += f" — {_h(j['location'])}"
            if j.get("publications"):
                line += f"\n  <i>{_h(', '.join(j['publications'][:3]))}</i>"
            if j.get("beats"):
                line += f"\n  Beats: {_h(', '.join(j['beats'][:3]))}"
            if j.get("email"):
                line += f"\n  {_h(j['email'])}"
            elif j.get("social_links"):
                socials = [v for v in j["social_links"].values() if v]
                if socials:
                    line += f"\n  {_h(socials[0])}"
            lines.append(line)
        if total > 8:
            lines.append(f"\n<i>...and {total - 8} more. Use /journalists &lt;name&gt; to search.</i>")
        await _send_html(update, "\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def collectors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"q": query} if query else {}
        items = await _api_get("/collectors/", params)
        if not items:
            await update.message.reply_text("No collectors found.")
            return
        total = len(items)
        lines = [f"<b>Collectors ({total} total){' matching &quot;' + _h(query) + '&quot;' if query else ''}</b>\n"]
        for c in items[:8]:
            line = f"• <b>{_h(c['name'])}</b>"
            if c.get("location"):
                line += f" — {_h(c['location'])}"
            if c.get("interests"):
                line += f"\n  <i>Interests: {_h(', '.join(c['interests'][:3]))}</i>"
            if c.get("bio"):
                line += f"\n  {_h(_truncate(c['bio'], 150))}"
            lines.append(line)
        if total > 8:
            lines.append(f"\n<i>...and {total - 8} more. Use /collectors &lt;name&gt; to search.</i>")
        await _send_html(update, "\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def curators_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    await update.message.chat.send_action("typing")
    try:
        params = {"q": query} if query else {}
        items = await _api_get("/curators/", params)
        if not items:
            await update.message.reply_text("No curators found.")
            return
        total = len(items)
        lines = [f"<b>Curators ({total} total){' matching &quot;' + _h(query) + '&quot;' if query else ''}</b>\n"]
        for c in items[:8]:
            line = f"• <b>{_h(c['name'])}</b>"
            if c.get("institution"):
                line += f" — {_h(c['institution'])}"
            if c.get("role"):
                line += f"\n  <i>{_h(c['role'])}</i>"
            if c.get("focus_areas"):
                line += f"\n  Focus: {_h(', '.join(c['focus_areas'][:3]))}"
            lines.append(line)
        if total > 8:
            lines.append(f"\n<i>...and {total - 8} more. Use /curators &lt;name&gt; to search.</i>")
        await _send_html(update, "\n".join(lines))
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
        text = f"<b>{_h(brief['title'])}</b>\n<i>Week of {_h(brief['week_of'])}</i>\n\n"
        if brief.get("top_mediums"):
            text += f"Trending: {_h(', '.join(brief['top_mediums'][:4]))}\n\n"
        text += _h(_truncate(brief["brief"], 800))
        await _send_html(update, text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def colors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        data = await _api_get("/briefs/color-trends/latest")
        if not data:
            await update.message.reply_text("No color trend data yet.")
            return
        lines = [f"<b>Color &amp; Size Trends — Week of {_h(data['week_of'])}</b>"]
        if data.get("summary"):
            lines.append(f"\n{_h(_truncate(data['summary'], 300))}")
        if data.get("popular_colors"):
            lines.append("\n<b>Popular Colors:</b>")
            for c in data["popular_colors"][:5]:
                lines.append(f"• {_h(c['name'])} <code>{_h(c['hex'])}</code> [{_h(c['trend'])}]")
        if data.get("popular_sizes"):
            lines.append("\n<b>Popular Sizes:</b>")
            for s in data["popular_sizes"][:5]:
                lines.append(f"• {_h(s['label'])} {_h(s['dimensions'])} · {_h(s['medium'])} [{_h(s['trend'])}]")
        await _send_html(update, "\n".join(lines))
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
        text = f"<b>Daily Action — {_h(action['date'])}</b>\n"
        if action.get("goal_name"):
            text += f"<i>Goal: {_h(action['goal_name'])}</i>\n\n"
        text += _h(action["content"])
        await _send_html(update, text)
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
        lines = [f"<b>{i+1}. {_h(item['title'])}</b>\n{_h(_truncate(item.get('summary', ''), 200))}" for i, item in enumerate(items)]
        await _send_html(update, "\n\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Search failed: {e}")


async def scan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Triggering full web scan... check back in ~5 minutes.")
    try:
        await _api_post("/scan/all")
    except Exception as e:
        await update.message.reply_text(f"Failed to trigger scan: {e}")


# ── Chat (fallback) ───────────────────────────────────────────────────────────

# Keyword → API endpoint mapping
_SECTION_ROUTES = {
    ("curator", "curators"):                                       "/curators/",
    ("journalist", "journalists", "press", "media"):               "/journalists/",
    ("institution", "institutions", "museum", "gallery"):          "/institutions/",
    ("collector", "collectors"):                                   "/collectors/",
    ("corporation", "corporations", "company", "brand", "sponsor"): "/corporations/",
    ("opportunity", "opportunities", "open call"):                 "/opportunities/",
    ("grant", "grants", "funding"):                                "/opportunities/",
    ("contest", "contests", "prize", "award"):                     "/opportunities/",
}


def _detect_section(text: str) -> tuple[str, str] | None:
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

    q_match = re.search(r'(?:find|search|show|list|get)\s+(?:me\s+)?(.+)', text, re.I)
    query = q_match.group(1).strip() if q_match else None

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
                lines = [f"<b>{_h(label.title())}s found: {len(items)}</b>"]
                for item in items[:6]:
                    name = _h(item.get("name") or item.get("title", ""))
                    detail = " · ".join(x for x in [
                        _h(item.get("role") or item.get("type") or item.get("category") or ""),
                        _h(item.get("institution") or item.get("organization") or item.get("contact_name") or item.get("organizer") or ""),
                    ] if x)
                    email = _h(item.get("email") or item.get("contact_email") or "")
                    line = f"• <b>{name}</b>" + (f" — {detail}" if detail else "")
                    if email:
                        line += f"\n  {email}"
                    lines.append(line)
                if len(items) > 6:
                    lines.append(f"<i>...and {len(items)-6} more. Use the app to see all.</i>")
                reply = "\n".join(lines)
                history.append({"role": "user", "content": text})
                history.append({"role": "assistant", "content": reply})
                _history[user_id] = history[-20:]
                await _send_html(update, reply)
                return
        except Exception:
            pass  # fall through to chat

    # Default: send to AI chat endpoint
    try:
        data = await _api_post("/chat/", {"message": text, "history": history[-10:]})
        response_text = data["response"]
        sources = data.get("sources", [])
        if sources:
            response_text += f"\n\nSources: {', '.join(sources[:3])}"
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": data["response"]})
        _history[user_id] = history[-20:]
        await _send_html(update, _h(response_text))
    except httpx.HTTPError as e:
        await update.message.reply_text(f"API error: {e}")
    except Exception as e:
        await update.message.reply_text(f"Something went wrong: {e}")
