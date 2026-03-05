from sqlalchemy import Column, Text, Date, JSON, UniqueConstraint
from app.db.base import Base, UUIDMixin, TimestampMixin


class ColorSizeTrend(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "color_size_trends"
    __table_args__ = (UniqueConstraint("week_of", name="color_size_trends_week_of_unique"),)

    week_of = Column(Date, nullable=False)
    popular_colors = Column(JSON, default=list)   # [{name, hex, trend, context}]
    popular_sizes = Column(JSON, default=list)    # [{label, dimensions, medium, trend, context}]
    summary = Column(Text)
    sources = Column(JSON, default=list)
