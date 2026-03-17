import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.dependencies import get_current_account
from models.schemas import Account

@pytest.mark.asyncio
async def test_get_current_account_success():
    mock_request = MagicMock()
    mock_request.app.state.account_repository = AsyncMock()
    mock_request.cookies.get.return_value = "Bearer valid_token"
    
    auth_service_mock = MagicMock()
    auth_service_mock.verify_token.return_value = {"sub": "1"}
    
    account_repo_mock = mock_request.app.state.account_repository
    account_repo_mock.get_by_id.return_value = Account(id=1, login="testuser", is_blocked=False)
    
    # Replace the auth service in the dependency with our mock
    from app import dependencies
    dependencies.AUTH_SERVICE = auth_service_mock

    account = await get_current_account(request=mock_request, token="valid_token")
    
    assert account.id == 1
    assert account.login == "testuser"

@pytest.mark.asyncio
async def test_get_current_account_no_token():
    mock_request = MagicMock()
    mock_request.cookies.get.return_value = None
    
    with pytest.raises(HTTPException) as excinfo:
        await get_current_account(request=mock_request, token=None)
    
    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_account_invalid_token():
    mock_request = MagicMock()
    mock_request.cookies.get.return_value = "Bearer invalid_token"
    
    auth_service_mock = MagicMock()
    auth_service_mock.verify_token.return_value = None
    
    from app import dependencies
    dependencies.AUTH_SERVICE = auth_service_mock
    
    with pytest.raises(HTTPException) as excinfo:
        await get_current_account(request=mock_request, token="invalid_token")
        
    assert excinfo.value.status_code == 401
