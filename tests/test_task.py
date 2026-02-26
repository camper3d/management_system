import pytest
import pytest_asyncio
from httpx import AsyncClient
import jwt


@pytest.mark.asyncio
async def test_manager_can_create_task(auth_headers, client: AsyncClient):
    """Тест возможности менеджера создавать задачи для членов команды:

        1. Менеджер создаёт команду
        2. Регистрируется второй пользователь (рабочий)
        3. Менеджер добавляет рабочего в команду
        4. Менеджер создаёт задачу для рабочего
        5. Проверяется корректность всех полей созданной задачи
"""

    response = await client.post("/api/teams/", json={"name": "DevTeam"}, headers=auth_headers)
    assert response.status_code == 200
    team = response.json()
    team_id = team["id"]

    register_response = await client.post("/api/auth/register", json={
        "email": "worker@example.com",
        "password": "123"
    })
    assert register_response.status_code in (200, 201)

    login_data = {
        "username": "worker@example.com",
        "password": "123"
    }
    login_response = await client.post(
        "/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    worker_token = login_response.json()["access_token"]

    decoded_token = jwt.decode(worker_token, options={"verify_signature": False})
    worker_id = decoded_token["user_id"]

    add_member_response = await client.post(
        f"/api/teams/{team_id}/add-member",
        json={
            "user_id": worker_id,
            "role": "member"
        },
        headers=auth_headers
    )

    assert add_member_response.status_code == 200
    assert add_member_response.json()["message"] == "Member added"

    task_response = await client.post("/api/tasks/", json={
        "title": "Fix bug",
        "description": "Bug in login flow",
        "assignee_id": worker_id
    }, headers=auth_headers)

    assert task_response.status_code == 200
    task_data = task_response.json()

    assert task_data["title"] == "Fix bug"
    assert task_data["description"] == "Bug in login flow"
    assert task_data["status"] == "open"
    assert task_data["deadline"] is None

    assert task_data["assignee"] is not None
    assert task_data["assignee"]["id"] == worker_id
    assert task_data["assignee"]["email"] == "worker@example.com"
    assert task_data["assignee"]["role"] == "member"

    manager_token = auth_headers["Authorization"].replace("Bearer ", "")
    decoded_manager = jwt.decode(manager_token, options={"verify_signature": False})
    manager_id = decoded_manager["user_id"]

    assert task_data["creator"] is not None
    assert task_data["creator"]["id"] == manager_id
    assert task_data["creator"]["email"] == "test@example.com"
    assert task_data["creator"]["role"] == "admin"

    assert task_data["comments"] == []
