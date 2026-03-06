"""
AI Studio OS — Telegram Bot
Connects to the FastAPI backend for all sections.
"""
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from handlers import (
    start_handler,
    help_handler,
    message_handler,
    scan_handler,
    search_handler,
    opportunities_handler,
    grants_handler,
    contests_handler,
    journalists_handler,
    collectors_handler,
    curators_handler,
    brief_handler,
    colors_handler,
    daily_handler,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # Opportunities & Grants
    app.add_handler(CommandHandler("opportunities", opportunities_handler))
    app.add_handler(CommandHandler("grants", grants_handler))
    app.add_handler(CommandHandler("contests", contests_handler))

    # People
    app.add_handler(CommandHandler("journalists", journalists_handler))
    app.add_handler(CommandHandler("collectors", collectors_handler))
    app.add_handler(CommandHandler("curators", curators_handler))

    # Market Intelligence
    app.add_handler(CommandHandler("brief", brief_handler))
    app.add_handler(CommandHandler("colors", colors_handler))

    # Daily Action
    app.add_handler(CommandHandler("daily", daily_handler))

    # Search & Scan
    app.add_handler(CommandHandler("search", search_handler))
    app.add_handler(CommandHandler("scan", scan_handler))

    # Fallback: natural language chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("Bot starting with all sections enabled...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
