from pydantic import BaseModel, Field
from datetime import datetime


class EvaluationCreate(BaseModel):
    task_id: int
    score: int = Field(..., ge=1, le=5)


class EvaluationOut(BaseModel):
    id: int
    task_id: int
    score: int
    evaluator_id: int
    evaluated_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AverageRatingResponse(BaseModel):
    average_score: float
    total_evaluations: int