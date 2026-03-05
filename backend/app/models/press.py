from sqlalchemy import Column, Text, ARRAY, String, DateTime
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class PressItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "press_items"

    title            = Column(Text, nullable=False)
    content          = Column(Text)
    summary          = Column(Text)
    source           = Column(Text)
    author           = Column(Text)
    url              = Column(Text, unique=True)
    published_at     = Column(DateTime(timezone=True))
    category         = Column(Text)     # exhibition | review | news | interview
    tags             = Column(ARRAY(String))
    mentioned_artists = Column(ARRAY(String))
    embedding        = Column(Vector(1536))
