from asyncpg.pool import Pool

class UserRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def create_user(self, is_verified: bool) -> int:
        """
        Создает нового пользователя и возвращает его ID.
        """
        query = "INSERT INTO users (is_verified_seller) VALUES ($1) RETURNING id;"
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(query, is_verified)
            return user_id
