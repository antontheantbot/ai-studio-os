import logging
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.services.llm import chat

router = APIRouter()
logger = logging.getLogger(__name__)

GOALS = [
    "Feature coverage in Architectural Digest, Vanity Fair, Vogue Scandinavia, Frieze, Artnet, Artsy, The Art Newspaper",
    "World-class Instagram presence (target: 100K+ followers, strong engagement)",
    "Google Knowledge Panel and dominant SEO for 'Ryan Koopmans' and 'Alice Wexell'",
    "Permanent collection acquisition at the Louvre Abu Dhabi or Guggenheim Abu Dhabi",
    "High revenue from artwork sales, NFT/Bitcoin Ordinals releases, and luxury brand collaborations",
    "Becoming Leila Heller Gallery's highest-selling artist",
    "Showing at Art Basel within 2 years",
    "Having their work recognised in art history",
]

SYSTEM_PROMPT = """You are a strategic career assistant for Ryan Koopmans and Alice Wexell, a world-renowned contemporary artist duo based in Stockholm. Their singular mission is to become the most successful contemporary artists in the world.

Their goals are:
- Feature coverage in Architectural Digest, Vanity Fair, Vogue Scandinavia, and top-tier art publications (Frieze, Artnet, Artsy, The Art Newspaper)
- A world-class Instagram presence (target: 100K+ followers, strong engagement)
- A Google Knowledge Panel and dominant SEO for "Ryan Koopmans" and "Alice Wexell"
- Permanent collection acquisition at the Louvre Abu Dhabi or Guggenheim Abu Dhabi
- High revenue from artwork sales, NFT/Bitcoin Ordinals releases, and luxury brand collaborations
- Becoming Leila Heller Gallery's highest-selling artist
- Showing at Art Basel within 2 years
- Having their work recognised in art history

You generate one specific, concrete, achievable daily action that moves them toward their goals. Your tone is direct, professional, and ambitious. Never give vague advice."""

ACTION_PROMPT = """Today is {date}. Generate today's daily action focused on this goal:

GOAL: {goal}

Respond in EXACTLY this format — no intro, no sign-off, just the block:

---
🎯 DAILY ACTION — {date}

GOAL IT SERVES: {goal}

TODAY'S ACTION:
[One single, concrete, achievable action they can complete today. Be specific — not "reach out to press" but name the exact editor, publication, subject line, or platform. Include any specific names, handles, or contacts if relevant.]

WHY TODAY:
[1–2 sentences on why this action matters and how it connects to the bigger goal.]

TIME REQUIRED: [realistic estimate, e.g. "30 minutes"]

WHAT GOOD LOOKS LIKE:
[What the completed action looks like — specific and tangible.]

---"""


async def _generate_action(goal_index: int, today: date) -> str:
    goal = GOALS[goal_index]
    date_str = today.strftime("%A, %B %d %Y")
    prompt = ACTION_PROMPT.format(date=date_str, goal=goal)
    return await chat([{"role": "user", "content": prompt}], system=SYSTEM_PROMPT)


async def _get_or_create_today(db: AsyncSession) -> dict:
    today = date.today()

    # Check if today's action already exists
    result = await db.execute(
        text("SELECT * FROM daily_actions WHERE date = :d"), {"d": today}
    )
    row = result.first()
    if row:
        return dict(row._mapping)

    # Find last goal used to rotate
    last = await db.execute(
        text("SELECT goal_index FROM daily_actions ORDER BY date DESC LIMIT 1")
    )
    last_row = last.first()
    last_index = last_row.goal_index if last_row else -1
    next_index = (last_index + 1) % len(GOALS)

    content = await _generate_action(next_index, today)

    await db.execute(
        text("""
            INSERT INTO daily_actions (id, date, goal_index, goal_name, content)
            VALUES (gen_random_uuid(), :date, :goal_index, :goal_name, :content)
            ON CONFLICT (date) DO NOTHING
        """),
        {
            "date": today,
            "goal_index": next_index,
            "goal_name": GOALS[next_index],
            "content": content,
        },
    )
    await db.commit()

    result = await db.execute(
        text("SELECT * FROM daily_actions WHERE date = :d"), {"d": today}
    )
    return dict(result.first()._mapping)


@router.get("/today")
async def get_today(db: AsyncSession = Depends(get_db)):
    return await _get_or_create_today(db)


@router.post("/generate")
async def force_generate(db: AsyncSession = Depends(get_db)):
    """Force-regenerate today's action (replaces existing)."""
    today = date.today()

    # Advance from today's current entry if it exists, otherwise from yesterday's
    last = await db.execute(
        text("SELECT goal_index FROM daily_actions ORDER BY date DESC, updated_at DESC LIMIT 1"),
    )
    last_row = last.first()
    last_index = last_row.goal_index if last_row else -1
    next_index = (last_index + 1) % len(GOALS)

    content = await _generate_action(next_index, today)

    await db.execute(
        text("""
            INSERT INTO daily_actions (id, date, goal_index, goal_name, content)
            VALUES (gen_random_uuid(), :date, :goal_index, :goal_name, :content)
            ON CONFLICT (date) DO UPDATE SET
                goal_index = EXCLUDED.goal_index,
                goal_name = EXCLUDED.goal_name,
                content = EXCLUDED.content,
                updated_at = now()
        """),
        {
            "date": today,
            "goal_index": next_index,
            "goal_name": GOALS[next_index],
            "content": content,
        },
    )
    await db.commit()

    result = await db.execute(
        text("SELECT * FROM daily_actions WHERE date = :d"), {"d": today}
    )
    return dict(result.first()._mapping)


@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM daily_actions ORDER BY date DESC LIMIT 30")
    )
    return [dict(r._mapping) for r in result]
