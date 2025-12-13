from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base
from sqlalchemy import Table


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column("meeting_id", Integer, ForeignKey("meetings.id")),
    Column("user_id", Integer, ForeignKey("users.id")),
)


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", foreign_keys=[creator_id])

    participants = relationship("User", secondary=meeting_participants, back_populates="meetings")