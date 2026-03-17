import pytest
from unittest.mock import AsyncMock

from repositories.redis_repository import RedisRepository

@pytest.mark.asyncio
async def test_redis_repository_set_get():
    """
    Юнит-тест: проверяем, что RedisRepository правильно вызывает методы клиента.
    """
    repo = RedisRepository()
    repo.client = AsyncMock()

    test_key = "test_key"
    test_value = {"data": "test_data"}
    ttl = 3600

    await repo.set(test_key, test_value, ttl)
    repo.client.set.assert_called_once_with(test_key, '{"data": "test_data"}', ex=ttl)

    repo.client.get.return_value = '{"data": "test_data"}'
    retrieved_value = await repo.get(test_key)

    repo.client.get.assert_called_once_with(test_key)
    assert retrieved_value == test_value

@pytest.mark.asyncio
async def test_redis_repository_get_none():
    """
    Юнит-тест: проверяем, что RedisRepository возвращает None, если ключ не найден.
    """
    repo = RedisRepository()
    repo.client = AsyncMock()
    repo.client.get.return_value = None

    test_key = "non_existent_key"
    retrieved_value = await repo.get(test_key)

    repo.client.get.assert_called_once_with(test_key)
    assert retrieved_value is None

@pytest.mark.asyncio
async def test_redis_repository_delete():
    """
    Юнит-тест: проверяем, что RedisRepository правильно вызывает метод delete.
    """
    repo = RedisRepository()
    repo.client = AsyncMock()

    test_key = "test_key"
    await repo.delete(test_key)

    repo.client.delete.assert_called_once_with(test_key)
