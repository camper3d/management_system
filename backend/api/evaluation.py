from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.schemas.evaluation import EvaluationCreate, EvaluationOut, AverageRatingResponse
from backend.crud.evaluation import create_evaluation, get_user_evaluations, get_average_rating
from backend.api.deps import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
async def add_evaluation(
        eval_in: EvaluationCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Создать новую оценку для текущего пользователя.

    Args:
        eval_in (EvaluationCreate): Данные для создания оценки (входная схема).
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
        current_user (User): Текущий пользователь, полученный из JWT‑токена.

    Returns:
        EvaluationOut: Объект созданной оценки.

    Raises:
        HTTPException: Если входные данные некорректны (ValueError → 400).
    """

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
    """
    Получить список всех оценок, связанных с текущим пользователем.

    Args:
        db (AsyncSession): Асинхронная сессия SQLAlchemy.
        current_user (User): Текущий пользователь.

    Returns:
        list[EvaluationOut]: Список оценок пользователя.
                             Если пользователь не состоит в команде, возвращается пустой список.
    """

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
    """
    Получить средний рейтинг текущего пользователя за последние N дней.

    Args:
        days (int): Количество дней для расчёта среднего рейтинга (по умолчанию 30, от 1 до 365).
        db (AsyncSession): Асинхронная сессия SQLAlchemy.
        current_user (User): Текущий пользователь.

    Returns:
        AverageRatingResponse: Средний балл и количество оценок.
                               Если пользователь не состоит в команде, возвращается
                               {"average_score": 0.0, "total_evaluations": 0}.
    """

    if current_user.team_id is None:
        return {"average_score": 0.0, "total_evaluations": 0}

    stats = await get_average_rating(db, current_user.id, current_user.team_id, days=days)
    return stats