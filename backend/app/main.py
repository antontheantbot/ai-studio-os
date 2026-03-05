import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
import app.models  # noqa: F401 — registers all ORM models with Base.metadata
from app.api.routes import router

logger = logging.getLogger(__name__)


async def _daily_scan_loop():
    """Run opportunity and grant scans once per day."""
    await asyncio.sleep(60)
    while True:
        try:
            logger.info("[Scheduler] Starting daily opportunity + grant scan")
            from app.agents.opportunity_scanner import scan_with_scoring
            from app.agents.tavily_scanner import run as tavily_run
            await scan_with_scoring()
            await tavily_run()
            logger.info("[Scheduler] Daily scan complete")
        except Exception as e:
            logger.error(f"[Scheduler] Daily scan error: {e}")
        await asyncio.sleep(24 * 60 * 60)


async def _weekly_journalist_scan_loop():
    """Scan for new journalists once per week."""
    await asyncio.sleep(120)  # stagger after other scans
    while True:
        try:
            logger.info("[Scheduler] Starting weekly journalist scan")
            from app.agents.web_ingestor import scan_journalists
            await scan_journalists()
            logger.info("[Scheduler] Weekly journalist scan complete")
        except Exception as e:
            logger.error(f"[Scheduler] Journalist scan error: {e}")
        await asyncio.sleep(7 * 24 * 60 * 60)


async def _weekly_market_scan_loop():
    """Scan art market and generate creative brief once per week."""
    await asyncio.sleep(90)  # stagger after daily scan starts
    while True:
        try:
            logger.info("[Scheduler] Starting weekly market brief scan")
            from app.api.routes.briefs import _scan_and_save
            await _scan_and_save()
            logger.info("[Scheduler] Weekly market brief complete")
        except Exception as e:
            logger.error(f"[Scheduler] Weekly market brief error: {e}")
        await asyncio.sleep(7 * 24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task = asyncio.create_task(_daily_scan_loop())
    market_task = asyncio.create_task(_weekly_market_scan_loop())
    journalist_task = asyncio.create_task(_weekly_journalist_scan_loop())
    yield
    task.cancel()
    market_task.cancel()
    journalist_task.cancel()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
