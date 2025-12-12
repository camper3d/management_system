from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.evaluation import EvaluationCreate, EvaluationOut, AverageRatingResponse
from app.crud.evaluation import create_evaluation, get_user_evaluations, get_average_rating
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
async def add_evaluation(
        eval_in: EvaluationCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        evaluation = await create_evaluation(db, eval_in, current_user.id)
        await db.refresh(evaluation)
        return evaluation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=list[EvaluationOut])
async def get_my_evaluations(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.team_id is None:
        return []
    evaluations = await get_user_evaluations(db, current_user.id, current_user.team_id)
    return evaluations


@router.get("/me/average", response_model=AverageRatingResponse)
async def get_my_average_rating(
        days: int = Query(30, ge=1, le=365),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.team_id is None:
        return {"average_score": 0.0, "total_evaluations": 0}

    stats = await get_average_rating(db, current_user.id, current_user.team_id, days=days)
    return stats