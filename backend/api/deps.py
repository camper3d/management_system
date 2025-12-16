from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.auth import TokenData
from backend.core.config import settings
from sqlalchemy.future import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Извлекает текущего пользователя из JWT‑токена и проверяет его наличие в базе данных.

    Args:
        token (str): JWT‑токен, автоматически получаемый через Depends(oauth2_scheme).
        db (AsyncSession): Асинхронная сессия SQLAlchemy, предоставляемая через Depends(get_db).

    Returns:
        User: Объект пользователя, соответствующий user_id из токена.

    Raises:
        HTTPException: Если токен недействителен, не содержит user_id,
                       либо пользователь с таким идентификатором отсутствует в базе.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user