import redis.asyncio as redis
from typing import Optional, Any
import json

class RedisRepository:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db)

    async def get(self, key: str) -> Optional[Any]:
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int):
        """
        Сохраняет значение в Redis с TTL.
        TTL (Time To Live) - время жизни ключа в секундах.
        Я выбрал TTL равным 1 часу (3600 секунд), потому что предсказания могут устаревать,
        и нет смысла хранить их вечно. К тому же, это снизит потребление памяти Redis.
        """
        await self.client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        await self.client.delete(key)
