from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import AsyncSessionLocal


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session