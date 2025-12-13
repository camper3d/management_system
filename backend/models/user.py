from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.models.base import Base
import enum


class UserRole(str, enum.Enum):
    MEMBER = "member"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER)

    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])

    tasks_assigned = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    tasks_created = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")

    meetings = relationship("Meeting", secondary="meeting_participants", back_populates="participants")
    evaluations_given = relationship("Evaluation", foreign_keys="Evaluation.evaluator_id", back_populates="evaluator")