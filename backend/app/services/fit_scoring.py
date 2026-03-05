"""
Fit Scoring Service
Calculates how well an opportunity matches the artist's profile.
"""
import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ArtistProfile:
    """Define the artist's focus for scoring."""
    focuses_on_digital_art: bool = True
    focuses_on_installations: bool = True
    focuses_on_architecture: bool = True
    preferred_scales: list[str] = None
    preferred_regions: list[str] = None
    min_budget: Optional[int] = None

    def __post_init__(self):
        if self.preferred_scales is None:
            self.preferred_scales = ["medium", "large", "monumental"]
        if self.preferred_regions is None:
            self.preferred_regions = []


# Default artist profile — customize as needed
DEFAULT_PROFILE = ArtistProfile(
    focuses_on_digital_art=True,
    focuses_on_installations=True,
    focuses_on_architecture=True,
    preferred_scales=["large", "monumental"],
    preferred_regions=["Europe", "North America", "Asia"],
    min_budget=10000,
)


def calculate_fit_score(
    opportunity: dict,
    profile: ArtistProfile = DEFAULT_PROFILE,
) -> dict:
    """
    Calculate a fit score (0-100) for an opportunity.

    Returns dict with:
        fit_score: float (0-100)
        digital_art_relevance: int (1-10)
        installation_scale: str
        architecture_relevance: int (1-10)
        breakdown: dict with component scores
    """
    scores = {
        "category_match": 0,
        "scale_match": 0,
        "region_match": 0,
        "budget_match": 0,
        "digital_relevance": 0,
        "architecture_relevance": 0,
    }

    title = (opportunity.get("title") or "").lower()
    description = (opportunity.get("description") or "").lower()
    category = (opportunity.get("category") or "").lower()
    combined_text = f"{title} {description} {category}"

    # ─── Digital Art Relevance (1-10) ───────────────────────────────────────
    digital_keywords = [
        "digital", "new media", "technology", "interactive", "immersive",
        "projection", "video", "ai", "artificial intelligence", "generative",
        "nft", "virtual", "augmented reality", "ar", "vr", "led", "screen"
    ]
    digital_count = sum(1 for kw in digital_keywords if kw in combined_text)
    digital_relevance = min(10, max(1, digital_count * 2))
    scores["digital_relevance"] = digital_relevance * 10  # max 100

    # ─── Architecture Relevance (1-10) ──────────────────────────────────────
    arch_keywords = [
        "architecture", "building", "space", "site-specific", "installation",
        "public art", "urban", "facade", "structure", "pavilion", "monument"
    ]
    arch_count = sum(1 for kw in arch_keywords if kw in combined_text)
    architecture_relevance = min(10, max(1, arch_count * 2))
    scores["architecture_relevance"] = architecture_relevance * 10

    # ─── Category Match ─────────────────────────────────────────────────────
    favorable_categories = ["commission", "residency", "festival", "biennale"]
    if any(cat in category for cat in favorable_categories):
        scores["category_match"] = 100
    elif "open_call" in category:
        scores["category_match"] = 70
    else:
        scores["category_match"] = 50

    # ─── Scale Detection ────────────────────────────────────────────────────
    if any(word in combined_text for word in ["monumental", "large-scale", "major"]):
        detected_scale = "monumental"
    elif any(word in combined_text for word in ["large", "significant", "substantial"]):
        detected_scale = "large"
    elif any(word in combined_text for word in ["small", "intimate", "modest"]):
        detected_scale = "small"
    else:
        detected_scale = "medium"

    if detected_scale in profile.preferred_scales:
        scores["scale_match"] = 100
    else:
        scores["scale_match"] = 40

    # ─── Region Match ───────────────────────────────────────────────────────
    location = (opportunity.get("location") or "").lower()
    if profile.preferred_regions:
        if any(region.lower() in location for region in profile.preferred_regions):
            scores["region_match"] = 100
        else:
            scores["region_match"] = 50
    else:
        scores["region_match"] = 75  # No preference = neutral

    # ─── Budget Match ───────────────────────────────────────────────────────
    budget_text = opportunity.get("budget") or ""
    try:
        # Try to extract numeric budget
        import re
        numbers = re.findall(r'[\d,]+', budget_text.replace(',', ''))
        if numbers:
            budget_value = int(numbers[-1])  # Take largest number
            if profile.min_budget and budget_value >= profile.min_budget:
                scores["budget_match"] = 100
            elif profile.min_budget:
                scores["budget_match"] = int((budget_value / profile.min_budget) * 100)
            else:
                scores["budget_match"] = 75
        else:
            scores["budget_match"] = 50  # Unknown budget
    except:
        scores["budget_match"] = 50

    # ─── Calculate Final Score ──────────────────────────────────────────────
    weights = {
        "digital_relevance": 0.25,
        "architecture_relevance": 0.20,
        "category_match": 0.15,
        "scale_match": 0.15,
        "region_match": 0.15,
        "budget_match": 0.10,
    }

    fit_score = sum(scores[k] * weights[k] for k in weights)

    return {
        "fit_score": round(fit_score, 1),
        "digital_art_relevance": digital_relevance,
        "installation_scale": detected_scale,
        "architecture_relevance": architecture_relevance,
        "breakdown": scores,
    }


async def score_and_update_opportunity(db, opportunity_id: str, opportunity_data: dict):
    """Calculate fit score and update the opportunity in the database."""
    from sqlalchemy import text

    result = calculate_fit_score(opportunity_data)

    await db.execute(
        text("""
            UPDATE opportunities
            SET fit_score = :fit_score,
                digital_art_relevance = :digital_art_relevance,
                installation_scale = :installation_scale,
                architecture_relevance = :architecture_relevance
            WHERE id = :id
        """),
        {
            "id": opportunity_id,
            "fit_score": result["fit_score"],
            "digital_art_relevance": result["digital_art_relevance"],
            "installation_scale": result["installation_scale"],
            "architecture_relevance": result["architecture_relevance"],
        }
    )
    await db.commit()

    return result
