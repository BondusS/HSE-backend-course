import hashlib
import time
from typing import Optional
from asyncpg.pool import Pool
from app.metrics import DB_QUERY_DURATION
from models.schemas import Account

class AccountRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    async def create_account(self, login: str, password: str) -> Account:
        hashed_password = self._hash_password(password)
        query = "INSERT INTO account (login, password) VALUES ($1, $2) RETURNING id, login, is_blocked"
        start_time = time.time()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, login, hashed_password)
        DB_QUERY_DURATION.labels(query_type="insert").observe(time.time() - start_time)
        return Account(**row)

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        query = "SELECT id, login, is_blocked FROM account WHERE id = $1"
        start_time = time.time()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, account_id)
        DB_QUERY_DURATION.labels(query_type="select").observe(time.time() - start_time)
        return Account(**row) if row else None

    async def get_by_login_and_password(self, login: str, password: str) -> Optional[Account]:
        hashed_password = self._hash_password(password)
        query = "SELECT id, login, is_blocked FROM account WHERE login = $1 AND password = $2"
        start_time = time.time()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, login, hashed_password)
        DB_QUERY_DURATION.labels(query_type="select").observe(time.time() - start_time)
        return Account(**row) if row else None

    async def block_account(self, account_id: int) -> Optional[Account]:
        query = "UPDATE account SET is_blocked = TRUE WHERE id = $1 RETURNING id, login, is_blocked"
        start_time = time.time()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, account_id)
        DB_QUERY_DURATION.labels(query_type="update").observe(time.time() - start_time)
        return Account(**row) if row else None

    async def delete_account(self, account_id: int):
        query = "DELETE FROM account WHERE id = $1"
        start_time = time.time()
        async with self.pool.acquire() as conn:
            await conn.execute(query, account_id)
        DB_QUERY_DURATION.labels(query_type="delete").observe(time.time() - start_time)
