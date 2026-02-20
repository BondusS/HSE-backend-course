import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app, lifespan # Импортируем функцию lifespan
import asyncio

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

    @pytest.mark.asyncio
    async def test_async_predict_success(self, client: AsyncClient):
        """
        Проверяет успешное создание задачи асинхронной модерации.
        """
        user_response = await client.post("/users/", json={"is_verified_seller": True})
        assert user_response.status_code == 201, f"Не удалось создать пользователя: {user_response.text}"
        user_id = user_response.json()["id"]

        item_data = {
            "name": "Асинхронный товар", "description": "Описание", "category": 1,
            "images_qty": 1, "seller_id": user_id
        }
        item_response = await client.post("/items/", json=item_data)
        assert item_response.status_code == 201, f"Не удалось создать объявление: {item_response.text}"
        item_id = item_response.json()["id"]

        async_predict_response = await client.post(f"/async_predict?item_id={item_id}")
        assert async_predict_response.status_code == 202, f"Неверный статус для async_predict: {async_predict_response.text}"
        data = async_predict_response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["message"] == "Moderation request accepted"

        # Проверяем, что запись в БД создана со статусом pending
        pool = app.state.pool
        async with pool.acquire() as conn:
            result = await conn.fetchrow("SELECT status FROM moderation_results WHERE id = $1", data["task_id"])
            assert result["status"] == "pending"
        
        # Очистка
        pool = app.state.pool
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM moderation_results WHERE id = $1", data["task_id"])
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)

    @pytest.mark.asyncio
    async def test_async_predict_item_not_found(self, client: AsyncClient):
        """
        Проверяет, что async_predict возвращает 404, если объявление не найдено.
        """
        response = await client.post("/async_predict?item_id=999999")
        assert response.status_code == 404
        assert "не найдено" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_moderation_result_pending(self, client: AsyncClient):
        """
        Проверяет получение статуса pending для задачи модерации.
        """
        user_response = await client.post("/users/", json={"is_verified_seller": True})
        assert user_response.status_code == 201, f"Не удалось создать пользователя: {user_response.text}"
        user_id = user_response.json()["id"]

        item_data = {
            "name": "Товар для статуса", "description": "Описание", "category": 1,
            "images_qty": 1, "seller_id": user_id
        }
        item_response = await client.post("/items/", json=item_data)
        assert item_response.status_code == 201, f"Не удалось создать объявление: {item_response.text}"
        item_id = item_response.json()["id"]

        async_predict_response = await client.post(f"/async_predict?item_id={item_id}")
        assert async_predict_response.status_code == 202
        task_id = async_predict_response.json()["task_id"]

        status_response = await client.get(f"/moderation_result/{task_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "pending"
        assert data["is_violation"] is None
        assert data["probability"] is None
        
        # Очистка
        pool = app.state.pool
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM moderation_results WHERE id = $1", task_id)
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)

    @pytest.mark.asyncio
    async def test_get_moderation_result_not_found(self, client: AsyncClient):
        """
        Проверяет, что /moderation_result/{task_id} возвращает 404, если задача не найдена.
        """
        response = await client.get("/moderation_result/999999")
        assert response.status_code == 404
        assert "не найдена" in response.json()["detail"]
