from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.base import AsyncSessionLocal


async def get_db() -> AsyncSession:
    """
        Получить асинхронную сессию базы данных.

        Yields:
            AsyncSession: Асинхронная сессия SQLAlchemy для работы с БД.
        """

    async with AsyncSessionLocal() as session:
        yield session