import anthropic
from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are the AI assistant for an artist's studio OS.
You have access to a knowledge base of opportunities, collectors, curators,
press articles, and research notes. Answer concisely and accurately.
When referencing sources, cite them by title."""


async def chat(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    """Send messages to Claude and return the text response."""
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


async def generate(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Single-turn generation helper."""
    return await chat([{"role": "user", "content": prompt}], system=system)
