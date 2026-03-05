from fastapi import APIRouter

from app.api.routes import (
    opportunities,
    architecture,
    collectors,
    curators,
    press,
    proposals,
    knowledge,
    chat,
    artists,
    artworks,
)

router = APIRouter()

router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
router.include_router(architecture.router, prefix="/architecture", tags=["Architecture"])
router.include_router(collectors.router, prefix="/collectors", tags=["Collectors"])
router.include_router(curators.router, prefix="/curators", tags=["Curators"])
router.include_router(press.router, prefix="/press", tags=["Press"])
router.include_router(proposals.router, prefix="/proposals", tags=["Proposals"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(artists.router, prefix="/artists", tags=["Artists"])
router.include_router(artworks.router, prefix="/artworks", tags=["Artworks"])
