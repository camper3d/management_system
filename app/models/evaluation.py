from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer, nullable=False)

    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evaluated_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    task = relationship("Task", back_populates="evaluations")
    evaluator = relationship("User", foreign_keys=[evaluator_id])
    evaluated_user = relationship("User", foreign_keys=[evaluated_user_id])

    __table_args__ = (
        CheckConstraint('score >= 1 AND score <= 5', name='check_score_range'),
    )