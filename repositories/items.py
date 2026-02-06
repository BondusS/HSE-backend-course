from asyncpg.pool import Pool
from models.schemas import Item

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
            WHERE i.id = $1;
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, item_id)
            if row:
                # Вручную создаем Pydantic-модель Item из полученных данных
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
