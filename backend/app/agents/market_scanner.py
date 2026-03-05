"""
Market Scanner — Tavily-powered scanner for art market trend intelligence.
Scans Christie's, Sotheby's, Art Basel, Pace Gallery, and Artsy to extract
market signals, then feeds them to Claude to generate weekly creative briefs.
"""
import json
import logging
import re
from datetime import date, timedelta

from tavily import AsyncTavilyClient

from app.core.config import settings
from app.services.llm import generate

logger = logging.getLogger(__name__)

MARKET_QUERIES = [
    "Christie's auction results digital art new media 2026",
    "Sotheby's contemporary art top lots sold 2026",
    "Art Basel 2026 featured artists trends emerging",
    "Pace Gallery new exhibitions digital art 2026",
    "Artsy art market report trending artists 2026",
    "Christie's new media AI art hammer price record",
    "Sotheby's generative art NFT auction results",
    "Art Basel Unlimited large scale installation artists",
    "Pace Gallery immersive digital commission 2026",
    "Artsy most collected artists price appreciation 2026",
    "art market report technology art investment 2026",
    "contemporary art fair trends collectors buying 2026",
]

SIGNALS_PROMPT = """From these art market search results (Christie's, Sotheby's, Art Basel, Pace, Artsy), extract market signals.

Return a JSON object with:
- signals: array of objects, each with:
  - signal (string, the market signal e.g. "AI-generated works breaking auction records")
  - source (string, e.g. "Christie's", "Sotheby's", "Art Basel", "Pace", "Artsy")
  - url (string, source URL)
  - category (string: "price_trend" | "medium_trend" | "collector_demand" | "institutional_focus" | "artist_breakout")
  - strength (string: "strong" | "moderate" | "emerging")
- top_artists: array of artist names showing strong market momentum
- top_mediums: array of mediums/categories gaining traction (e.g. "AI video", "generative sculpture")
- top_venues: array of venue names actively showing this work

Only include verifiable signals from named sources. Return {{ "signals": [], "top_artists": [], "top_mediums": [], "top_venues": [] }} if nothing relevant found.

Search results:
{results}"""

BRIEF_PROMPT = """You are a strategic creative director for a leading digital artist.
Based on the following art market signals from Christie's, Sotheby's, Art Basel, Pace, and Artsy, generate a detailed weekly creative brief.

Market signals:
{signals_json}

Top trending mediums: {top_mediums}
Top artists with momentum: {top_artists}
Active venues: {top_venues}
Week of: {week_of}

Generate a creative brief with these sections:

**MARKET PULSE — Week of {week_of}**

**1. KEY MARKET SIGNALS**
[3-5 bullet points: what is selling, what collectors are buying, what prices are doing]

**2. MEDIUM & FORM OPPORTUNITIES**
[Specific mediums and forms gaining institutional and collector traction right now]

**3. THEMATIC DIRECTIONS**
[3 concrete thematic directions an artist could explore, aligned with where collectors and institutions are looking]

**4. CREATIVE BRIEFS** (3 distinct project concepts)
For each brief include:
- Concept title
- One-paragraph description
- Target venue type
- Recommended medium
- Why this is well-timed for the current market

**5. STRATEGIC RECOMMENDATIONS**
[3-5 actionable steps: who to approach, which fairs to target, what to develop in the next 90 days]

Be specific, direct, and market-aware. Write for a sophisticated digital artist ready to act."""


COLOR_SIZE_QUERIES = [
    "contemporary art 2026 dominant color palette trend paintings photography",
    "popular art colors collectors buying 2026 gallery exhibition",
    "contemporary painting color trend earth tones monochrome palette 2026",
    "most popular artwork canvas size dimensions art market 2026",
    "artwork format size trend collecting 2026 fair gallery",
    "photography print size popular format contemporary art 2026",
    "contemporary art large small format trend collectors 2026",
]

COLOR_SIZE_PROMPT = """From these art market search results, extract the most popular colors and artwork sizes in contemporary art — paintings, photography, prints, video, and digital works. Exclude sculpture, ceramics, and furniture.

Return a JSON object with:
- popular_colors: array of up to 8 objects, each with:
  - name (string, color name e.g. "Raw Umber", "Cobalt Blue", "Warm White")
  - hex (string, closest approximate hex code e.g. "#7B6555")
  - trend (string: "rising" | "dominant" | "emerging")
  - context (string, one sentence e.g. "Dominant in large-format oil at Art Basel 2026")
- popular_sizes: array of up to 8 objects, each with:
  - label (string, e.g. "Large Format", "Cabinet Scale", "Square", "Panoramic")
  - dimensions (string, e.g. "150×200cm", "30×40cm", "variable")
  - medium (string, e.g. "Oil on canvas", "C-print", "Inkjet on paper")
  - trend (string: "rising" | "dominant" | "emerging")
  - context (string, one sentence on why this format is gaining traction)
- summary (string, 2–3 sentences summarising overall color and size trends)
- sources: array of source URLs referenced

Return {{ "popular_colors": [], "popular_sizes": [], "summary": "", "sources": [] }} if insufficient data.

Search results:
{results}"""


class MarketScanner:
    def __init__(self):
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def scan(self) -> dict:
        """Scan all market sources and return aggregated signals."""
        all_results = []
        seen_urls = set()

        for query in MARKET_QUERIES:
            try:
                response = await self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_answer=False,
                )
                for r in response.get("results", []):
                    if r.get("url") not in seen_urls:
                        all_results.append(r)
                        seen_urls.add(r.get("url", ""))
                logger.info(f"[MarketScanner] '{query}': {len(response.get('results', []))} results")
            except Exception as e:
                logger.error(f"[MarketScanner] Query failed '{query}': {e}")

        if not all_results:
            return {"signals": [], "top_artists": [], "top_mediums": [], "top_venues": []}

        formatted = "\n\n".join(
            f"Source: {r.get('url', '')}\nTitle: {r.get('title', '')}\nContent: {r.get('content', '')[:600]}"
            for r in all_results[:40]
        )

        try:
            raw = await generate(SIGNALS_PROMPT.format(results=formatted))
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"[MarketScanner] Signal extraction failed: {e}")

        return {"signals": [], "top_artists": [], "top_mediums": [], "top_venues": []}

    async def generate_brief(self, signals_data: dict, week_of: date) -> str:
        """Generate a creative brief from market signals."""
        signals_json = json.dumps(signals_data.get("signals", []), indent=2)
        top_mediums = ", ".join(signals_data.get("top_mediums", [])[:8]) or "varied"
        top_artists = ", ".join(signals_data.get("top_artists", [])[:8]) or "varied"
        top_venues = ", ".join(signals_data.get("top_venues", [])[:6]) or "major institutions"
        week_str = week_of.strftime("%B %d, %Y")

        return await generate(BRIEF_PROMPT.format(
            signals_json=signals_json,
            top_mediums=top_mediums,
            top_artists=top_artists,
            top_venues=top_venues,
            week_of=week_str,
        ))

    async def scan_color_size(self) -> dict:
        """Scan for popular colors and artwork sizes in contemporary art."""
        all_results = []
        seen_urls: set = set()

        for query in COLOR_SIZE_QUERIES:
            try:
                response = await self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_answer=False,
                )
                for r in response.get("results", []):
                    if r.get("url") not in seen_urls:
                        all_results.append(r)
                        seen_urls.add(r.get("url", ""))
                logger.info(f"[ColorSizeScanner] '{query}': {len(response.get('results', []))} results")
            except Exception as e:
                logger.error(f"[ColorSizeScanner] Query failed '{query}': {e}")

        if not all_results:
            return {"popular_colors": [], "popular_sizes": [], "summary": "", "sources": []}

        formatted = "\n\n".join(
            f"Source: {r.get('url', '')}\nTitle: {r.get('title', '')}\nContent: {r.get('content', '')[:600]}"
            for r in all_results[:35]
        )

        try:
            raw = await generate(COLOR_SIZE_PROMPT.format(results=formatted))
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"[ColorSizeScanner] Extraction failed: {e}")

        return {"popular_colors": [], "popular_sizes": [], "summary": "", "sources": []}

    def current_week_start(self) -> date:
        today = date.today()
        return today - timedelta(days=today.weekday())


_scanner = MarketScanner()


async def scan_market() -> dict:
    return await _scanner.scan()


async def generate_brief(signals_data: dict, week_of: date) -> str:
    return await _scanner.generate_brief(signals_data, week_of)


def current_week_start() -> date:
    return _scanner.current_week_start()


async def scan_color_size() -> dict:
    return await _scanner.scan_color_size()
