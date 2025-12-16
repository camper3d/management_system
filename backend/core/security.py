from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from backend.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
        Проверяет соответствие введённого пароля его хэшу.

        Args:
            plain_password (str): Обычный пароль в открытом виде.
            hashed_password (str): Хэшированный пароль, сохранённый в базе.

        Returns:
            bool: True, если пароль совпадает с хэшем, иначе False.
        """

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
        Хэширует пароль для безопасного хранения.

        Args:
            password (str): Пароль в открытом виде.

        Returns:
            str: Хэшированное значение пароля.
        """

    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
        Создаёт JWT‑токен доступа с заданными данными и временем жизни.

        Args:
            data (dict): Данные для кодирования в токене (например, user_id).
            expires_delta (timedelta, optional): Время жизни токена.
                Если не указано, используется значение из настроек (ACCESS_TOKEN_EXPIRE_MINUTES).

        Returns:
            str: Сгенерированный JWT‑токен.
        """

    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)