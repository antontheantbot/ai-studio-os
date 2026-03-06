from sqlalchemy import Column, Text, Date, Integer, UniqueConstraint
from app.db.base import Base, UUIDMixin, TimestampMixin


class DailyAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "daily_actions"
    __table_args__ = (UniqueConstraint("date", name="daily_actions_date_unique"),)

    date = Column(Date, nullable=False)
    goal_index = Column(Integer, nullable=False)
    goal_name = Column(Text)
    content = Column(Text)   # full Claude-generated action text
