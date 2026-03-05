from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class Proposal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "proposals"

    title          = Column(Text, nullable=False)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    content        = Column(Text, nullable=False)
    status         = Column(Text, default="draft")   # draft | submitted | accepted | rejected
    submitted_at   = Column(DateTime(timezone=True))
    response_at    = Column(DateTime(timezone=True))
    notes          = Column(Text)
    embedding      = Column(Vector(1536))
