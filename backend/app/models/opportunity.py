from sqlalchemy import Column, Text, Date, Boolean, ARRAY, String
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class Opportunity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "opportunities"

    title       = Column(Text, nullable=False)
    description = Column(Text)
    category    = Column(Text)          # open_call | residency | commission | festival
    organizer   = Column(Text)
    location    = Column(Text)
    country     = Column(Text)
    deadline    = Column(Date)
    fee         = Column(Text)
    award       = Column(Text)
    url         = Column(Text, unique=True)
    tags        = Column(ARRAY(String))
    is_active   = Column(Boolean, default=True)
    embedding   = Column(Vector(1536))
