from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.models.meeting import Meeting, meeting_participants
from app.models.user import User
from app.schemas.meeting import MeetingCreate
from datetime import datetime


async def user_has_conflict(db: AsyncSession, user_id: int, start: datetime, end: datetime) -> bool:
    query = select(Meeting).join(meeting_participants).where(
        and_(
            meeting_participants.c.user_id == user_id,
            or_(
                and_(Meeting.start_time < end, Meeting.end_time > start),
                and_(Meeting.start_time == start, Meeting.end_time == end)
            )
        )
    )
    result = await db.execute(query)
    return result.scalars().first() is not None


async def create_meeting(db: AsyncSession, meeting_in: MeetingCreate, creator_id: int, team_id: int) -> Meeting:
    if meeting_in.start_time >= meeting_in.end_time:
        raise ValueError("End time must be after start time")

    participants = []
    for user_id in meeting_in.participant_ids:
        user = await db.get(User, user_id)
        if not user or user.team_id != team_id:
            raise ValueError(f"User {user_id} not in your team or not found")
        participants.append(user)

    for user in participants:
        if await user_has_conflict(db, user.id, meeting_in.start_time, meeting_in.end_time):
            raise ValueError(f"User {user.id} has a conflicting meeting")

    meeting = Meeting(
        title=meeting_in.title,
        start_time=meeting_in.start_time,
        end_time=meeting_in.end_time,
        creator_id=creator_id
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    stmt = meeting_participants.insert().values([
        {"meeting_id": meeting.id, "user_id": user.id} for user in participants
    ])
    await db.execute(stmt)
    await db.commit()

    return meeting


async def get_user_meetings(db: AsyncSession, user_id: int) -> list[Meeting]:
    result = await db.execute(
        select(Meeting)
        .join(meeting_participants)
        .where(meeting_participants.c.user_id == user_id)
        .order_by(Meeting.start_time)
    )
    return result.scalars().all()


async def delete_meeting(db: AsyncSession, meeting_id: int, user_id: int, team_id: int) -> bool:
    meeting = await db.get(Meeting, meeting_id)
    if not meeting:
        return False

    creator = await db.get(User, meeting.creator_id)
    if not creator or creator.team_id != team_id:
        return False

    user = await db.get(User, user_id)
    if not user:
        return False

    if user.id == meeting.creator_id or user.role == "admin":
        await db.delete(meeting)
        await db.commit()
        return True
    return False