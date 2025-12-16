from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Date
from datetime import datetime, time, date
from calendar import monthrange
from backend.models.task import Task
from backend.models.meeting import Meeting, meeting_participants


async def get_events_for_day(db: AsyncSession, user_id: int, target_date: date) -> list:
    """
        Получить список событий (задачи и встречи) для конкретного пользователя за указанный день.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
            user_id (int): Идентификатор пользователя, для которого ищем события.
            target_date (date): Целевая дата (год-месяц-день).

        Returns:
            list: Список словарей с событиями. Каждый словарь содержит:
                - id (int): идентификатор события
                - title (str): заголовок события ("Задача: ..." или "Встреча: ...")
                - type (str): тип события ("task" или "meeting")
                - start (datetime): время начала
                - end (datetime): время окончания
                - assignee_id (int, optional): назначенный исполнитель (для задач)
                - creator_id (int): создатель события
        """

    events = []

    task_result = await db.execute(
        select(Task).where(
            ((Task.assignee_id == user_id) | (Task.creator_id == user_id)) &
            (Task.deadline.isnot(None)) &
            (Task.deadline.cast(Date) == target_date)
        )
    )
    for task in task_result.scalars():
        events.append({
            "id": task.id,
            "title": f"Задача: {task.title}",
            "type": "task",
            "start": task.deadline,
            "end": task.deadline,
            "assignee_id": task.assignee_id,
            "creator_id": task.creator_id
        })

    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    meeting_result = await db.execute(
        select(Meeting)
        .join(meeting_participants)
        .where(
            meeting_participants.c.user_id == user_id,
            Meeting.start_time >= start_of_day,
            Meeting.start_time <= end_of_day
        )
    )
    for meeting in meeting_result.scalars():
        events.append({
            "id": meeting.id,
            "title": f"Встреча: {meeting.title}",
            "type": "meeting",
            "start": meeting.start_time,
            "end": meeting.end_time,
            "creator_id": meeting.creator_id
        })

    events.sort(key=lambda e: e["start"])
    return events


async def get_events_for_month(db: AsyncSession, user_id: int, year: int, month: int) -> dict[str, list]:
    """
        Получить все события пользователя за указанный месяц.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
            user_id (int): Идентификатор пользователя.
            year (int): Год.
            month (int): Месяц (1–12).

        Returns:
            dict[str, list]: Словарь, где ключ — дата в формате ISO (YYYY-MM-DD),
            а значение — список событий за этот день (см. get_events_for_day).
        """

    _, last_day = monthrange(year, month)
    events_by_day = {}

    for day in range(1, last_day + 1):
        target_date = date(year, month, day)
        key = target_date.isoformat()
        events_by_day[key] = await get_events_for_day(db, user_id, target_date)

    return events_by_day