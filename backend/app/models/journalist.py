from sqlalchemy import Column, Text, JSON, UniqueConstraint
from app.db.base import Base, UUIDMixin, TimestampMixin


class Journalist(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "journalists"
    __table_args__ = (UniqueConstraint("name", name="journalists_name_unique"),)

    name = Column(Text, nullable=False)
    bio = Column(Text)
    publications = Column(JSON, default=list)   # ["Artforum", "Frieze", "NYT"]
    beats = Column(JSON, default=list)          # ["contemporary art", "architecture", "photography"]
    email = Column(Text)
    social_links = Column(JSON, default=dict)   # {twitter, instagram, linkedin, website}
    location = Column(Text)
    country = Column(Text)
    notes = Column(Text)
