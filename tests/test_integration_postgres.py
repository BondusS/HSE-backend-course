import pytest
from asyncpg.pool import Pool
from repositories.items import ItemRepository
from repositories.users import UserRepository

# Фикстура для получения пула соединений из приложения
@pytest.fixture
async def db_pool(request) -> Pool:
    # Предполагается, что `app` из `main` доступен
    # и жизненный цикл `lifespan` был запущен фикстурой более высокого уровня
    from main import app
    return app.state.pool

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_user_item_creation_and_closing(db_pool):
    """
    Интеграционный тест, который проверяет:
    1. Создание пользователя.
    2. Создание объявления для этого пользователя.
    3. Получение созданного объявления.
    4. Закрытие объявления.
    5. Невозможность получить закрытое объявление.
    """
    user_repo = UserRepository(db_pool)
    item_repo = ItemRepository(db_pool)

    # 1. Создаем пользователя
    user_id = await user_repo.create_user(is_verified=True)
    assert user_id is not None

    # 2. Создаем объявление
    item_name = "Integration Test Item"
    item_id = await item_repo.create_item(
        name=item_name,
        description="Test description",
        category=1,
        images_qty=1,
        seller_id=user_id,
    )
    assert item_id is not None

    # 3. Получаем созданное объявление
    item = await item_repo.get_item_with_seller_info(item_id)
    assert item is not None
    assert item.item_id == item_id
    assert item.name == item_name
    assert item.seller_id == user_id

    # 4. Закрываем объявление
    closed_item_id = await item_repo.close_item(item_id)
    assert closed_item_id == item_id

    # 5. Проверяем, что объявление больше не доступно через get_item_with_seller_info
    item_after_closing = await item_repo.get_item_with_seller_info(item_id)
    assert item_after_closing is None

    # Дополнительная проверка: убедимся, что close_item не работает дважды
    closed_again = await item_repo.close_item(item_id)
    assert closed_again is None
