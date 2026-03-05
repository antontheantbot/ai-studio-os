from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from app.agents.strategy_advisor import strategy_advisor

router = APIRouter()


class StrategyQuery(BaseModel):
    question: str
    include_collectors: bool = True
    include_institutions: bool = True
    include_opportunities: bool = True
    include_locations: bool = True


class StrategyResponse(BaseModel):
    answer: str
    sources: List[dict]
    recommendations: List[str]


@router.post("/analyze", response_model=StrategyResponse)
async def analyze_strategy(query: StrategyQuery):
    """
    Analyze the art world database to answer strategic questions.

    Example questions:
    - "Which collectors in Switzerland collect digital art?"
    - "What museums show immersive digital installations?"
    - "Find architecture similar to Soviet sanatoriums."
    """
    result = await strategy_advisor.analyze(
        question=query.question,
        include_collectors=query.include_collectors,
        include_institutions=query.include_institutions,
        include_opportunities=query.include_opportunities,
        include_locations=query.include_locations,
    )
    return result


@router.get("/collectors")
async def collector_report(focus: str = Query(default="digital art")):
    """Get a strategic report on collectors matching a focus area."""
    return await strategy_advisor.get_collector_report(focus)


@router.get("/opportunities")
async def opportunity_strategy(months: int = Query(default=3, ge=1, le=12)):
    """Get strategic recommendations for upcoming opportunities."""
    return await strategy_advisor.get_opportunity_strategy(months)


@router.get("/locations")
async def location_recommendations(style: str = Query(default="brutalist")):
    """Get location recommendations for a specific architectural style."""
    return await strategy_advisor.get_location_recommendations(style)


@router.get("/institutions")
async def institution_map(region: str = Query(default="Europe")):
    """Map institutions in a region that show digital/installation art."""
    return await strategy_advisor.get_institution_map(region)
