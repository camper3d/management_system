from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.models.base import Base
import enum


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)

    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    team = relationship("Team", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="tasks_assigned")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="tasks_created")

    comments = relationship("Comment", back_populates="task")
    evaluations = relationship("Evaluation", back_populates="task")