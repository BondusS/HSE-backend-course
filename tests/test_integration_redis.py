import pytest
import asyncio
from repositories.redis_repository import RedisRepository

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_redis_set_get_delete():
    """
    Интеграционный тест для проверки полного цикла работы с Redis:
    установка значения, получение, проверка и удаление.
    """
    repo = RedisRepository(host="localhost", port=6379)
    test_key = "integration_test_key"
    test_value = {"message": "Hello, Redis!"}

    try:
        await repo.set(test_key, test_value, ttl=60)
        retrieved_value = await repo.get(test_key)
        assert retrieved_value == test_value
        exists = await repo.client.exists(test_key)
        assert exists
        await repo.delete(test_key)
        retrieved_value_after_delete = await repo.get(test_key)
        assert retrieved_value_after_delete is None
    finally:
        await repo.delete(test_key)
        await repo.client.close()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_redis_ttl():
    """
    Интеграционный тест для проверки TTL (времени жизни) ключа в Redis.
    """
    repo = RedisRepository(host="localhost", port=6379)
    test_key = "integration_ttl_test_key"
    test_value = {"message": "This key will expire"}

    try:
        await repo.set(test_key, test_value, ttl=1)
        retrieved_value = await repo.get(test_key)
        assert retrieved_value == test_value
        await asyncio.sleep(1.1)
        retrieved_value_after_ttl = await repo.get(test_key)
        assert retrieved_value_after_ttl is None
    finally:
        await repo.delete(test_key)
        await repo.client.close()
