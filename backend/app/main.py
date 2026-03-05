import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.routes import router

logger = logging.getLogger(__name__)


async def _daily_scan_loop():
    """Run opportunity and grant scans once per day."""
    # Wait 60s after startup before the first scan so the DB is ready
    await asyncio.sleep(60)
    while True:
        try:
            logger.info("[Scheduler] Starting daily opportunity + grant scan")
            from app.agents.opportunity_scanner import scan_with_scoring
            from app.agents.tavily_scanner import run as tavily_run
            await asyncio.gather(scan_with_scoring(), tavily_run(), return_exceptions=True)
            logger.info("[Scheduler] Daily scan complete")
        except Exception as e:
            logger.error(f"[Scheduler] Daily scan error: {e}")
        await asyncio.sleep(24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task = asyncio.create_task(_daily_scan_loop())
    yield
    task.cancel()
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
