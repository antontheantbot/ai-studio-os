from sqlalchemy import Column, Text, ARRAY, String
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class Collector(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "collectors"

    name         = Column(Text, nullable=False)
    bio          = Column(Text)
    location     = Column(Text)
    country      = Column(Text)
    interests    = Column(ARRAY(String))
    known_works  = Column(ARRAY(String))
    institutions = Column(ARRAY(String))
    contact_email = Column(Text)
    contact_url  = Column(Text)
    social_links = Column(JSONB)
    notes        = Column(Text)
    embedding    = Column(Vector(1536))
