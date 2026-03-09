"""Press Monitor v2 Models"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Date,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from app.db.base import Base


class CoverageMention(Base):
    __tablename__ = "coverage_mentions"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(Text, nullable=False)
    title = Column(Text)
    url = Column(Text, unique=True)
    summary = Column(Text)
    sentiment = Column(String(10), default="neutral")
    subjects = Column(ARRAY(Text), default=[])
    published_at = Column(DateTime(timezone=True))
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    publication_tier = Column(Integer, default=3)
    embedding = Column(Vector(1536))
    __table_args__ = (
        CheckConstraint("sentiment IN ('positive', 'neutral', 'negative')"),
        CheckConstraint("publication_tier BETWEEN 1 AND 4"),
        Index("idx_coverage_published", "published_at"),
    )


class TargetJournalist(Base):
    __tablename__ = "target_journalists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    email = Column(Text)
    publication = Column(Text, nullable=False)
    role = Column(Text)
    beat = Column(ARRAY(Text), default=[])
    tier = Column(Integer, default=2)
    last_pitched_at = Column(DateTime(timezone=True))
    pitch_status = Column(String(20), default="not_pitched")
    follow_up_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    journalist_id = Column(UUID(as_uuid=True), ForeignKey("journalists.id", ondelete="SET NULL"), nullable=True)
    contact = relationship("Journalist", foreign_keys=[journalist_id])
    articles = relationship("JournalistArticle", back_populates="journalist", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("name", "publication", name="uq_journalist_publication"),
        CheckConstraint("tier BETWEEN 1 AND 4"),
        CheckConstraint(
            "pitch_status IN ('not_pitched', 'pitched', 'follow_up_due', 'in_discussion', 'declined', 'published')"
        ),
        Index("idx_journalist_followup", "follow_up_date"),
        Index("idx_journalist_status", "pitch_status"),
    )


class JournalistArticle(Base):
    __tablename__ = "journalist_articles"
    id = Column(Integer, primary_key=True, index=True)
    journalist_id = Column(Integer, ForeignKey("target_journalists.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True)
    summary = Column(Text)
    published_at = Column(DateTime(timezone=True))
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    themes = Column(ARRAY(Text), default=[])
    relevance_score = Column(Float, default=0.0)
    warm_angle = Column(Text)
    is_actionable = Column(Boolean, default=False)
    actioned = Column(Boolean, default=False)
    embedding = Column(Vector(1536))
    journalist = relationship("TargetJournalist", back_populates="articles")
    __table_args__ = (
        Index("idx_jarticle_actionable", "is_actionable", postgresql_where="is_actionable = true"),
        Index("idx_jarticle_relevance", "relevance_score"),
    )


class PressBrief(Base):
    __tablename__ = "press_briefs"
    id = Column(Integer, primary_key=True, index=True)
    brief_type = Column(String(10), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    coverage_count = Column(Integer, default=0)
    actionable_count = Column(Integer, default=0)
    content = Column(JSONB, nullable=False)
    __table_args__ = (
        CheckConstraint("brief_type IN ('daily', 'weekly')"),
        Index("idx_brief_type_date", "brief_type", "generated_at"),
    )
