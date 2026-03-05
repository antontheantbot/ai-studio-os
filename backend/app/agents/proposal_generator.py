"""
Proposal Generator Agent
Generates and saves museum-quality proposals using Claude.
Also embeds them for future semantic search.
"""
import logging
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

PROPOSAL_SYSTEM = """You are an expert art writer with 20 years of experience writing
successful proposals for museums, biennials, and public art commissions.
Your proposals are precise, conceptually rigorous, and compelling.
You understand both the artistic vision and the institutional language required."""

PROPOSAL_PROMPT = """Write a complete, museum-quality proposal for the following opportunity.

OPPORTUNITY
Title: {opportunity_title}
Description: {opportunity_description}

ARTIST INPUT
Statement: {artist_statement}
Project Concept: {project_concept}
{budget_section}

Structure the proposal with these sections:
1. Project Title
2. Executive Summary (150 words)
3. Artistic Concept & Vision (300 words)
4. Technical Approach & Materials (200 words)
5. Exhibition / Presentation Plan (150 words)
6. Timeline (bullet points)
7. Budget Overview{budget_note}
8. Artist Biography (100 words)

Use authoritative, precise language. Avoid clichés."""


class ProposalGenerator:
    async def generate(
        self,
        opportunity_title: str,
        opportunity_description: str,
        artist_statement: str,
        project_concept: str,
        budget_range: str | None = None,
        opportunity_id: str | None = None,
    ) -> dict:
        budget_section = f"Budget Range: {budget_range}" if budget_range else ""
        budget_note = f" (target range: {budget_range})" if budget_range else ""

        prompt = PROPOSAL_PROMPT.format(
            opportunity_title=opportunity_title,
            opportunity_description=opportunity_description,
            artist_statement=artist_statement,
            project_concept=project_concept,
            budget_section=budget_section,
            budget_note=budget_note,
        )

        content = await generate(prompt, system=PROPOSAL_SYSTEM)
        title = f"Proposal: {opportunity_title}"

        proposal_id = await self._save(
            title=title,
            content=content,
            opportunity_id=opportunity_id,
        )

        return {"id": proposal_id, "title": title, "content": content}

    async def _save(self, title: str, content: str, opportunity_id: str | None) -> str:
        embedding = await embed(f"{title}\n{content[:2000]}")
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("""
                    INSERT INTO proposals (title, content, opportunity_id, embedding)
                    VALUES (:title, :content, :opportunity_id, :embedding::vector)
                    RETURNING id
                """),
                {
                    "title": title,
                    "content": content,
                    "opportunity_id": opportunity_id,
                    "embedding": embedding_str,
                },
            )
            await db.commit()
            return str(result.first()[0])
