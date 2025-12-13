from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.schemas.event_calendar import DayEventsResponse, MonthEventsResponse
from backend.crud.event_calendar import get_events_for_day, get_events_for_month

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/day", response_model=DayEventsResponse)
async def get_calendar_day(
    day: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if day:
        try:
            target_date = datetime.fromisoformat(day).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = date.today()

    events = await get_events_for_day(db, current_user.id, target_date)
    return {
        "date": target_date.isoformat(),
        "events": events
    }


@router.get("/month", response_model=MonthEventsResponse)
async def get_calendar_month(
    year: int | None = None,
    month: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()
    target_year = year or now.year
    target_month = month or now.month

    if not (1 <= target_month <= 12):
        raise HTTPException(status_code=400, detail="Month must be 1-12")

    events_by_day = await get_events_for_month(db, current_user.id, target_year, target_month)
    return {
        "year": target_year,
        "month": target_month,
        "days": events_by_day
    }