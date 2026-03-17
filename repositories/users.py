import time
from asyncpg.pool import Pool
from app.metrics import DB_QUERY_DURATION

class UserRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def create_user(self, is_verified: bool) -> int:
        """
        Создает нового пользователя и возвращает его ID.
        """
        query = "INSERT INTO users (is_verified_seller) VALUES ($1) RETURNING id;"
        start_time = time.time()
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(query, is_verified)
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="insert").observe(end_time - start_time)
        return user_id
