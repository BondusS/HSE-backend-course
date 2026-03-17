import time
from asyncpg.pool import Pool
from datetime import datetime
from typing import Optional
from app.metrics import DB_QUERY_DURATION

class ModerationResultRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def create_pending_result(self, item_id: int) -> int:
        """
        Создает новую запись в moderation_results со статусом 'pending'
        и возвращает ее ID (task_id).
        """
        query = """
            INSERT INTO moderation_results (item_id, status, created_at)
            VALUES ($1, 'pending', NOW())
            RETURNING id;
        """
        start_time = time.time()
        async with self.pool.acquire() as conn:
            task_id = await conn.fetchval(query, item_id)
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="insert").observe(end_time - start_time)
        return task_id

    async def get_result_by_id(self, task_id: int) -> Optional[dict]:
        """
        Получает запись о результате модерации по task_id.
        """
        query = """
            SELECT
                id as task_id,
                item_id,
                status,
                is_violation,
                probability,
                error_message,
                created_at,
                processed_at
            FROM moderation_results
            WHERE id = $1;
        """
        start_time = time.time()
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, task_id)
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="select").observe(end_time - start_time)
        if record:
            return dict(record)
        return None

    async def update_result(
        self,
        task_id: int,
        status: str,
        is_violation: Optional[bool] = None,
        probability: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """
        Обновляет статус и результаты модерации для записи по task_id.
        """
        set_clauses = ["status = $2", "processed_at = NOW()"]
        params = [task_id, status]
        
        if is_violation is not None:
            set_clauses.append("is_violation = $3")
            params.append(is_violation)
        if probability is not None:
            set_clauses.append("probability = $4")
            params.append(probability)
        if error_message is not None:
            set_clauses.append("error_message = $5")
            params.append(error_message)
        
        final_set_clauses = []
        param_idx = 2
        for clause in set_clauses:
            if "$3" in clause and is_violation is None:
                continue
            if "$4" in clause and probability is None:
                continue
            if "$5" in clause and error_message is None:
                continue
            final_set_clauses.append(f"{clause.split('=')[0].strip()} = ${param_idx}")
            param_idx += 1

        final_params = [task_id, status]
        if is_violation is not None:
            final_params.append(is_violation)
        if probability is not None:
            final_params.append(probability)
        if error_message is not None:
            final_params.append(error_message)


        query = f"""
            UPDATE moderation_results
            SET {', '.join(final_set_clauses)}
            WHERE id = $1;
        """
        start_time = time.time()
        async with self.pool.acquire() as conn:
            await conn.execute(query, *final_params)
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="update").observe(end_time - start_time)
