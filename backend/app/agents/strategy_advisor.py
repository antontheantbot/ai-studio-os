"""
Strategy Advisor Agent
Analyzes the knowledge base to provide strategic insights and recommendations.
"""
import logging
import json
from typing import Optional
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import chat

log = logging.getLogger(__name__)


STRATEGY_SYSTEM_PROMPT = """You are a strategic advisor for a digital installation artist.
You have access to a comprehensive database of:
- Art collectors and their interests
- Curators and institutions
- Exhibitions and press coverage
- Opportunities (residencies, commissions, festivals)
- Architecture locations suitable for installations

Your role is to analyze this data and provide actionable strategic insights.
Be specific, cite data when available, and prioritize opportunities that align with digital/installation art.

Format your responses with clear sections and bullet points when listing multiple items."""


class StrategyAdvisor:
    """AI-powered strategy advisor that analyzes the art world database."""

    async def analyze(
        self,
        question: str,
        include_collectors: bool = True,
        include_institutions: bool = True,
        include_opportunities: bool = True,
        include_locations: bool = True,
        limit_per_category: int = 10,
    ) -> dict:
        """
        Analyze the database to answer a strategic question.

        Returns:
            dict with 'answer', 'sources', and 'recommendations'
        """
        log.info(f"Strategy analysis requested: {question}")

        async with AsyncSessionLocal() as db:
            # Embed the question for semantic search
            query_embedding = await embed(question)
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            context_parts = []
            sources = []

            # ─── Gather relevant collectors ─────────────────────────────────
            if include_collectors:
                collectors = await db.execute(
                    text("""
                        SELECT name, interests, institutions, country, city,
                               1 - (embedding <=> :embedding) as similarity
                        FROM collectors
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding
                        LIMIT :limit
                    """),
                    {"embedding": embedding_str, "limit": limit_per_category}
                )
                collector_rows = collectors.fetchall()
                if collector_rows:
                    collector_text = "COLLECTORS:\n" + "\n".join(
                        f"- {r.name} ({r.city}, {r.country}): interests={r.interests}, institutions={r.institutions}"
                        for r in collector_rows
                    )
                    context_parts.append(collector_text)
                    sources.extend([{"type": "collector", "name": r.name} for r in collector_rows])

            # ─── Gather relevant institutions ───────────────────────────────
            if include_institutions:
                # Try new institutions table first
                try:
                    institutions = await db.execute(
                        text("""
                            SELECT name, city, country, type, focus_areas, digital_art_program,
                                   1 - (embedding <=> :embedding) as similarity
                            FROM institutions
                            WHERE embedding IS NOT NULL
                            ORDER BY embedding <=> :embedding
                            LIMIT :limit
                        """),
                        {"embedding": embedding_str, "limit": limit_per_category}
                    )
                    inst_rows = institutions.fetchall()
                    if inst_rows:
                        inst_text = "INSTITUTIONS:\n" + "\n".join(
                            f"- {r.name} ({r.city}, {r.country}): type={r.type}, focus={r.focus_areas}, digital_program={r.digital_art_program}"
                            for r in inst_rows
                        )
                        context_parts.append(inst_text)
                        sources.extend([{"type": "institution", "name": r.name} for r in inst_rows])
                except Exception:
                    pass  # Table might not exist yet

                # Also check curators for institution info
                curators = await db.execute(
                    text("""
                        SELECT name, institution, focus_areas, notable_shows,
                               1 - (embedding <=> :embedding) as similarity
                        FROM curators
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding
                        LIMIT :limit
                    """),
                    {"embedding": embedding_str, "limit": limit_per_category}
                )
                curator_rows = curators.fetchall()
                if curator_rows:
                    curator_text = "CURATORS:\n" + "\n".join(
                        f"- {r.name} at {r.institution}: focus={r.focus_areas}, shows={r.notable_shows}"
                        for r in curator_rows
                    )
                    context_parts.append(curator_text)
                    sources.extend([{"type": "curator", "name": r.name} for r in curator_rows])

            # ─── Gather relevant opportunities ──────────────────────────────
            if include_opportunities:
                opportunities = await db.execute(
                    text("""
                        SELECT title, category, deadline, url, description, fit_score,
                               1 - (embedding <=> :embedding) as similarity
                        FROM opportunities
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding
                        LIMIT :limit
                    """),
                    {"embedding": embedding_str, "limit": limit_per_category}
                )
                opp_rows = opportunities.fetchall()
                if opp_rows:
                    opp_text = "OPPORTUNITIES:\n" + "\n".join(
                        f"- {r.title} ({r.category}): deadline={r.deadline}, fit_score={r.fit_score}"
                        for r in opp_rows
                    )
                    context_parts.append(opp_text)
                    sources.extend([{"type": "opportunity", "title": r.title} for r in opp_rows])

            # ─── Gather relevant locations ──────────────────────────────────
            if include_locations:
                locations = await db.execute(
                    text("""
                        SELECT name, city, country, style, suitability, photography_score,
                               1 - (embedding <=> :embedding) as similarity
                        FROM architecture_locations
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding
                        LIMIT :limit
                    """),
                    {"embedding": embedding_str, "limit": limit_per_category}
                )
                loc_rows = locations.fetchall()
                if loc_rows:
                    loc_text = "LOCATIONS:\n" + "\n".join(
                        f"- {r.name} ({r.city}, {r.country}): style={r.style}, suitability={r.suitability}"
                        for r in loc_rows
                    )
                    context_parts.append(loc_text)
                    sources.extend([{"type": "location", "name": r.name} for r in loc_rows])

            # ─── Generate strategic analysis ────────────────────────────────
            if not context_parts:
                return {
                    "answer": "I don't have enough data in the database to answer this question. Try running the scanner agents first to populate the database.",
                    "sources": [],
                    "recommendations": [],
                }

            full_context = "\n\n".join(context_parts)

            prompt = f"""Based on the following data from our art world database, answer this strategic question:

QUESTION: {question}

DATABASE CONTEXT:
{full_context}

Provide:
1. A direct answer to the question
2. Specific recommendations based on the data
3. Any patterns or insights you notice"""

            answer = await chat(
                messages=[{"role": "user", "content": prompt}],
                system=STRATEGY_SYSTEM_PROMPT,
                max_tokens=2000,
            )

            # Extract recommendations (simple heuristic)
            recommendations = []
            if "recommend" in answer.lower():
                lines = answer.split("\n")
                for line in lines:
                    if any(word in line.lower() for word in ["recommend", "suggest", "consider", "prioritize"]):
                        if line.strip().startswith("-") or line.strip().startswith("•"):
                            recommendations.append(line.strip().lstrip("-•").strip())

            return {
                "answer": answer,
                "sources": sources[:20],  # Limit sources in response
                "recommendations": recommendations[:10],
            }

    async def get_collector_report(self, focus: str = "digital art") -> dict:
        """Generate a report on collectors who match a specific focus."""
        question = f"Which collectors are most likely to be interested in {focus}? What are their collecting patterns and institutional connections?"
        return await self.analyze(
            question,
            include_collectors=True,
            include_institutions=True,
            include_opportunities=False,
            include_locations=False,
        )

    async def get_opportunity_strategy(self, months_ahead: int = 3) -> dict:
        """Generate a strategic plan for upcoming opportunities."""
        question = f"What are the most strategic opportunities to pursue in the next {months_ahead} months for a digital installation artist? Consider fit scores, deadlines, and institutional prestige."
        return await self.analyze(
            question,
            include_collectors=False,
            include_institutions=True,
            include_opportunities=True,
            include_locations=False,
        )

    async def get_location_recommendations(self, style: str = "brutalist") -> dict:
        """Get location recommendations for a specific architectural style."""
        question = f"What are the best {style} architecture locations for photography or installations? Consider accessibility and visual potential."
        return await self.analyze(
            question,
            include_collectors=False,
            include_institutions=False,
            include_opportunities=False,
            include_locations=True,
        )

    async def get_institution_map(self, region: str = "Europe") -> dict:
        """Map institutions in a region that show digital/installation art."""
        question = f"Which institutions in {region} have strong digital art programs or have shown immersive installations? What curators should I know?"
        return await self.analyze(
            question,
            include_collectors=False,
            include_institutions=True,
            include_opportunities=False,
            include_locations=False,
        )


# Singleton instance
strategy_advisor = StrategyAdvisor()


async def run():
    """Run a sample strategy analysis."""
    result = await strategy_advisor.analyze(
        "What institutions should I prioritize for showing digital installations?"
    )
    log.info(f"Strategy analysis complete: {len(result['sources'])} sources consulted")
    return result
