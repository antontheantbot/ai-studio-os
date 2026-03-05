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
    strategy,
    artists,
    institutions,
    exhibitions,
    artworks,
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
