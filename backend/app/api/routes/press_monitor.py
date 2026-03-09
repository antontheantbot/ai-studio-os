"""Press Monitor v2 API Routes"""

from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.press_monitor import (
    CoverageMention, TargetJournalist, JournalistArticle, PressBrief
)

router = APIRouter()


@router.get("/coverage")
def list_coverage(
    days: int = Query(7, ge=1, le=90),
    sentiment: Optional[str] = Query(None),
    tier: Optional[int] = Query(None, ge=1, le=4),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    q = db.query(CoverageMention).filter(CoverageMention.discovered_at >= since)
    if sentiment: q = q.filter(CoverageMention.sentiment == sentiment)
    if tier: q = q.filter(CoverageMention.publication_tier == tier)
    mentions = q.order_by(desc(CoverageMention.discovered_at)).limit(limit).all()
    return {"count": len(mentions), "mentions": [
        {"id": m.id, "source": m.source, "title": m.title, "url": m.url,
         "summary": m.summary, "sentiment": m.sentiment, "subjects": m.subjects,
         "tier": m.publication_tier,
         "published_at": m.published_at.isoformat() if m.published_at else None,
         "discovered_at": m.discovered_at.isoformat() if m.discovered_at else None}
        for m in mentions
    ]}


@router.get("/coverage/stats")
def coverage_stats(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    mentions = db.query(CoverageMention).filter(CoverageMention.discovered_at >= since).all()
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
def list_journalists(
    status: Optional[str] = Query(None),
    tier: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
):
    q = db.query(TargetJournalist)
    if status: q = q.filter(TargetJournalist.pitch_status == status)
    if tier: q = q.filter(TargetJournalist.tier == tier)
    journalists = q.order_by(TargetJournalist.tier.asc(), TargetJournalist.name.asc()).all()
    return {"count": len(journalists), "journalists": [
        {"id": j.id, "name": j.name, "email": j.email, "publication": j.publication,
         "role": j.role, "beat": j.beat, "tier": j.tier,
         "pitch_status": j.pitch_status,
         "follow_up_date": j.follow_up_date.isoformat() if j.follow_up_date else None,
         "last_pitched_at": j.last_pitched_at.isoformat() if j.last_pitched_at else None,
         "notes": j.notes,
         "article_count": len(j.articles) if j.articles else 0,
         "actionable_count": sum(1 for a in (j.articles or []) if a.is_actionable and not a.actioned)}
        for j in journalists
    ]}


@router.post("/journalists")
def add_journalist(
    name: str, publication: str, email: Optional[str] = None,
    role: Optional[str] = None, beat: Optional[list] = None,
    tier: int = 2, notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    existing = db.query(TargetJournalist).filter(
        TargetJournalist.name == name, TargetJournalist.publication == publication).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"{name} at {publication} already exists.")
    journalist = TargetJournalist(name=name, email=email, publication=publication,
                                  role=role, beat=beat or [], tier=tier, notes=notes)
    db.add(journalist)
    db.commit()
    db.refresh(journalist)
    return {"id": journalist.id, "name": journalist.name, "publication": journalist.publication}


@router.patch("/journalists/{journalist_id}")
def update_journalist(
    journalist_id: int, email: Optional[str] = None,
    pitch_status: Optional[str] = None, follow_up_date: Optional[str] = None,
    notes: Optional[str] = None, db: Session = Depends(get_db),
):
    j = db.query(TargetJournalist).get(journalist_id)
    if not j: raise HTTPException(status_code=404, detail="Journalist not found.")
    if email is not None: j.email = email
    if pitch_status is not None:
        j.pitch_status = pitch_status
        if pitch_status == "pitched": j.last_pitched_at = datetime.utcnow()
    if follow_up_date is not None:
        j.follow_up_date = date.fromisoformat(follow_up_date) if follow_up_date else None
    if notes is not None: j.notes = notes
    j.updated_at = datetime.utcnow()
    db.commit()
    return {"updated": True, "id": j.id}


@router.get("/opportunities")
def list_opportunities(
    actionable_only: bool = Query(True),
    min_relevance: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(JournalistArticle).join(TargetJournalist)
    if actionable_only:
        q = q.filter(JournalistArticle.is_actionable == True, JournalistArticle.actioned == False)
    q = q.filter(JournalistArticle.relevance_score >= min_relevance)
    articles = q.order_by(desc(JournalistArticle.relevance_score)).limit(limit).all()
    return {"count": len(articles), "opportunities": [
        {"id": a.id,
         "journalist": a.journalist.name if a.journalist else "Unknown",
         "journalist_email": a.journalist.email if a.journalist else None,
         "publication": a.journalist.publication if a.journalist else "Unknown",
         "article_title": a.title, "article_url": a.url, "summary": a.summary,
         "themes": a.themes, "relevance_score": a.relevance_score,
         "warm_angle": a.warm_angle, "is_actionable": a.is_actionable,
         "actioned": a.actioned,
         "discovered_at": a.discovered_at.isoformat() if a.discovered_at else None}
        for a in articles
    ]}


@router.post("/opportunities/{article_id}/action")
def mark_actioned(article_id: int, db: Session = Depends(get_db)):
    article = db.query(JournalistArticle).get(article_id)
    if not article: raise HTTPException(status_code=404, detail="Article not found.")
    article.actioned = True
    db.commit()
    return {"actioned": True, "id": article.id}


@router.get("/briefs")
def list_briefs(brief_type: str = Query("daily"), limit: int = Query(7, ge=1, le=30),
                db: Session = Depends(get_db)):
    briefs = db.query(PressBrief).filter(
        PressBrief.brief_type == brief_type
    ).order_by(desc(PressBrief.generated_at)).limit(limit).all()
    return {"count": len(briefs), "briefs": [
        {"id": b.id, "type": b.brief_type, "generated_at": b.generated_at.isoformat(),
         "coverage_count": b.coverage_count, "actionable_count": b.actionable_count,
         "content": b.content}
        for b in briefs
    ]}


@router.get("/briefs/latest")
def latest_brief(db: Session = Depends(get_db)):
    brief = db.query(PressBrief).filter(
        PressBrief.brief_type == "daily"
    ).order_by(desc(PressBrief.generated_at)).first()
    if not brief: raise HTTPException(status_code=404, detail="No briefs generated yet.")
    return {"id": brief.id, "generated_at": brief.generated_at.isoformat(),
            "coverage_count": brief.coverage_count, "actionable_count": brief.actionable_count,
            "content": brief.content}


@router.get("/follow-ups")
def follow_ups_due(include_past: bool = Query(True), db: Session = Depends(get_db)):
    today = date.today()
    q = db.query(TargetJournalist).filter(
        TargetJournalist.follow_up_date.isnot(None),
        TargetJournalist.pitch_status.in_(["pitched", "follow_up_due"]))
    if include_past: q = q.filter(TargetJournalist.follow_up_date <= today)
    else: q = q.filter(TargetJournalist.follow_up_date == today)
    journalists = q.order_by(TargetJournalist.follow_up_date.asc()).all()
    return {"count": len(journalists), "follow_ups": [
        {"id": j.id, "name": j.name, "email": j.email, "publication": j.publication,
         "follow_up_date": j.follow_up_date.isoformat(),
         "days_overdue": (today - j.follow_up_date).days, "notes": j.notes}
        for j in journalists
    ]}


@router.post("/scan/coverage")
def trigger_coverage_scan():
    from app.agents.press_monitor import scan_coverage
    result = scan_coverage.delay()
    return {"task_id": str(result.id), "status": "queued"}


@router.post("/scan/journalists")
def trigger_journalist_scan():
    from app.agents.press_monitor import scan_journalists
    result = scan_journalists.delay()
    return {"task_id": str(result.id), "status": "queued"}


@router.post("/scan/brief")
def trigger_brief_generation():
    from app.agents.press_monitor import generate_brief
    result = generate_brief.delay()
    return {"task_id": str(result.id), "status": "queued"}
