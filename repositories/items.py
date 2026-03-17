import time
from asyncpg.pool import Pool
from models.schemas import Item
from app.metrics import DB_QUERY_DURATION

class ItemRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_item_with_seller_info(self, item_id: int) -> Item | None:
        """
        Получает из базы данных объявление и статус верификации его продавца.
        """
        query = """
            SELECT
                i.id as item_id,
                i.name,
                i.description,
                i.category,
                i.images_qty,
                u.id as seller_id,
                u.is_verified_seller
            FROM items i
            JOIN users u ON i.seller_id = u.id
            WHERE i.id = $1 AND i.is_closed = FALSE;
        """
        start_time = time.time()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, item_id)
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="select").observe(end_time - start_time)
        
        if row:
            return Item(
                item_id=row['item_id'],
                name=row['name'],
                description=row['description'],
                category=row['category'],
                images_qty=row['images_qty'],
                seller_id=row['seller_id'],
                is_verified_seller=row['is_verified_seller']
            )
        return None

    async def create_item(
        self, name: str, description: str, category: int, images_qty: int, seller_id: int
    ) -> int:
        """
        Создает новое объявление и возвращает его ID.
        """
        query = """
            INSERT INTO items (name, description, category, images_qty, seller_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id;
        """
        start_time = time.time()
        async with self.pool.acquire() as conn:
            item_id = await conn.fetchval(
                query, name, description, category, images_qty, seller_id
            )
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="insert").observe(end_time - start_time)
        return item_id

    async def close_item(self, item_id: int) -> int | None:
        """
        Помечает объявление как закрытое.
        """
        query = """
            UPDATE items
            SET is_closed = TRUE
            WHERE id = $1 AND is_closed = FALSE
            RETURNING id;
        """
        start_time = time.time()
        async with self.pool.acquire() as conn:
            closed_item_id = await conn.fetchval(query, item_id)
        end_time = time.time()
        DB_QUERY_DURATION.labels(query_type="update").observe(end_time - start_time)
        return closed_item_id
