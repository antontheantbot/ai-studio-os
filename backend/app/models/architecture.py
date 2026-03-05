from sqlalchemy import Column, Text, Integer, ARRAY, String
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class ArchitectureLocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "architecture_locations"

    name        = Column(Text, nullable=False)
    description = Column(Text)
    architect   = Column(Text)
    city        = Column(Text)
    country     = Column(Text)
    style       = Column(Text)
    year_built  = Column(Integer)
    suitability = Column(ARRAY(String))   # photography | installation | performance
    image_urls  = Column(ARRAY(String))
    source_url  = Column(Text)
    embedding   = Column(Vector(1536))
