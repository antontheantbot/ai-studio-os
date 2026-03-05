import json
import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_briefs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, week_of, title, trends, top_artists, top_mediums, brief, sources, created_at FROM market_briefs ORDER BY week_of DESC LIMIT 20")
    )
    return [dict(r._mapping) for r in result]


@router.get("/latest")
async def latest_brief(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM market_briefs ORDER BY week_of DESC LIMIT 1")
    )
    row = result.first()
    return dict(row._mapping) if row else {}


@router.post("/scan")
async def scan_market(background_tasks: BackgroundTasks):
    """Scan Christie's, Sotheby's, Art Basel, Pace, Artsy for market signals and save a brief."""
    background_tasks.add_task(_scan_and_save)
    return {"status": "scanning", "message": "Scanning art market sources — brief ready in ~3 minutes"}


@router.get("/color-trends/latest")
async def latest_color_trends(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM color_size_trends ORDER BY week_of DESC LIMIT 1")
    )
    row = result.first()
    return dict(row._mapping) if row else {}


@router.post("/color-trends/scan")
async def scan_color_trends(background_tasks: BackgroundTasks):
    """Scan contemporary art sources for popular colors and sizes."""
    background_tasks.add_task(_scan_color_size_and_save)
    return {"status": "scanning", "message": "Scanning for color and size trends — ready in ~2 minutes"}


async def _scan_color_size_and_save():
    from app.agents.market_scanner import scan_color_size, current_week_start
    from app.db.session import AsyncSessionLocal

    week_of = current_week_start()
    try:
        data = await scan_color_size()
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO color_size_trends (id, week_of, popular_colors, popular_sizes, summary, sources)
                    VALUES (gen_random_uuid(), :week_of, CAST(:colors AS jsonb), CAST(:sizes AS jsonb), :summary, CAST(:sources AS jsonb))
                    ON CONFLICT (week_of) DO UPDATE SET
                        popular_colors = EXCLUDED.popular_colors,
                        popular_sizes = EXCLUDED.popular_sizes,
                        summary = EXCLUDED.summary,
                        sources = EXCLUDED.sources,
                        updated_at = now()
                """),
                {
                    "week_of": week_of,
                    "colors": json.dumps(data.get("popular_colors", [])),
                    "sizes": json.dumps(data.get("popular_sizes", [])),
                    "summary": data.get("summary", ""),
                    "sources": json.dumps(data.get("sources", [])),
                },
            )
            await db.commit()
            logger.info(f"[ColorSizeScanner] Trends saved for week {week_of}")
    except Exception as e:
        logger.error(f"[ColorSizeScanner] Scan and save failed: {e}")


async def _scan_and_save():
    from app.agents.market_scanner import scan_market, generate_brief, current_week_start
    from app.db.session import AsyncSessionLocal

    week_of = current_week_start()

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            text("SELECT id FROM market_briefs WHERE week_of = :w"), {"w": week_of}
        )
        if existing.first():
            logger.info(f"[MarketScanner] Brief for week {week_of} already exists, regenerating")

    try:
        signals_data = await scan_market()
        brief_text = await generate_brief(signals_data, week_of)

        signals = signals_data.get("signals", [])
        top_artists = signals_data.get("top_artists", [])
        top_mediums = signals_data.get("top_mediums", [])
        top_venues = signals_data.get("top_venues", [])
        sources = list({s.get("url") for s in signals if s.get("url")})
        trends = [
            {"category": s.get("category"), "signal": s.get("signal"), "strength": s.get("strength")}
            for s in signals
        ]

        title = f"Market Brief — Week of {week_of.strftime('%B %d, %Y')}"

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO market_briefs (id, week_of, title, signals, trends, top_artists, top_mediums, brief, sources)
                    VALUES (gen_random_uuid(), :week_of, :title, CAST(:signals AS jsonb), CAST(:trends AS jsonb),
                            CAST(:top_artists AS jsonb), CAST(:top_mediums AS jsonb),
                            :brief, CAST(:sources AS jsonb))
                    ON CONFLICT (week_of) DO UPDATE SET
                        title = EXCLUDED.title,
                        signals = EXCLUDED.signals,
                        trends = EXCLUDED.trends,
                        top_artists = EXCLUDED.top_artists,
                        top_mediums = EXCLUDED.top_mediums,
                        brief = EXCLUDED.brief,
                        sources = EXCLUDED.sources,
                        updated_at = now()
                """),
                {
                    "week_of": week_of,
                    "title": title,
                    "signals": json.dumps(signals),
                    "trends": json.dumps(trends),
                    "top_artists": json.dumps(top_artists),
                    "top_mediums": json.dumps(top_mediums),
                    "brief": brief_text,
                    "sources": json.dumps(sources),
                },
            )
            await db.commit()
            logger.info(f"[MarketScanner] Brief saved for week {week_of}")
    except Exception as e:
        logger.error(f"[MarketScanner] Scan and save failed: {e}")
