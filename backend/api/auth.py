from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from backend.db.session import get_db
from backend.schemas.auth import UserCreate, Token
from backend.crud.user import create_user, get_user_by_email
from backend.core.security import verify_password, create_access_token
from backend.models.user import User
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])

html_router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Зарегистрировать нового пользователя и выдать ему JWT‑токен доступа.

    Args:
        user (UserCreate): Данные для создания пользователя (email, пароль и др.).
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        Token: JWT‑токен доступа в формате {"access_token": str, "token_type": "bearer"}.

    Raises:
        HTTPException:
            - 400: Если email уже зарегистрирован.
    """

    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await create_user(db, user)
    access_token = create_access_token(data={"user_id": new_user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Авторизовать пользователя по email и паролю и выдать JWT‑токен доступа.

    Args:
        form_data (OAuth2PasswordRequestForm): Данные формы входа (username=email, password).
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        Token: JWT‑токен доступа в формате {"access_token": str, "token_type": "bearer"}.

    Raises:
        HTTPException:
            - 401: Если email или пароль неверны.
    """

    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# роуты для html_router
@html_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Отображает страницу регистрации нового пользователя.

    Args:
        request (Request): Объект запроса FastAPI.

    Returns:
        TemplateResponse: HTML-страница с формой регистрации (auth/register.html).
    """
    return request.app.state.templates.TemplateResponse(
        "auth/register.html", {"request": request}
    )


@html_router.post("/register")
async def register_html(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Обрабатывает отправку формы регистрации.

    Проверяет уникальность email, создаёт нового пользователя,
    генерирует JWT-токен и устанавливает cookie для аутентификации.

    Args:
        request (Request): Объект запроса FastAPI.
        email (str): Email пользователя (из формы).
        password (str): Пароль пользователя (из формы).
        full_name (Optional[str]): Полное имя пользователя (опционально).
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        TemplateResponse: Если email уже существует — возвращает страницу регистрации с ошибкой.
        RedirectResponse: При успешной регистрации перенаправляет на /dashboard
                         и устанавливает cookie с токеном.
    """
    db_user = await get_user_by_email(db, email)
    if db_user:
        return request.app.state.templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Email already registered"},
        )

    user_create = UserCreate(email=email, password=password, full_name=full_name)
    new_user = await create_user(db, user_create)
    access_token = create_access_token(data={"user_id": new_user.id})

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=1800
    )
    return response


@html_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Отображает страницу входа в систему.

    Args:
        request (Request): Объект запроса FastAPI.

    Returns:
        TemplateResponse: HTML-страница с формой входа (auth/login.html).
    """
    return request.app.state.templates.TemplateResponse(
        "auth/login.html", {"request": request}
    )


@html_router.post("/login")
async def login_html(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Аутентифицирует пользователя и создаёт сессию.

    Проверяет существование пользователя и соответствие пароля.
    При успехе генерирует JWT-токен и устанавливает cookie.

    Args:
        request (Request): Объект запроса FastAPI.
        email (str): Email пользователя (из формы).
        password (str): Пароль пользователя (из формы).
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        TemplateResponse: Если данные неверны — возвращает страницу входа с ошибкой.
        RedirectResponse: При успешном входе перенаправляет на /dashboard
                         и устанавливает cookie с токеном.
    """
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    access_token = create_access_token(data={"user_id": user.id})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=1800
    )
    return response


@html_router.get("/logout")
async def logout():
    """
    Выполняет выход пользователя из системы.

    Удаляет cookie с токеном доступа и перенаправляет на страницу входа.

    Returns:
        RedirectResponse: Перенаправление на /login с удалённой cookie аутентификации.
    """
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# Экспортируем оба роутера
auth_api_router = router
auth_html_router = html_router
