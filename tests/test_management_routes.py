import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from main import app

# Фикстуры

@pytest.fixture
def client():
    """Фикстура для создания тестового клиента FastAPI."""
    # Мокируем зависимости, чтобы сделать тесты быстрыми и изолированными (юнит-тесты)
    app.state.item_repository = AsyncMock()
    app.state.redis_repository = AsyncMock()
    app.state.user_repository = AsyncMock()
    app.state.moderation_result_repository = AsyncMock()
    app.state.prediction_service = MagicMock()
    app.state.kafka_producer = AsyncMock()
    return TestClient(app)

# Тесты для /close

def test_close_item_success(client):
    """
    Юнит-тест: успешное закрытие объявления.
    """
    item_id_to_close = 123
    app.state.item_repository.close_item.return_value = item_id_to_close

    response = client.post(f"/close?item_id={item_id_to_close}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Объявление {item_id_to_close} успешно закрыто."}
    app.state.item_repository.close_item.assert_awaited_once_with(item_id_to_close)
    app.state.redis_repository.delete.assert_awaited_once_with(f"prediction:{item_id_to_close}")

def test_close_item_not_found(client):
    """
    Юнит-тест: закрытие несуществующего объявления.
    """
    item_id_to_close = 404
    app.state.item_repository.close_item.return_value = None

    response = client.post(f"/close?item_id={item_id_to_close}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"Объявление с ID {item_id_to_close} не найдено."}
    app.state.item_repository.close_item.assert_awaited_once_with(item_id_to_close)

def test_close_item_invalid_id(client):
    """
    Юнит-тест: невалидный ID объявления.
    """
    response = client.post("/close?item_id=invalid")
    assert response.status_code == 422

    response = client.post("/close?item_id=-1")
    assert response.status_code == 422
