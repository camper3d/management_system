from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from backend.models import User
from backend.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    admin = relationship("User", foreign_keys=[admin_id])
    members = relationship("User", back_populates="team", foreign_keys=[User.team_id])
    tasks = relationship("Task", back_populates="team")