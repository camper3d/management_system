import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    """Тест процесса регистрации и последующего входа пользователя"""

    response = await client.post("/api/auth/register", json={
        "email": "user1@example.com",
        "password": "securepassword",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    token_data = response.json()
    assert "access_token" in token_data

    response = await client.post("/api/auth/login", data={
        "username": "user1@example.com",
        "password": "securepassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Тест входа с неверным паролем"""

    await client.post("/api/auth/register", json={
        "email": "user2@example.com",
        "password": "mypassword"
    })

    response = await client.post("/api/auth/login", data={
        "username": "user2@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401
