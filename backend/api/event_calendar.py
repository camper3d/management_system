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
    """
    Получить события текущего пользователя за конкретный день календаря.

    Args:
        day (str | None): Дата в формате ISO (YYYY-MM-DD).
                          Если не указана, используется текущая дата.
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
        current_user (User): Текущий пользователь, полученный из JWT‑токена.

    Returns:
        DayEventsResponse: Объект с ключами:
            - date (str): дата в формате ISO.
            - events (list): список событий (задачи и встречи) за указанный день.

    Raises:
        HTTPException: Если дата указана в неверном формате.
    """

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
    """
    Получить события текущего пользователя за указанный месяц календаря.

    Args:
        year (int | None): Год. Если не указан, используется текущий год.
        month (int | None): Месяц (1–12). Если не указан, используется текущий месяц.
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
        current_user (User): Текущий пользователь, полученный из JWT‑токена.

    Returns:
        MonthEventsResponse: Объект с ключами:
            - year (int): целевой год.
            - month (int): целевой месяц.
            - days (dict): словарь, где ключ — дата (ISO‑строка),
                           значение — список событий за этот день.

    Raises:
        HTTPException: Если месяц указан вне диапазона 1–12.
    """

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