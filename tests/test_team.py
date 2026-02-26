import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_team(auth_headers, client: AsyncClient):
    """Тест успешного создания команды"""

    response = await client.post(
        "/api/teams/",
        json={"name": "Test Team"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Team"
    assert len(data["members"]) == 1


@pytest.mark.asyncio
async def test_cannot_create_team_twice(auth_headers, client: AsyncClient):
    """Тест невозможности создания двух команд одним пользователем"""

    await client.post("/api/teams/", json={"name": "Team1"}, headers=auth_headers)
    response = await client.post("/api/teams/", json={"name": "Team2"}, headers=auth_headers)
    assert response.status_code == 400
