from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.meeting import MeetingCreate, MeetingOut
from app.crud.meeting import create_meeting, get_user_meetings, delete_meeting
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
async def create_new_meeting(
        meeting_in: MeetingCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.team_id is None:
        raise HTTPException(status_code=400, detail="You must be in a team")

    if current_user.id not in meeting_in.participant_ids:
        meeting_in.participant_ids.append(current_user.id)

    try:
        meeting = await create_meeting(db, meeting_in, current_user.id, current_user.team_id)
        await db.refresh(meeting, ["creator", "participants"])
        return meeting
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[MeetingOut])
async def list_my_meetings(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    meetings = await get_user_meetings(db, current_user.id)
    for m in meetings:
        await db.refresh(m, ["creator", "participants"])
    return meetings


@router.delete("/{meeting_id}")
async def cancel_meeting(
        meeting_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.team_id is None:
        raise HTTPException(status_code=400, detail="You must be in a team")

    success = await delete_meeting(db, meeting_id, current_user.id, current_user.team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found or access denied")

    return {"message": "Meeting cancelled"}