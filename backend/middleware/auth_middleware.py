from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from backend.core.config import settings
from backend.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.db.session import AsyncSessionLocal


class AuthMiddleware(BaseHTTPMiddleware):
    """
    1. Извлекает JWT токен из cookie запроса
    2. Проверяет валидность токена
    3. Загружает пользователя из базы данных по ID из токена
    4. Сохраняет объект пользователя в request.state.user для использования в эндпоинтах

    Если токен отсутствует, невалиден или пользователь не найден,
    request.state.user устанавливается в None (анонимный пользователь).
    """
    async def dispatch(self, request: Request, call_next):
        """
        Args:
            request (Request): Входящий HTTP запрос
            call_next (Callable): Функция для передачи запроса дальше по цепочке middleware

        Returns:
            Response: HTTP ответ после обработки запроса
        """
        request.state.user = None
        token = None

        auth_cookie = request.cookies.get("access_token")
        if auth_cookie and auth_cookie.startswith("Bearer "):
            token = auth_cookie[7:]  # убираем "Bearer "

        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id: int = payload.get("user_id")
                if user_id:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(User).where(User.id == user_id))
                        user = result.scalars().first()
                        if user:
                            request.state.user = user
            except JWTError:
                pass

        response = await call_next(request)
        return response
