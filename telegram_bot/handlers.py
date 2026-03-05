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


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to *AI Studio OS*\n\n"
        "I can help you with:\n"
        "• Finding art opportunities\n"
        "• Researching collectors & curators\n"
        "• Monitoring press & exhibitions\n"
        "• Writing proposals\n"
        "• Searching your knowledge base\n\n"
        "Just send me a message, or use /help for commands.",
        parse_mode="Markdown",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Commands*\n"
        "/scan — trigger opportunity scanner\n"
        "/search <query> — search knowledge base\n"
        "/help — show this message\n\n"
        "Or just chat naturally — I'll search your studio database to answer.",
        parse_mode="Markdown",
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    history = _history.get(user_id, [])

    await update.message.chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{API_BASE}/chat/",
                json={"message": text, "history": history[-10:]},  # last 5 turns
            )
            resp.raise_for_status()
            data = resp.json()

        response_text = data["response"]
        sources = data.get("sources", [])

        if sources:
            response_text += f"\n\n_Sources: {', '.join(sources[:3])}_"

        # Update history
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": data["response"]})
        _history[user_id] = history[-20:]  # keep last 10 turns

        await update.message.reply_text(response_text, parse_mode="Markdown")

    except httpx.HTTPError as e:
        await update.message.reply_text(f"API error: {e}")
    except Exception as e:
        await update.message.reply_text(f"Something went wrong: {e}")


async def scan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Triggering opportunity scan...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{API_BASE}/opportunities/scan")
            data = resp.json()
        await update.message.reply_text(f"Scan queued. Task ID: `{data['task_id']}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Failed to trigger scan: {e}")


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <your query>")
        return

    await update.message.chat.send_action("typing")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{API_BASE}/knowledge/search", params={"q": query, "limit": 5})
            items = resp.json()

        if not items:
            await update.message.reply_text("No results found.")
            return

        lines = [f"*{i+1}. {item['title']}*\n{item.get('summary', '')[:200]}" for i, item in enumerate(items)]
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Search failed: {e}")
