from sqlalchemy import Column, Text, ARRAY, String
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.base import Base, UUIDMixin, TimestampMixin


class Corporation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "corporations"

    name = Column(Text, nullable=False, unique=True)
    type = Column(Text)            # brand, agency, foundation, tech, gallery, etc.
    contact_name = Column(Text)    # primary contact person at the org
    contact_role = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    website = Column(Text)
    city = Column(Text)
    country = Column(Text)
    focus_areas = Column(ARRAY(String), default=[])
    tags = Column(ARRAY(String), default=[])
    notes = Column(Text)
    source = Column(Text)          # how / when discovered
    social_links = Column(JSONB, default={})
    embedding = Column(Vector(1536))
