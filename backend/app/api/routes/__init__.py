from fastapi import APIRouter, BackgroundTasks

from app.api.routes import (
    opportunities,
    architecture,
    collectors,
    curators,
    press,
    proposals,
    knowledge,
    chat,
    strategy,
    artists,
    institutions,
    exhibitions,
    artworks,
    briefs,
    journalists,
    daily,
)

router = APIRouter()

router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
router.include_router(architecture.router, prefix="/architecture", tags=["architecture"])
router.include_router(collectors.router, prefix="/collectors", tags=["collectors"])
router.include_router(curators.router, prefix="/curators", tags=["curators"])
router.include_router(press.router, prefix="/press", tags=["press"])
router.include_router(proposals.router, prefix="/proposals", tags=["proposals"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
router.include_router(artists.router, prefix="/artists", tags=["artists"])
router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
router.include_router(exhibitions.router, prefix="/exhibitions", tags=["exhibitions"])
router.include_router(artworks.router, prefix="/artworks", tags=["artworks"])
router.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
router.include_router(journalists.router, prefix="/journalists", tags=["journalists"])
router.include_router(daily.router, prefix="/daily", tags=["daily"])


@router.post("/scan/all", tags=["scan"])
async def scan_everything(background_tasks: BackgroundTasks):
    """Trigger a full web scan across all categories (opportunities, architecture,
    collectors, curators, press, knowledge) using Tavily."""
    from app.agents.opportunity_scanner import scan_with_scoring
    from app.agents.web_ingestor import run_all
    background_tasks.add_task(scan_with_scoring)
    background_tasks.add_task(run_all)
    return {
        "status": "scanning",
        "categories": ["opportunities", "architecture", "collectors", "curators", "press", "knowledge"],
        "message": "Full web scan started — check back in ~5 minutes",
    }
