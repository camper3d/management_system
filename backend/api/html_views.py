from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.crud.user import delete_user, update_user_profile
from backend.db.session import get_db
from backend.crud.task import get_tasks_for_user, create_task, get_task_by_id, update_task
from backend.crud.meeting import get_user_meetings, create_meeting
from backend.models.user import User
from backend.crud.event_calendar import get_events_for_month
from datetime import date, datetime
from calendar import monthrange
from typing import List
from backend.crud.team import get_team_members, join_team_by_code, get_team_by_id
from backend.crud.evaluation import create_evaluation
from backend.schemas.task import TaskCreate
from backend.schemas.meeting import MeetingCreate
from backend.schemas.evaluation import EvaluationCreate


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

    user = request.state.user
    tasks = []
    meetings = []
    team = None

    if user.team_id is not None:
        tasks = await get_tasks_for_user(db, user.id, user.team_id)
        meetings = await get_user_meetings(db, user.id)
        team = await get_team_by_id(db, user.team_id)

    return request.app.state.templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "tasks": tasks,
        "meetings": meetings,
        'team': team
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


@html_router.get("/tasks/create", response_class=HTMLResponse)
async def create_task_form(request: Request, db: AsyncSession = Depends(get_db)):
    """
        Отображает форму создания новой задачи.

        Args:
            request (Request): Объект запроса FastAPI
            db (AsyncSession): Асинхронная сессия базы данных

        Returns:
            HTMLResponse: HTML страница с формой создания задачи

        Notes:
            - Требуется авторизация пользователя
            - Если пользователь в команде, загружается список членов команды для назначения
            - Доступно только для авторизованных пользователей (роль не проверяется)
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    user = request.state.user
    team_members = []
    if user.team_id:
        team_members = await get_team_members(db, user.team_id)
    return request.app.state.templates.TemplateResponse("task_create.html", {
        "request": request, "team_members": team_members, "user": user
    })


@html_router.post("/tasks/create")
async def handle_create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    deadline: str = Form(None),
    assignee_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
        Обрабатывает создание новой задачи.

        Args:
            request (Request): Объект запроса FastAPI
            title (str): Заголовок задачи (обязательное поле)
            description (str | None): Описание задачи (опционально)
            deadline (str | None): Дедлайн в формате ISO строки (опционально)
            assignee_id (int): ID пользователя, на которого назначается задача
            db (AsyncSession): Асинхронная сессия базы данных

        Returns:
            RedirectResponse: Перенаправление на страницу задач с сообщением об успехе или ошибке

        Raises:
            303 Redirect: Перенаправление с параметрами success или error в URL

        Notes:
            - Требуется авторизация пользователя
            - Только пользователи с ролями admin или manager могут создавать задачи
            - Дата дедлайна конвертируется из ISO формата
            - При ошибке возвращается на форму создания с сообщением об ошибке
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    user = request.state.user
    if user.role not in ("admin", "manager"):
        return RedirectResponse(url="/tasks?error=Only+managers+can+create+tasks", status_code=303)

    try:
        deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")) if deadline else None
        task_in = TaskCreate(title=title, description=description, deadline=deadline_dt, assignee_id=assignee_id)
        await create_task(db, task_in, user.id, user.team_id)
        return RedirectResponse(url="/tasks?success=Task+created", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/tasks/create?error={str(e)[:100]}", status_code=303)


@html_router.post("/tasks/{task_id}/update-status")
async def update_task_status(
    request: Request,
    task_id: int,
    status: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновляет статус задачи.

    Args:
        request (Request): Объект запроса FastAPI
        task_id (int): ID задачи для обновления
        status (str): Новый статус задачи (должен быть допустимым значением)
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        RedirectResponse: Перенаправление на страницу задач с сообщением об успехе или ошибке

    Notes:
        - Требуется авторизация пользователя
        - Задача должна принадлежать той же команде, что и пользователь
        - Только исполнитель задачи может менять статус на in_progress или done
        - Статус обновляется через функцию update_task
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    user = request.state.user
    task = await get_task_by_id(db, task_id)
    if not task or task.team_id != user.team_id:
        return RedirectResponse(url="/tasks?error=Task+not+found", status_code=303)

    if status in ("in_progress", "done") and task.assignee_id != user.id:
        return RedirectResponse(url="/tasks?error=Only+assignee+can+update+status", status_code=303)

    await update_task(db, task, {"status": status})
    return RedirectResponse(url="/tasks?success=Status+updated", status_code=303)


@html_router.get("/join", response_class=HTMLResponse)
async def join_team_form(request: Request):
    """
    Отображает форму для присоединения к команде по инвайт-коду.

    Args:
        request (Request): Объект запроса FastAPI

    Returns:
        HTMLResponse: HTML страница с формой ввода инвайт-кода

    Notes:
        - Требуется авторизация пользователя
        - Пользователь не должен состоять ни в одной команде
        - При уже существующей команде перенаправляет на dashboard с ошибкой
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    if request.state.user.team_id:
        return RedirectResponse(url="/dashboard?error=Already+in+a+team")
    return request.app.state.templates.TemplateResponse("join_team.html", {"request": request})


@html_router.post("/join")
async def handle_join_team(
        request: Request,
        invite_code: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    """
    Обрабатывает присоединение пользователя к команде по инвайт-коду.

    Args:
        request (Request): Объект запроса FastAPI
        invite_code (str): Инвайт-код команды (очищается от пробелов)
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        RedirectResponse: Перенаправление на dashboard с сообщением об успехе или на форму с ошибкой

    Notes:
        - Требуется авторизация пользователя
        - Инвайт-код очищается от пробелов (strip)
        - При успехе пользователь становится MEMBER команды
        - При неудаче возвращается на форму с сообщением об ошибке
    """
    if not request.state.user:
        return RedirectResponse(url="/login")

    success = await join_team_by_code(db, request.state.user.id, invite_code.strip())
    if success:
        return RedirectResponse(url="/dashboard?success=Joined+team", status_code=303)
    else:
        return RedirectResponse(url="/join?error=Invalid+or+expired+code", status_code=303)


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


@html_router.get("/meetings/create", response_class=HTMLResponse)
async def create_meeting_form(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Отображает форму создания новой встречи.

    Args:
        request (Request): Объект запроса FastAPI
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        HTMLResponse: HTML страница с формой создания встречи

    Notes:
        - Требуется авторизация пользователя
        - Если пользователь в команде, загружается список членов команды для приглашения
        - Доступно только для авторизованных пользователей
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    user = request.state.user
    team_members = []
    if user.team_id:
        team_members = await get_team_members(db, user.team_id)
    return request.app.state.templates.TemplateResponse("meeting_create.html", {
        "request": request, "team_members": team_members, "user": user
    })


@html_router.post("/meetings/create")
async def handle_create_meeting(
    request: Request,
    title: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    participant_ids: List[str] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Обрабатывает создание новой встречи.

    Args:
        request (Request): Объект запроса FastAPI
        title (str): Название встречи (обязательное поле)
        start_time (str): Время начала в ISO формате (обязательное поле)
        end_time (str): Время окончания в ISO формате (обязательное поле)
        participant_ids (List[str]): Список ID участников (обязательное поле)
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        RedirectResponse: Перенаправление на страницу встреч с сообщением об успехе или ошибке

    Raises:
        303 Redirect: Перенаправление с параметрами success или error в URL

    Notes:
        - Требуется авторизация пользователя
        - Даты конвертируются из ISO формата (поддерживается Z для UTC)
        - ID участников преобразуются из строк в целые числа
        - При ошибке возвращается на форму создания с сообщением об ошибке
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    user = request.state.user

    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        meeting_in = MeetingCreate(
            title=title,
            start_time=start,
            end_time=end,
            participant_ids=[int(x) for x in participant_ids]
        )
        await create_meeting(db, meeting_in, user.id, user.team_id)
        return RedirectResponse(url="/meetings?success=Meeting+created", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/meetings/create?error={str(e)[:100]}", status_code=303)


@html_router.get("/evaluations/create/{task_id}", response_class=HTMLResponse)
async def evaluation_form(request: Request, task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Отображает форму оценки выполненной задачи.

    Args:
        request (Request): Объект запроса FastAPI
        task_id (int): ID задачи для оценки
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        HTMLResponse: HTML страница с формой оценки задачи

    Notes:
        - Требуется авторизация пользователя
        - Задача должна иметь статус "done" (выполнена)
        - Только менеджеры и администраторы могут оценивать задачи
        - При невыполненной задаче перенаправляет на список задач с ошибкой
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    task = await get_task_by_id(db, task_id)
    if not task or task.status != "done":
        return RedirectResponse(url="/tasks?error=Only+completed+tasks+can+be+evaluated", status_code=303)
    return request.app.state.templates.TemplateResponse("evaluation_create.html", {
        "request": request, "task": task
    })


@html_router.post("/evaluations/create/{task_id}")
async def handle_evaluation(
    request: Request,
    task_id: int,
    score: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Обрабатывает создание оценки для выполненной задачи.

    Args:
        request (Request): Объект запроса FastAPI
        task_id (int): ID оцениваемой задачи
        score (int): Оценка за выполненную задачу (обязательное поле)
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        RedirectResponse: Перенаправление на страницу задач с сообщением об успехе или ошибке

    Notes:
        - Требуется авторизация пользователя
        - Создает оценку через функцию create_evaluation
        - При ошибке возвращает на форму с сообщением (обрезанным до 100 символов)
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    try:
        eval_in = EvaluationCreate(task_id=task_id, score=score)
        await create_evaluation(db, eval_in, request.state.user.id)
        return RedirectResponse(url="/tasks?success=Evaluation+submitted", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/evaluations/create/{task_id}?error={str(e)[:100]}", status_code=303)


@html_router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_form(request: Request):
    """
    Отображает форму редактирования профиля пользователя.

    Args:
        request (Request): Объект запроса FastAPI

    Returns:
        HTMLResponse: HTML страница с формой редактирования профиля

    Notes:
        - Требуется авторизация пользователя
        - В форму передаются текущие данные пользователя для предзаполнения
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    return request.app.state.templates.TemplateResponse("profile_edit.html", {
        "request": request,
        "user": request.state.user
    })


@html_router.post("/profile/edit")
async def handle_edit_profile(
        request: Request,
        full_name: str = Form(None),
        email: str = Form(None),
        db: AsyncSession = Depends(get_db)
):
    """
    Обрабатывает обновление профиля пользователя.

    Args:
        request (Request): Объект запроса FastAPI
        full_name (str | None): Новое полное имя (опционально)
        email (str | None): Новый email (опционально)
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        RedirectResponse: Перенаправление на страницу профиля с сообщением об успехе или ошибке

    Raises:
        ValueError: Если email уже используется другим пользователем

    Notes:
        - Требуется авторизация пользователя
        - Обновляются только переданные поля
        - Проверяется уникальность email при обновлении
        - Использует функцию update_user_profile для бизнес-логики
    """
    if not request.state.user:
        return RedirectResponse(url="/login")

    try:
        updated = await update_user_profile(db, request.state.user.id, full_name, email)
        if updated:
            return RedirectResponse(url="/profile/edit?success=Profile+updated", status_code=303)
        else:
            return RedirectResponse(url="/profile/edit?error=User+not+found", status_code=303)
    except ValueError as e:
        return RedirectResponse(url=f"/profile/edit?error={str(e)}", status_code=303)


@html_router.get("/profile/delete", response_class=HTMLResponse)
async def delete_profile_confirm(request: Request):
    """
    Отображает страницу подтверждения удаления профиля.

    Args:
        request (Request): Объект запроса FastAPI

    Returns:
        HTMLResponse: HTML страница с предупреждением о удалении аккаунта

    Notes:
        - Требуется авторизация пользователя
        - Страница запрашивает подтверждение перед удалением
        - Содержит предупреждение о необратимости действия

    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    return request.app.state.templates.TemplateResponse("profile_delete.html", {
        "request": request
    })


@html_router.post("/profile/delete")
async def handle_delete_profile(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Обрабатывает удаление профиля пользователя.

    Args:
        request (Request): Объект запроса FastAPI
        db (AsyncSession): Асинхронная сессия базы данных

    Returns:
        RedirectResponse: Перенаправление на главную страницу с сообщением об успехе или на профиль с ошибкой

    Notes:
        - Требуется авторизация пользователя
        - При успешном удалении удаляется cookie access_token
        - Использует функцию delete_user для удаления из БД
        - Действие необратимо - все данные пользователя удаляются
    """
    if not request.state.user:
        return RedirectResponse(url="/login")
    success = await delete_user(db, request.state.user.id)
    if success:
        response = RedirectResponse(url="/?success=Account+deleted", status_code=303)
        response.delete_cookie("access_token")
        return response
    return RedirectResponse(url="/profile?error=Deletion+failed", status_code=303)

