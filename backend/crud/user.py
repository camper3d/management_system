from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.user import User
from backend.core.security import get_password_hash
from backend.schemas.auth import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
        Найти пользователя по его email.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
            email (str): Email пользователя.

        Returns:
            User | None: Объект пользователя, если найден, иначе None.
        """

    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    """
        Создать нового пользователя.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
            user_create (UserCreate): Входные данные для создания пользователя (email, пароль, полное имя).

        Returns:
            User: Созданный объект пользователя.

        Notes:
            - Пароль автоматически хэшируется перед сохранением.
            - Новому пользователю назначается роль "member" по умолчанию.
        """

    db_user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name,
        role="member"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        full_name: str | None = None,
        email: str | None = None
) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return None

    if email:
        existing = await db.execute(select(User).where(User.email == email, User.id != user_id))
        if existing.scalars().first():
            raise ValueError("Email already in use")
        user.email = email

    if full_name is not None:
        user.full_name = full_name

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True


