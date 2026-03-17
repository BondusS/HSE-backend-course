import pytest
from asyncpg.pool import Pool
from repositories.accounts import AccountRepository

@pytest.fixture
async def db_pool(request) -> Pool:
    from main import app
    return app.state.pool

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_account_repository(db_pool):
    """
    Интеграционный тест для AccountRepository.
    """
    repo = AccountRepository(db_pool)
    login = "testuser"
    password = "testpassword"

    # 1. Create account
    account = await repo.create_account(login, password)
    assert account.login == login
    assert not account.is_blocked

    # 2. Get by ID
    retrieved_account = await repo.get_by_id(account.id)
    assert retrieved_account.id == account.id
    assert retrieved_account.login == login

    # 3. Get by login and password
    found_account = await repo.get_by_login_and_password(login, password)
    assert found_account.id == account.id

    # 4. Block account
    blocked_account = await repo.block_account(account.id)
    assert blocked_account.is_blocked

    # 5. Delete account
    await repo.delete_account(account.id)
    deleted_account = await repo.get_by_id(account.id)
    assert deleted_account is None
