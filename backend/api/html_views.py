from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.crud.task import get_tasks_for_user
from backend.crud.meeting import get_user_meetings
from backend.models.user import User
from backend.crud.event_calendar import get_events_for_month
from datetime import date
from calendar import monthrange

html_router = APIRouter()


@html_router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница: редирект на /dashboard или /login"""
    if request.state.user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@html_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Отображает главную панель управления с задачами и встречами пользователя.

    Проверяет аутентификацию пользователя. Если пользователь состоит в команде,
    загружает его задачи и встречи из базы данных.

    Args:
        request (Request): Объект запроса FastAPI.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        TemplateResponse: HTML-страница дашборда (dashboard.html) с данными пользователя,
                         задачами и встречами. При отсутствии аутентификации —
                         RedirectResponse на /login.
    """
    if not request.state.user:
        return RedirectResponse(url="/login")

    user: User = request.state.user
    tasks = []
    meetings = []

    if user.team_id is not None:
        tasks = await get_tasks_for_user(db, user.id, user.team_id)
        meetings = await get_user_meetings(db, user.id)

    return request.app.state.templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "tasks": tasks,
        "meetings": meetings
    })


@html_router.get("/calendar", response_class=HTMLResponse)
async def calendar_view(
    request: Request,
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Отображает календарь событий пользователя на указанный месяц.

    Генерирует сетку календаря с понедельника по воскресенье,
    отображает события для каждого дня и выделяет текущую дату.

    Args:
        request (Request): Объект запроса FastAPI.
        year (int, optional): Год для отображения. По умолчанию текущий год.
        month (int, optional): Месяц для отображения. По умолчанию текущий месяц.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        TemplateResponse: HTML-страница календаря (calendar.html) с сеткой месяцев,
                         событиями по дням и навигацией.
                         При отсутствии аутентификации — RedirectResponse на /login.

    Notes:
        - Календарь всегда начинается с понедельника.
        - Пустые ячейки в начале и конце месяца отображаются без дней.
        - События загружаются функцией get_events_for_month().
    """
    if not request.state.user:
        return RedirectResponse(url="/login")

    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    events_by_day = await get_events_for_month(
        db,
        user_id=request.state.user.id,
        year=target_year,
        month=target_month
    )

    first_weekday, num_days = monthrange(target_year, target_month)
    weeks = []
    day = 1

    for week_idx in range(6):
        week = []
        for weekday in range(7):
            if week_idx == 0 and weekday < first_weekday:
                week.append({"day": None, "date_str": None, "events": []})
            elif day <= num_days:
                date_str = f"{target_year}-{target_month:02d}-{day:02d}"
                events = events_by_day.get(date_str, [])
                week.append({
                    "day": day,
                    "date_str": date_str,
                    "events": events,
                    "is_today": date_str == today.isoformat()
                })
                day += 1
            else:
                week.append({"day": None, "date_str": None, "events": []})
        weeks.append(week)
        if day > num_days:
            break

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return request.app.state.templates.TemplateResponse("calendar.html", {
        "request": request,
        "year": target_year,
        "month": target_month,
        "weeks": weeks,
        "weekdays": weekdays,
        "today": today
    })


@html_router.get("/tasks", response_class=HTMLResponse)
async def tasks_view(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Отображает страницу со списком задач пользователя.

    Проверяет аутентификацию пользователя. Если пользователь состоит в команде,
    загружает его задачи из базы данных.

    Args:
        request (Request): Объект запроса FastAPI.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        TemplateResponse: HTML-страница задач (tasks.html) с данными пользователя
                         и списком его задач. При отсутствии аутентификации —
                         RedirectResponse на /login.
    """
    if not request.state.user:
        return RedirectResponse(url="/login")

    user: User = request.state.user
    tasks = []
    if user.team_id is not None:
        tasks = await get_tasks_for_user(db, user.id, user.team_id)

    return request.app.state.templates.TemplateResponse("tasks.html", {
        "request": request,
        "user": user,
        "tasks": tasks
    })


@html_router.get("/meetings", response_class=HTMLResponse)
async def meetings_view(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Отображает страницу со списком встреч пользователя.

    Проверяет аутентификацию пользователя. Если пользователь состоит в команде,
    загружает его встречи из базы данных.

    Args:
        request (Request): Объект запроса FastAPI.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        TemplateResponse: HTML-страница встреч (meetings.html) с данными пользователя
                         и списком его встреч. При отсутствии аутентификации —
                         RedirectResponse на /login.
    """
    if not request.state.user:
        return RedirectResponse(url="/login")

    user: User = request.state.user
    meetings = []
    if user.team_id is not None:
        meetings = await get_user_meetings(db, user.id)
    return request.app.state.templates.TemplateResponse("meetings.html", {
        "request": request,
        "user": user,
        "meetings": meetings
    })