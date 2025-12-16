from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from backend.models.evaluation import Evaluation
from backend.models.task import Task, TaskStatus
from backend.models.user import User
from backend.schemas.evaluation import EvaluationCreate


async def create_evaluation(db: AsyncSession, evaluation_in: EvaluationCreate, evaluator_id: int) -> Evaluation:
    """
        Создать новую оценку для задачи.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
            evaluation_in (EvaluationCreate): Входные данные для оценки (task_id, score).
            evaluator_id (int): Идентификатор пользователя, который выставляет оценку.

        Returns:
            Evaluation: Созданный объект оценки.

        Raises:
            ValueError:
                - "Task not found": если задача не существует.
                - "Can only evaluate completed tasks": если задача не завершена.
                - "Evaluator not in the same team": если оценщик не состоит в той же команде.
                - "Only managers or admins can evaluate": если роль оценщика не admin/manager.
                - "Cannot evaluate yourself": если оценщик пытается оценить сам себя.
                - "Task already evaluated": если задача уже была оценена ранее.
        """

    task = await db.get(Task, evaluation_in.task_id)
    if not task:
        raise ValueError("Task not found")
    if task.status != TaskStatus.DONE:
        raise ValueError("Can only evaluate completed tasks")

    evaluator = await db.get(User, evaluator_id)
    if not evaluator or evaluator.team_id != task.team_id:
        raise ValueError("Evaluator not in the same team")
    if evaluator.role not in ("admin", "manager"):
        raise ValueError("Only managers or admins can evaluate")

    if evaluator_id == task.assignee_id:
        raise ValueError("Cannot evaluate yourself")

    existing = await db.execute(
        select(Evaluation).where(Evaluation.task_id == evaluation_in.task_id)
    )
    if existing.scalars().first():
        raise ValueError("Task already evaluated")

    evaluation = Evaluation(
        task_id=evaluation_in.task_id,
        score=evaluation_in.score,
        evaluator_id=evaluator_id,
        evaluated_user_id=task.assignee_id
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


async def get_user_evaluations(db: AsyncSession, user_id: int, team_id: int) -> list[Evaluation]:
    """
        Получить все оценки пользователя внутри команды.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            user_id (int): Идентификатор пользователя, для которого ищем оценки.
            team_id (int): Идентификатор команды.

        Returns:
            list[Evaluation]: Список оценок, выставленных пользователю за задачи его команды.
        """

    result = await db.execute(
        select(Evaluation)
        .where(
            and_(
                Evaluation.evaluated_user_id == user_id,
                Evaluation.task_id.in_(
                    select(Task.id).where(Task.team_id == team_id)
                )
            )
        )
    )
    return result.scalars().all()


async def get_average_rating(db: AsyncSession, user_id: int, team_id: int, days: int = 30) -> dict:
    """
        Рассчитать средний рейтинг пользователя за последние N дней.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            user_id (int): Идентификатор пользователя.
            team_id (int): Идентификатор команды.
            days (int, optional): Количество дней для анализа (по умолчанию 30).

        Returns:
            dict: Словарь с ключами:
                - "average_score" (float): средний балл.
                - "total_evaluations" (int): количество оценок за указанный период.
        """

    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(func.avg(Evaluation.score), func.count(Evaluation.id))
        .join(Task, Evaluation.task_id == Task.id)
        .where(
            and_(
                Evaluation.evaluated_user_id == user_id,
                Task.team_id == team_id,
                Evaluation.created_at >= since
            )
        )
    )
    avg, count = result.first()
    return {
        "average_score": float(avg) if avg else 0.0,
        "total_evaluations": count or 0
    }