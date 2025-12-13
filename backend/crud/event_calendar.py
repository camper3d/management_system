from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date
from calendar import monthrange
from backend.models.task import Task
from backend.models.meeting import Meeting, meeting_participants


async def get_events_for_day(db: AsyncSession, user_id: int, target_date: date) -> list:
    events = []

    task_result = await db.execute(
        select(Task).where(
            ((Task.assignee_id == user_id) | (Task.creator_id == user_id)) &
            (Task.deadline.isnot(None)) &
            (Task.deadline.cast(date) == target_date)
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

    meeting_result = await db.execute(
        select(Meeting)
        .join(meeting_participants)
        .where(
            meeting_participants.c.user_id == user_id,
            Meeting.start_time.cast(date) == target_date
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
    _, last_day = monthrange(year, month)
    events_by_day = {}

    for day in range(1, last_day + 1):
        target_date = date(year, month, day)
        key = target_date.isoformat()
        events_by_day[key] = await get_events_for_day(db, user_id, target_date)

    return events_by_day