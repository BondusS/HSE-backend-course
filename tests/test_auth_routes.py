import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from main import app
from models.schemas import Account

@pytest.fixture
def client():
    app.state.account_repository = AsyncMock()
    return TestClient(app)

def test_login_success(client):
    account_repo_mock = app.state.account_repository
    account_repo_mock.get_by_login_and_password.return_value = Account(id=1, login="testuser", is_blocked=False)

    response = client.post("/login", data={"username": "testuser", "password": "testpassword"})

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "access_token" in response.cookies

def test_login_failure(client):
    account_repo_mock = app.state.account_repository
    account_repo_mock.get_by_login_and_password.return_value = None

    response = client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})

    assert response.status_code == 401
    assert "access_token" not in response.cookies
