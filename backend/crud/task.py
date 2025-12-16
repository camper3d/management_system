from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from backend.models.task import Task, TaskStatus
from backend.models.comment import Comment
from backend.schemas.task import TaskCreate


async def create_task(db: AsyncSession, task_in: TaskCreate, creator_id: int, team_id: int) -> Task:
    """
        Создать новую задачу в команде.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            task_in (TaskCreate): Входные данные для задачи (заголовок, описание, дедлайн, assignee_id).
            creator_id (int): Идентификатор пользователя, создавшего задачу.
            team_id (int): Идентификатор команды.

        Returns:
            Task: Созданный объект задачи.
        """

    task = Task(
        title=task_in.title,
        description=task_in.description,
        deadline=task_in.deadline,
        status=TaskStatus.OPEN,
        team_id=team_id,
        assignee_id=task_in.assignee_id,
        creator_id=creator_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task_by_id(db: AsyncSession, task_id: int) -> Task | None:
    """
        Получить задачу по её идентификатору.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            task_id (int): Идентификатор задачи.

        Returns:
            Task | None: Объект задачи, если найден, иначе None.
        """

    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalars().first()


async def get_tasks_for_user(db: AsyncSession, user_id: int, team_id: int) -> list[Task]:
    """
        Получить список задач для пользователя в рамках команды.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            user_id (int): Идентификатор пользователя.
            team_id (int): Идентификатор команды.

        Returns:
            list[Task]: Список задач, где пользователь является создателем или исполнителем.
        """

    result = await db.execute(
        select(Task).where(
            and_(Task.team_id == team_id, Task.creator_id == user_id) |
            and_(Task.team_id == team_id, Task.assignee_id == user_id)
        )
    )
    return result.scalars().all()


async def update_task(db: AsyncSession, task: Task, update_data: dict) -> Task:
    """
        Обновить данные существующей задачи.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            task (Task): Объект задачи для обновления.
            update_data (dict): Словарь с новыми значениями полей.

        Returns:
            Task: Обновлённый объект задачи.
        """

    for field, value in update_data.items():
        if value is not None:
            setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    """
        Удалить задачу.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            task (Task): Объект задачи для удаления.

        Returns:
            None
        """

    await db.delete(task)
    await db.commit()


# Комментарии

async def create_comment(db: AsyncSession, task_id: int, author_id: int, content: str) -> Comment:
    """
        Создать комментарий к задаче.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            task_id (int): Идентификатор задачи.
            author_id (int): Идентификатор автора комментария.
            content (str): Текст комментария.

        Returns:
            Comment: Созданный объект комментария.
        """

    comment = Comment(task_id=task_id, author_id=author_id, content=content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_comments_for_task(db: AsyncSession, task_id: int) -> list[Comment]:
    """
        Получить все комментарии для задачи.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            task_id (int): Идентификатор задачи.

        Returns:
            list[Comment]: Список комментариев для указанной задачи.
        """

    result = await db.execute(select(Comment).where(Comment.task_id == task_id))
    return result.scalars().all()