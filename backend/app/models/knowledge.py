from sqlalchemy import Column, Text, ARRAY, String
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class KnowledgeItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_items"

    title       = Column(Text, nullable=False)
    content     = Column(Text, nullable=False)
    summary     = Column(Text)
    source_type = Column(Text, nullable=False)   # note | article | pdf | url | reference
    source_url  = Column(Text)
    author      = Column(Text)
    tags        = Column(ARRAY(String))
    embedding   = Column(Vector(1536))
