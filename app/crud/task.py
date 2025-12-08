from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models.task import Task, TaskStatus
from app.models.comment import Comment
from app.schemas.task import TaskCreate


async def create_task(db: AsyncSession, task_in: TaskCreate, creator_id: int, team_id: int) -> Task:
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
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalars().first()


async def get_tasks_for_user(db: AsyncSession, user_id: int, team_id: int) -> list[Task]:
    result = await db.execute(
        select(Task).where(
            and_(Task.team_id == team_id, Task.creator_id == user_id) |
            and_(Task.team_id == team_id, Task.assignee_id == user_id)
        )
    )
    return result.scalars().all()


async def update_task(db: AsyncSession, task: Task, update_data: dict) -> Task:
    for field, value in update_data.items():
        if value is not None:
            setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()


# Комментарии

async def create_comment(db: AsyncSession, task_id: int, author_id: int, content: str) -> Comment:
    comment = Comment(task_id=task_id, author_id=author_id, content=content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_comments_for_task(db: AsyncSession, task_id: int) -> list[Comment]:
    result = await db.execute(select(Comment).where(Comment.task_id == task_id))
    return result.scalars().all()