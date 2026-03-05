from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.services.llm import generate

router = APIRouter()


class ProposalRequest(BaseModel):
    opportunity_title: str
    opportunity_description: str
    artist_statement: str
    project_concept: str
    budget_range: str | None = None


@router.post("/generate")
async def generate_proposal(req: ProposalRequest, db: AsyncSession = Depends(get_db)):
    """Generate a museum-quality proposal using Claude."""
    prompt = f"""Generate a professional museum-quality artist proposal for the following opportunity.

Opportunity: {req.opportunity_title}
Description: {req.opportunity_description}

Artist Statement: {req.artist_statement}
Project Concept: {req.project_concept}
{f"Budget Range: {req.budget_range}" if req.budget_range else ""}

Write a compelling, structured proposal with:
1. Project Overview
2. Artistic Vision & Concept
3. Technical Approach
4. Timeline
5. Budget Justification (if applicable)
6. Artist Bio Summary

Use a professional, authoritative tone appropriate for museum and gallery submission."""

    text = await generate(prompt)
    return {"proposal": text, "request": req.model_dump()}


@router.get("/")
async def list_proposals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(__import__("sqlalchemy").text("SELECT id, title, created_at FROM proposals ORDER BY created_at DESC"))
    return [dict(r._mapping) for r in result]
