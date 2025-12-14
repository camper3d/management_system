from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, DateTime, text
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer, nullable=False)

    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evaluated_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False)

    task = relationship("Task", back_populates="evaluations")
    evaluator = relationship("User", foreign_keys=[evaluator_id])
    evaluated_user = relationship("User", foreign_keys=[evaluated_user_id])

    __table_args__ = (
        CheckConstraint('score >= 1 AND score <= 5', name='check_score_range'),
    )