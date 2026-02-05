import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def mock_model_service():
    # Создаем мок-сервис
    mock_svc = MagicMock()
    # Используем `with patch` для временной замены сервиса в состоянии приложения
    with patch.object(app.state, 'prediction_service', mock_svc):
        yield mock_svc


def test_predict_success_violation(client, mock_model_service):
    mock_model_service.predict.return_value = {"is_violation": True, "probability": 0.95}
    mock_model_service.model = "exists"

    payload = {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 100,
        "name": "Test Item",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["is_violation"] is True


def test_predict_success_no_violation(client, mock_model_service):
    mock_model_service.predict.return_value = {"is_violation": False, "probability": 0.1}
    mock_model_service.model = "exists"

    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Good Item",
        "description": "Desc",
        "category": 1,
        "images_qty": 5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["is_violation"] is False


def test_validation_error(client):
    payload = {
        "seller_id": -5,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Item",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "seller_id"


def test_model_not_loaded(client):
    # Имитируем отсутствие сервиса, установив его в None
    with patch.object(app.state, 'prediction_service', None):
        payload = {
            "seller_id": 1,
            "is_verified_seller": True,
            "item_id": 100,
            "name": "Item",
            "description": "Desc",
            "category": 1,
            "images_qty": 1
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 503
        assert "not currently loaded" in response.json()["detail"]


def test_prediction_internal_error(client, mock_model_service):
    mock_model_service.predict.side_effect = Exception("Sklearn error")
    mock_model_service.model = "exists"

    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Item",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 500
    assert "Internal Server Error" in response.json()["detail"]
