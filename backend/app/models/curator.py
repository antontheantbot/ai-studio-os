from sqlalchemy import Column, Text, ARRAY, String
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class Curator(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "curators"

    name          = Column(Text, nullable=False)
    bio           = Column(Text)
    institution   = Column(Text)
    role          = Column(Text)
    location      = Column(Text)
    country       = Column(Text)
    focus_areas   = Column(ARRAY(String))
    notable_shows = Column(ARRAY(String))
    contact_email = Column(Text)
    contact_url   = Column(Text)
    social_links  = Column(JSONB)
    notes         = Column(Text)
    embedding     = Column(Vector(1536))
