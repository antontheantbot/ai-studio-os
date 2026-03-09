"""Press Monitor v2 API Routes"""

import asyncio
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.press_monitor import (
    CoverageMention, TargetJournalist, JournalistArticle, PressBrief
)

router = APIRouter()


@router.get("/coverage")
async def list_coverage(
    days: int = Query(7, ge=1, le=90),
    sentiment: Optional[str] = Query(None),
    tier: Optional[int] = Query(None, ge=1, le=4),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(CoverageMention).where(CoverageMention.discovered_at >= since)
    if sentiment:
        stmt = stmt.where(CoverageMention.sentiment == sentiment)
    if tier:
        stmt = stmt.where(CoverageMention.publication_tier == tier)
    stmt = stmt.order_by(desc(CoverageMention.discovered_at)).limit(limit)
    result = await db.execute(stmt)
    mentions = result.scalars().all()
    return [
        {"id": m.id, "source": m.source, "title": m.title, "url": m.url,
         "summary": m.summary, "sentiment": m.sentiment, "subjects": m.subjects,
         "publication_tier": m.publication_tier,
         "published_at": m.published_at.isoformat() if m.published_at else None,
         "discovered_at": m.discovered_at.isoformat() if m.discovered_at else None}
        for m in mentions
    ]


@router.get("/coverage/stats")
async def coverage_stats(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(select(CoverageMention).where(CoverageMention.discovered_at >= since))
    mentions = result.scalars().all()
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    sources = {}
    for m in mentions:
        sentiment_counts[m.sentiment] = sentiment_counts.get(m.sentiment, 0) + 1
        tier_counts[m.publication_tier] = tier_counts.get(m.publication_tier, 0) + 1
        sources[m.source] = sources.get(m.source, 0) + 1
    return {"period_days": days, "total_mentions": len(mentions),
            "by_sentiment": sentiment_counts, "by_tier": tier_counts,
            "top_sources": sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]}


@router.get("/journalists")
async def list_journalists(
    status: Optional[str] = Query(None),
    tier: Optional[int] = Query(None, ge=1, le=4),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TargetJournalist).options(selectinload(TargetJournalist.articles))
    if status:
        stmt = stmt.where(TargetJournalist.pitch_status == status)
    if tier:
        stmt = stmt.where(TargetJournalist.tier == tier)
    stmt = stmt.order_by(TargetJournalist.tier.asc(), TargetJournalist.name.asc())
    result = await db.execute(stmt)
    journalists = result.scalars().all()
    return [
        {"id": j.id, "name": j.name, "email": j.email, "publication": j.publication,
         "role": j.role, "beats": j.beat or [], "tier_level": j.tier,
         "pitch_status": j.pitch_status,
         "follow_up_date": j.follow_up_date.isoformat() if j.follow_up_date else None,
         "last_pitched_at": j.last_pitched_at.isoformat() if j.last_pitched_at else None,
         "notes": j.notes,
         "article_count": len(j.articles),
         "actionable_count": sum(1 for a in j.articles if a.is_actionable and not a.actioned)}
        for j in journalists
    ]


@router.post("/journalists")
async def add_journalist(
    name: str, publication: str, email: Optional[str] = None,
    role: Optional[str] = None, tier: int = 2, notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TargetJournalist).where(
            TargetJournalist.name == name, TargetJournalist.publication == publication))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"{name} at {publication} already exists.")
    journalist = TargetJournalist(name=name, email=email, publication=publication,
                                  role=role, tier=tier, notes=notes)
    db.add(journalist)
    await db.commit()
    await db.refresh(journalist)
    return {"id": journalist.id, "name": journalist.name, "publication": journalist.publication}


@router.patch("/journalists/{journalist_id}")
async def update_journalist(
    journalist_id: int, email: Optional[str] = None,
    pitch_status: Optional[str] = None, follow_up_date: Optional[str] = None,
    notes: Optional[str] = None, db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TargetJournalist).where(TargetJournalist.id == journalist_id))
    j = result.scalar_one_or_none()
    if not j:
        raise HTTPException(status_code=404, detail="Journalist not found.")
    if email is not None:
        j.email = email
    if pitch_status is not None:
        j.pitch_status = pitch_status
        if pitch_status == "pitched":
            j.last_pitched_at = datetime.utcnow()
    if follow_up_date is not None:
        j.follow_up_date = date.fromisoformat(follow_up_date) if follow_up_date else None
    if notes is not None:
        j.notes = notes
    j.updated_at = datetime.utcnow()
    await db.commit()
    return {"updated": True, "id": j.id}


@router.get("/opportunities")
async def list_opportunities(
    actionable_only: bool = Query(False),
    min_relevance: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JournalistArticle).options(selectinload(JournalistArticle.journalist))
    if actionable_only:
        stmt = stmt.where(JournalistArticle.is_actionable == True, JournalistArticle.actioned == False)
    if min_relevance > 0:
        stmt = stmt.where(JournalistArticle.relevance_score >= min_relevance)
    stmt = stmt.order_by(desc(JournalistArticle.relevance_score)).limit(limit)
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return [
        {"id": a.id,
         "journalist_name": a.journalist.name if a.journalist else "Unknown",
         "journalist_email": a.journalist.email if a.journalist else None,
         "journalist_publication": a.journalist.publication if a.journalist else "Unknown",
         "title": a.title, "url": a.url, "summary": a.summary,
         "themes": a.themes, "relevance_score": a.relevance_score,
         "warm_pitch_angle": a.warm_angle,
         "is_actionable": a.is_actionable,
         "actioned": a.actioned,
         "discovered_at": a.discovered_at.isoformat() if a.discovered_at else None}
        for a in articles
    ]


@router.post("/opportunities/{article_id}/action")
async def mark_actioned(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalistArticle).where(JournalistArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    article.actioned = True
    await db.commit()
    return {"actioned": True, "id": article.id}


@router.get("/briefs")
async def list_briefs(brief_type: str = Query("daily"), limit: int = Query(7, ge=1, le=30),
                      db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PressBrief).where(PressBrief.brief_type == brief_type)
        .order_by(desc(PressBrief.generated_at)).limit(limit))
    briefs = result.scalars().all()
    return [
        {"id": b.id, "type": b.brief_type, "generated_at": b.generated_at.isoformat(),
         "coverage_count": b.coverage_count, "actionable_count": b.actionable_count,
         "content": b.content}
        for b in briefs
    ]


@router.get("/briefs/latest")
async def latest_brief(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PressBrief).where(PressBrief.brief_type == "daily")
        .order_by(desc(PressBrief.generated_at)).limit(1))
    brief = result.scalar_one_or_none()
    if not brief:
        raise HTTPException(status_code=404, detail="No briefs generated yet.")
    return {"id": brief.id, "generated_at": brief.generated_at.isoformat(),
            "coverage_count": brief.coverage_count, "actionable_count": brief.actionable_count,
            "content": brief.content}


@router.get("/follow-ups")
async def follow_ups_due(days_ahead: int = Query(14), db: AsyncSession = Depends(get_db)):
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    stmt = select(TargetJournalist).where(
        TargetJournalist.follow_up_date.isnot(None),
        TargetJournalist.pitch_status.in_(["pitched", "follow_up_due"]),
        TargetJournalist.follow_up_date <= cutoff,
    ).order_by(TargetJournalist.follow_up_date.asc())
    result = await db.execute(stmt)
    journalists = result.scalars().all()
    return [
        {"id": j.id, "name": j.name, "email": j.email, "publication": j.publication,
         "follow_up_date": j.follow_up_date.isoformat(),
         "days_until": (j.follow_up_date - today).days, "notes": j.notes}
        for j in journalists
    ]


def _run_scan(fn_name: str):
    from app.agents.press_monitor import scan_coverage, scan_journalists, generate_brief
    fns = {"coverage": scan_coverage, "journalists": scan_journalists, "brief": generate_brief}
    fns[fn_name]()


@router.post("/scan/coverage")
async def trigger_coverage_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(asyncio.to_thread, _run_scan, "coverage")
    return {"status": "queued", "scan": "coverage"}


@router.post("/scan/journalists")
async def trigger_journalist_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(asyncio.to_thread, _run_scan, "journalists")
    return {"status": "queued", "scan": "journalists"}


@router.post("/scan/brief")
async def trigger_brief_generation(background_tasks: BackgroundTasks):
    background_tasks.add_task(asyncio.to_thread, _run_scan, "brief")
    return {"status": "queued", "scan": "brief"}
