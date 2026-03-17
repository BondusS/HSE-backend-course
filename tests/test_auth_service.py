import pytest
from services.auth import AuthService
from models.schemas import Account

@pytest.fixture
def auth_service():
    return AuthService(secret_key="test_secret")

def test_create_and_verify_token(auth_service: AuthService):
    account = Account(id=1, login="testuser", is_blocked=False)
    token = auth_service.create_token(account)
    
    payload = auth_service.verify_token(token)
    
    assert payload is not None
    assert payload["sub"] == str(account.id)
    assert payload["login"] == account.login

def test_verify_invalid_token(auth_service: AuthService):
    invalid_token = "invalid_token"
    payload = auth_service.verify_token(invalid_token)
    assert payload is None
