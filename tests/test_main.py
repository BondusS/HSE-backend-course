import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from main import app
from models.schemas import Item


# Используем pytest_asyncio.fixture для асинхронных фикстур
@pytest_asyncio.fixture
async def client() -> AsyncClient:
    # Используем новый, рекомендованный способ создания клиента
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_prediction_service():
    # Мокаем сервис предсказаний
    mock_svc = MagicMock()
    # Метод predict возвращает стандартный успешный ответ
    mock_svc.predict.return_value = {"is_violation": False, "probability": 0.1}
    mock_svc.model = "mock_model_exists" # Убеждаемся, что модель "загружена"
    return mock_svc


@pytest.fixture
def mock_item_repository():
    # Мокаем репозиторий
    mock_repo = MagicMock()
    # Создаем мок для асинхронного метода
    mock_repo.get_item_with_seller_info = AsyncMock()
    return mock_repo


@pytest.mark.asyncio
async def test_simple_predict_success(client: AsyncClient, mock_prediction_service, mock_item_repository):
    """
    Тест успешного выполнения simple_predict.
    """
    # Настраиваем мок репозитория: при вызове с item_id=1 он вернет тестовый Item
    test_item = Item(
        item_id=1, name="Test", description="Test desc", category=1,
        images_qty=1, seller_id=1, is_verified_seller=True
    )
    mock_item_repository.get_item_with_seller_info.return_value = test_item

    # Подменяем реальные сервисы нашими моками в состоянии приложения
    app.state.prediction_service = mock_prediction_service
    app.state.item_repository = mock_item_repository

    # Выполняем запрос
    response = await client.post("/simple_predict", params={"item_id": 1})

    # Проверяем результат
    assert response.status_code == 200
    assert response.json()["is_violation"] is False
    
    # Проверяем, что метод репозитория был вызван с правильным item_id
    mock_item_repository.get_item_with_seller_info.assert_awaited_once_with(1)
    # Проверяем, что сервис предсказаний был вызван с данными, которые вернул репозиторий
    mock_prediction_service.predict.assert_called_once_with(test_item)


@pytest.mark.asyncio
async def test_simple_predict_not_found(client: AsyncClient, mock_item_repository):
    """
    Тест случая, когда item_id не найден в базе данных.
    """
    # Настраиваем мок репозитория: при вызове он вернет None
    mock_item_repository.get_item_with_seller_info.return_value = None
    app.state.item_repository = mock_item_repository
    # Сервис предсказаний нам здесь не важен

    # Выполняем запрос
    response = await client.post("/simple_predict", params={"item_id": 999})

    # Проверяем, что получили ошибку 404
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    
    # Проверяем, что метод репозитория был вызван
    mock_item_repository.get_item_with_seller_info.assert_awaited_once_with(999)


@pytest.mark.asyncio
async def test_simple_predict_invalid_id(client: AsyncClient):
    """
    Тест на невалидный item_id (например, 0 или отрицательный).
    FastAPI должен вернуть ошибку 422.
    """
    response = await client.post("/simple_predict", params={"item_id": 0})
    assert response.status_code == 422
