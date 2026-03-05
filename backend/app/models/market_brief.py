from sqlalchemy import Column, Text, Date, JSON, UniqueConstraint
from app.db.base import Base, UUIDMixin, TimestampMixin


class MarketBrief(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "market_briefs"
    __table_args__ = (UniqueConstraint("week_of", name="market_briefs_week_of_unique"),)

    week_of = Column(Date, nullable=False)
    title = Column(Text, nullable=False)
    signals = Column(JSON, default=list)      # raw market signals
    trends = Column(JSON, default=list)       # structured trend objects
    top_artists = Column(JSON, default=list)  # trending artist names
    top_mediums = Column(JSON, default=list)  # trending mediums
    brief = Column(Text)                      # generated creative brief
    sources = Column(JSON, default=list)      # source URLs used
