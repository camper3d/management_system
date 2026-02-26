import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.models.base import Base
from backend.models.user import User
from backend.core.security import get_password_hash
from backend.core.config_test import test_settings
from backend.db.session import get_db
import uuid


test_engine = create_async_engine(
    test_settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Фикстура для создания тестового движка базы данных"""

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Фикстура для создания тестовой сессии базы данных"""

    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session) -> AsyncClient:
    """Фикстура для создания тестового HTTP клиента"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def create_user(db_session):
    """Фикстура для создания тестовых пользователей"""

    def _create_user(
            email: str = None,
            password: str = 'password123',
            full_name: str = None,
            role: str = "member"
    ):
        if email is None:
            email = f'test_{uuid.uuid4().hex}@example.com'
        return User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role
        )
    return _create_user


@pytest_asyncio.fixture
async def auth_headers(client, create_user, db_session):
    """Фикстура для получения заголовков авторизации"""

    user = create_user("test@example.com", "password123")
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(autouse=True)
async def clean_users(db_session):
    """Фикстура для автоматической очистки таблицы пользователей"""

    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
