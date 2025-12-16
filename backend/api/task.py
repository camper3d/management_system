from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.schemas.task import TaskCreate, TaskUpdate, TaskOut, CommentCreate, CommentOut
from backend.crud.task import create_task, get_task_by_id, get_tasks_for_user,\
    update_task, delete_task, create_comment, get_comments_for_task
from backend.api.deps import get_current_user
from backend.models.user import User, UserRole
from backend.models.task import TaskStatus


router = APIRouter(prefix="/tasks", tags=["tasks"])


def validate_role_for_task_management(current_user: User):
    """
    Проверяет, имеет ли текущий пользователь права на управление задачами.

    Args:
        current_user (User): Текущий пользователь.

    Raises:
        HTTPException: Если роль пользователя не ADMIN или MANAGER (403).
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Only managers or admins can manage tasks")


@router.post("/", response_model=TaskOut)
async def create_new_task(
        task_in: TaskCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Создать новую задачу в команде.

    Args:
        task_in (TaskCreate): Входные данные для создания задачи.
        db (AsyncSession): Асинхронная сессия SQLAlchemy.
        current_user (User): Текущий пользователь.

    Returns:
        TaskOut: Объект созданной задачи с комментариями.

    Raises:
        HTTPException:
            - 400: Если пользователь не состоит в команде или назначенный исполнитель вне команды.
            - 403: Если роль пользователя не позволяет управлять задачами.
    """

    validate_role_for_task_management(current_user)

    if current_user.team_id is None:
        raise HTTPException(status_code=400, detail="You must be in a team")

    assignee = await db.get(User, task_in.assignee_id)
    if not assignee or assignee.team_id != current_user.team_id:
        raise HTTPException(status_code=400, detail="Assignee must be in your team")

    task = await create_task(db, task_in, current_user.id, current_user.team_id)

    await db.refresh(task, ["creator", "assignee"])
    comments = await get_comments_for_task(db, task.id)
    task.comments = comments

    return task


@router.get("/", response_model=list[TaskOut])
async def list_my_tasks(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Получить список всех задач текущего пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            list[TaskOut]: Список задач с комментариями.
        """

    if current_user.team_id is None:
        return []
    tasks = await get_tasks_for_user(db, current_user.id, current_user.team_id)
    for task in tasks:
        await db.refresh(task, ["creator", "assignee"])
        task.comments = await get_comments_for_task(db, task.id)
    return tasks


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Получить задачу по её идентификатору.

        Args:
            task_id (int): Идентификатор задачи.
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            TaskOut: Объект задачи с комментариями.

        Raises:
            HTTPException:
                - 404: Если задача не найдена или принадлежит другой команде.
        """

    task = await get_task_by_id(db, task_id)
    if not task or task.team_id != current_user.team_id:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.refresh(task, ["creator", "assignee"])
    task.comments = await get_comments_for_task(db, task.id)
    return task


@router.put("/{task_id}", response_model=TaskOut)
async def update_existing_task(
        task_id: int,
        task_update: TaskUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Обновить существующую задачу.

        Args:
            task_id (int): Идентификатор задачи.
            task_update (TaskUpdate): Данные для обновления задачи.
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            TaskOut: Обновлённая задача с комментариями.

        Raises:
            HTTPException:
                - 400: Если статус некорректен.
                - 403: Если роль пользователя не позволяет управлять задачами.
                - 404: Если задача не найдена или принадлежит другой команде.
        """

    validate_role_for_task_management(current_user)

    task = await get_task_by_id(db, task_id)
    if not task or task.team_id != current_user.team_id:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_update.status and task_update.status not in [s.value for s in TaskStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")

    update_data = task_update.dict(exclude_unset=True)
    task = await update_task(db, task, update_data)

    await db.refresh(task, ["creator", "assignee"])
    task.comments = await get_comments_for_task(db, task.id)
    return task


@router.delete("/{task_id}")
async def delete_existing_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Удалить задачу по её идентификатору.

        Args:
            task_id (int): Идентификатор задачи.
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            dict: Сообщение об успешном удалении {"message": "Task deleted"}.

        Raises:
            HTTPException:
                - 403: Если пользователь не является создателем задачи.
                - 404: Если задача не найдена.
        """

    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only task creator can delete it")

    await delete_task(db, task)
    return {"message": "Task deleted"}


# Комментарии

@router.post("/{task_id}/comments", response_model=CommentOut)
async def add_comment_to_task(
        task_id: int,
        comment_in: CommentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
        Добавить комментарий к задаче.

        Args:
            task_id (int): Идентификатор задачи.
            comment_in (CommentCreate): Данные комментария (текст).
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            current_user (User): Текущий пользователь.

        Returns:
            CommentOut: Созданный комментарий с информацией об авторе.

        Raises:
            HTTPException:
                - 404: Если задача не найдена или принадлежит другой команде.
        """

    task = await get_task_by_id(db, task_id)
    if not task or task.team_id != current_user.team_id:
        raise HTTPException(status_code=404, detail="Task not found")

    comment = await create_comment(db, task_id, current_user.id, comment_in.content)
    await db.refresh(comment, ["author"])
    return comment