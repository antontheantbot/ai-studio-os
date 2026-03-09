"""
Press Monitor Agent v2
Three Celery jobs: scan_coverage, scan_journalists, generate_brief
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from app.db.session import SessionLocal
from app.models.press_monitor import (
    CoverageMention, TargetJournalist, JournalistArticle, PressBrief
)

logger = logging.getLogger("press_monitor")

SUBJECTS = ["Ryan Koopmans", "Alice Wexell", "The Wild Within"]

RELEVANCE_THEMES = [
    "nature reclaiming architecture", "biophilic design", "digital art",
    "photography and technology", "abandoned architecture", "immersive art",
    "screen-based art", "Scandinavian design", "architecture photography",
    "contemporary digital art", "nature and built environment",
    "time-based media", "art and ecology", "post-digital art",
    "media art", "large-scale photography", "art installation",
]

PUBLICATION_TIERS = {
    1: ["artforum", "frieze", "architectural digest", "vanity fair", "vogue",
        "artnews", "new york times", "guardian", "art newspaper", "wall street journal",
        "financial times", "apollo magazine", "flash art"],
    2: ["artnet", "artsy", "dezeen", "colossal", "designboom", "wallpaper",
        "dazed", "another magazine", "elephant magazine", "contemporary art daily",
        "hyperallergic", "e-flux", "mousse magazine"],
    3: ["arab news", "vogue arabia", "gq", "architectural review",
        "icon magazine", "mille world", "creative boom", "its nice that"],
}


def get_anthropic_client():
    from anthropic import Anthropic
    return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text: str) -> list:
    client = get_openai_client()
    response = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
    return response.data[0].embedding


def classify_tier(source: str) -> int:
    source_lower = source.lower()
    for tier, publications in PUBLICATION_TIERS.items():
        for pub in publications:
            if pub in source_lower:
                return tier
    return 4


def search_web(query: str) -> list:
    """Search web. Uses Tavily if available, else Playwright + DuckDuckGo."""
    try:
        if os.getenv("TAVILY_API_KEY"):
            from tavily import TavilyClient
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            results = client.search(query=query, search_depth="advanced", max_results=10, include_answer=False)
            return [
                {"title": r.get("title", ""), "url": r.get("url", ""),
                 "snippet": r.get("content", ""), "date": r.get("published_date", "")}
                for r in results.get("results", [])
            ]

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://html.duckduckgo.com/html/?q={query}", timeout=10000)
            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()
            results = []
            for result in soup.select(".result"):
                title_el = result.select_one(".result__title a")
                snippet_el = result.select_one(".result__snippet")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "date": "",
                    })
            return results[:10]
    except Exception as e:
        logger.error(f"Web search failed for '{query}': {e}")
        return []


# ============================================================
# JOB 1: COVERAGE SCANNER
# ============================================================

@shared_task(name="press_monitor.scan_coverage")
def scan_coverage():
    """Search web for mentions of Ryan/Alice/The Wild Within. Daily 6 AM."""
    db = SessionLocal()
    client = get_anthropic_client()
    new_mentions = []

    try:
        all_results = []
        for subject in SUBJECTS:
            for q in [f'"{subject}" art', f'"{subject}" exhibition 2025 OR 2026']:
                results = search_web(q)
                for r in results:
                    r["search_subject"] = subject
                all_results.extend(results)

        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                existing = db.query(CoverageMention).filter(CoverageMention.url == url).first()
                if not existing:
                    seen_urls.add(url)
                    unique_results.append(r)

        if not unique_results:
            logger.info("Coverage scan: no new mentions found.")
            return {"new_mentions": 0}

        results_text = "\n\n".join([
            f"[{i+1}] Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}\nSubject: {r['search_subject']}"
            for i, r in enumerate(unique_results[:20])
        ])

        analysis = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system="You are a press monitoring assistant for contemporary artists Ryan Koopmans and Alice Wexell. Analyze search results and determine which are genuine mentions. Filter out false positives. Return JSON.",
            messages=[{
                "role": "user",
                "content": f"""Analyze these search results. For each GENUINE mention of Ryan Koopmans, Alice Wexell, or The Wild Within, return a JSON array:
- index: result number
- source: publication name
- title: article title
- summary: 2-3 sentence summary in your own words
- sentiment: "positive", "neutral", or "negative"
- subjects: array of which subjects are mentioned

Return ONLY a JSON array. If no genuine mentions, return [].

Results:
{results_text}"""
            }]
        )

        response_text = analysis.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        mentions_data = json.loads(response_text)

        for mention in mentions_data:
            idx = mention.get("index", 0) - 1
            if 0 <= idx < len(unique_results):
                result = unique_results[idx]
                text_for_embedding = f"{mention.get('title', '')} {mention.get('summary', '')}"
                coverage = CoverageMention(
                    source=mention.get("source", result.get("title", "Unknown")),
                    title=mention.get("title", result.get("title")),
                    url=result["url"],
                    summary=mention.get("summary"),
                    sentiment=mention.get("sentiment", "neutral"),
                    subjects=mention.get("subjects", []),
                    published_at=datetime.utcnow(),
                    publication_tier=classify_tier(mention.get("source", "")),
                    embedding=get_embedding(text_for_embedding) if text_for_embedding.strip() else None,
                )
                db.add(coverage)
                new_mentions.append(mention)

        db.commit()
        logger.info(f"Coverage scan complete: {len(new_mentions)} new mentions stored.")
        return {"new_mentions": len(new_mentions)}

    except Exception as e:
        db.rollback()
        logger.error(f"Coverage scan error: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# ============================================================
# JOB 2: JOURNALIST ARTICLE SCANNER
# ============================================================

@shared_task(name="press_monitor.scan_journalists")
def scan_journalists():
    """Monitor target journalists' recent articles for warm outreach angles. Daily 7 AM."""
    db = SessionLocal()
    client = get_anthropic_client()
    actionable_count = 0

    try:
        journalists = db.query(TargetJournalist).filter(
            TargetJournalist.pitch_status.in_(["not_pitched", "pitched", "follow_up_due"])
        ).all()

        for journalist in journalists:
            all_results = []
            for q in [
                f'"{journalist.name}" {journalist.publication} article 2026',
                f'"{journalist.name}" {journalist.publication} wrote 2025 OR 2026',
            ]:
                all_results.extend(search_web(q))

            seen = set()
            unique = []
            for r in all_results:
                url = r.get("url", "")
                if url and url not in seen:
                    existing = db.query(JournalistArticle).filter(JournalistArticle.url == url).first()
                    if not existing:
                        seen.add(url)
                        unique.append(r)

            if not unique:
                continue

            results_text = "\n\n".join([
                f"[{i+1}] Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
                for i, r in enumerate(unique[:10])
            ])

            analysis = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                system=f"""You are an art world press strategist for Ryan Koopmans and Alice Wexell, a Stockholm-based artist duo whose work "The Wild Within" explores nature reclaiming abandoned architecture through photography, 3D digital sculpting, and time-based media.

Analyzing articles by {journalist.name} ({journalist.role} at {journalist.publication}) to find warm outreach angles.

Relevant themes: architecture, abandoned buildings, nature, ecology, biophilic design, digital art, screen-based art, photography + technology, Scandinavian art/design, immersive experiences, art market trends.

Score each article 0.0-1.0 for relevance. Above 0.6, suggest a warm pitch angle.""",
                messages=[{
                    "role": "user",
                    "content": f"""Analyze articles by {journalist.name}. For each genuinely BY this journalist, return JSON:
- index: result number
- title: article title
- summary: 1-2 sentence summary
- themes: array of topic themes
- relevance_score: 0.0-1.0
- warm_angle: if relevance > 0.6, a specific pitch angle (1-2 sentences). Otherwise null.

Return ONLY a JSON array. Filter out articles not by {journalist.name}.

Articles:
{results_text}"""
                }]
            )

            response_text = analysis.content[0].text.strip().replace("```json", "").replace("```", "").strip()
            try:
                articles_data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse analysis for {journalist.name}")
                continue

            for article in articles_data:
                idx = article.get("index", 0) - 1
                if 0 <= idx < len(unique):
                    result = unique[idx]
                    relevance = article.get("relevance_score", 0.0)
                    recently_pitched = (
                        journalist.last_pitched_at and
                        journalist.last_pitched_at > datetime.utcnow() - timedelta(days=30)
                    )
                    is_actionable = relevance >= 0.6 and not recently_pitched
                    text_for_embedding = f"{article.get('title', '')} {article.get('summary', '')}"

                    ja = JournalistArticle(
                        journalist_id=journalist.id,
                        title=article.get("title", result.get("title")),
                        url=result["url"],
                        summary=article.get("summary"),
                        published_at=datetime.utcnow(),
                        themes=article.get("themes", []),
                        relevance_score=relevance,
                        warm_angle=article.get("warm_angle"),
                        is_actionable=is_actionable,
                        embedding=get_embedding(text_for_embedding) if text_for_embedding.strip() else None,
                    )
                    db.add(ja)
                    if is_actionable:
                        actionable_count += 1

            db.commit()

        logger.info(f"Journalist scan complete: {actionable_count} actionable opportunities.")
        return {"actionable_opportunities": actionable_count}

    except Exception as e:
        db.rollback()
        logger.error(f"Journalist scan error: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# ============================================================
# JOB 3: DAILY BRIEF GENERATOR
# ============================================================

@shared_task(name="press_monitor.generate_brief")
def generate_brief():
    """Compile daily press brief and push to Telegram. Daily 8 AM."""
    db = SessionLocal()

    try:
        yesterday = datetime.utcnow() - timedelta(hours=24)
        today = datetime.utcnow().date()

        new_coverage = db.query(CoverageMention).filter(
            CoverageMention.discovered_at >= yesterday
        ).order_by(CoverageMention.publication_tier.asc()).all()

        actionable = db.query(JournalistArticle).filter(
            JournalistArticle.is_actionable == True,
            JournalistArticle.actioned == False
        ).order_by(JournalistArticle.relevance_score.desc()).all()

        follow_ups = db.query(TargetJournalist).filter(
            TargetJournalist.follow_up_date <= today,
            TargetJournalist.pitch_status.in_(["pitched", "follow_up_due"])
        ).all()

        brief_content = {
            "date": today.isoformat(),
            "coverage": [
                {"source": c.source, "title": c.title, "url": c.url,
                 "summary": c.summary, "sentiment": c.sentiment,
                 "tier": c.publication_tier, "subjects": c.subjects}
                for c in new_coverage
            ],
            "actionable_opportunities": [
                {"journalist": db.query(TargetJournalist).get(a.journalist_id).name if a.journalist_id else "Unknown",
                 "publication": db.query(TargetJournalist).get(a.journalist_id).publication if a.journalist_id else "Unknown",
                 "article_title": a.title, "article_url": a.url,
                 "relevance_score": a.relevance_score, "warm_angle": a.warm_angle, "themes": a.themes}
                for a in actionable[:10]
            ],
            "follow_ups_due": [
                {"name": f.name, "publication": f.publication, "email": f.email,
                 "follow_up_date": f.follow_up_date.isoformat() if f.follow_up_date else None, "notes": f.notes}
                for f in follow_ups
            ],
        }

        brief = PressBrief(
            brief_type="daily",
            coverage_count=len(new_coverage),
            actionable_count=len(actionable),
            content=brief_content,
        )
        db.add(brief)
        db.commit()

        telegram_message = _format_telegram_brief(brief_content)
        _push_to_telegram(telegram_message)

        logger.info(f"Daily brief: {len(new_coverage)} coverage, {len(actionable)} actionable, {len(follow_ups)} follow-ups.")
        return {"brief_id": brief.id, "coverage": len(new_coverage),
                "actionable": len(actionable), "follow_ups": len(follow_ups)}

    except Exception as e:
        db.rollback()
        logger.error(f"Brief generation error: {e}")
        return {"error": str(e)}
    finally:
        db.close()


def _format_telegram_brief(content: dict) -> str:
    lines = []
    date_str = content.get("date", "today")
    lines.append(f"{'='*30}")
    lines.append(f"PRESS BRIEF: {date_str}")
    lines.append(f"{'='*30}")

    follow_ups = content.get("follow_ups_due", [])
    if follow_ups:
        lines.append(f"\nFOLLOW-UPS DUE TODAY ({len(follow_ups)})")
        lines.append("-" * 20)
        for f in follow_ups:
            lines.append(f"  {f['name']} @ {f['publication']}")
            if f.get("email"): lines.append(f"  Email: {f['email']}")
            if f.get("notes"): lines.append(f"  Notes: {f['notes'][:100]}")
            lines.append("")

    opportunities = content.get("actionable_opportunities", [])
    if opportunities:
        lines.append(f"\nWARM OUTREACH OPPORTUNITIES ({len(opportunities)})")
        lines.append("-" * 20)
        for opp in opportunities[:5]:
            score_bar = "+" * int(opp["relevance_score"] * 10)
            lines.append(f"  {opp['journalist']} @ {opp['publication']}")
            lines.append(f"  Wrote: {opp['article_title'][:80]}")
            lines.append(f"  Relevance: [{score_bar:<10}] {opp['relevance_score']:.1f}")
            if opp.get("warm_angle"): lines.append(f"  ANGLE: {opp['warm_angle']}")
            lines.append(f"  Link: {opp['article_url']}")
            lines.append("")

    coverage = content.get("coverage", [])
    if coverage:
        lines.append(f"\nNEW MENTIONS ({len(coverage)})")
        lines.append("-" * 20)
        for c in coverage:
            emoji = {"positive": "+", "neutral": "o", "negative": "-"}.get(c["sentiment"], "o")
            tier_label = {1: "TOP", 2: "STRONG", 3: "MID", 4: "MINOR"}.get(c["tier"], "?")
            lines.append(f"  [{emoji}] [{tier_label}] {c['source']}")
            lines.append(f"  {c['title'][:80]}")
            if c.get("summary"): lines.append(f"  {c['summary'][:120]}")
            lines.append(f"  {c['url']}")
            lines.append("")

    if not follow_ups and not opportunities and not coverage:
        lines.append("\nQuiet day. No new mentions or opportunities.")
        lines.append("Consider proactive outreach to tier 1 targets.")

    lines.append(f"{'='*30}")
    return "\n".join(lines)


def _push_to_telegram(message: str):
    import httpx
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not set. Brief not pushed.")
        return
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    for chunk in chunks:
        try:
            httpx.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Telegram push failed: {e}")
