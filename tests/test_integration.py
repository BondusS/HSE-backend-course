import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app, lifespan # Импортируем функцию lifespan

@pytest.mark.integration
class TestDatabaseIntegration:
    """
    Интеграционные тесты, проверяющие взаимодействие с базой данных через API.
    """

    @pytest_asyncio.fixture(scope="function")
    async def client(self) -> AsyncClient:
        """
        Создает клиент для каждого теста.
        Явно управляет жизненным циклом (lifespan) приложения,
        чтобы гарантировать инициализацию app.state.
        """
        # Явно входим в контекст lifespan приложения, используя импортированную функцию
        async with lifespan(app):
            # Теперь app.state гарантированно инициализирован
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                yield client

    @pytest.mark.asyncio
    async def test_full_cycle(self, client: AsyncClient):
        """
        Проверяет полный жизненный цикл:
        1. Создание пользователя.
        2. Создание объявления для этого пользователя.
        3. Предсказание для созданного объявления.
        """
        # 1. Создаем пользователя
        user_response = await client.post("/users/", json={"is_verified_seller": True})
        assert user_response.status_code == 201, f"Не удалось создать пользователя: {user_response.text}"
        user_id = user_response.json()["id"]

        # 2. Создаем объявление для этого пользователя
        item_data = {
            "name": "Тестовый товар",
            "description": "Описание",
            "category": 1,
            "images_qty": 1,
            "seller_id": user_id,
        }
        item_response = await client.post("/items/", json=item_data)
        assert item_response.status_code == 201, f"Не удалось создать объявление: {item_response.text}"
        item_id = item_response.json()["id"]

        # 3. Делаем предсказание для созданного объявления
        predict_response = await client.post(f"/simple_predict?item_id={item_id}")
        assert predict_response.status_code == 200, f"Не удалось выполнить предсказание: {predict_response.text}"
        assert "is_violation" in predict_response.json()

        # Очистка (необязательна, т.к. тестовая БД пересоздается для каждого запуска,
        # но это хорошая практика на случай локальных тестов)
        pool = app.state.pool
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)

    @pytest.mark.asyncio
    async def test_create_item_for_non_existent_user(self, client: AsyncClient):
        """Проверяет, что нельзя создать объявление для несуществующего пользователя."""
        item_data = {
            "name": "Товар без продавца",
            "description": "Описание",
            "category": 1,
            "images_qty": 0,
            "seller_id": 999999, # Несуществующий ID
        }
        response = await client.post("/items/", json=item_data)
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_predict_for_non_existent_item(self, client: AsyncClient):
        """Проверяет, что для несуществующего объявления возвращается 404."""
        response = await client.post("/simple_predict?item_id=999999")
        assert response.status_code == 404
