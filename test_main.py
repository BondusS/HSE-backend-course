import pytest
from fastapi.testclient import TestClient
from main import app


# Фикстура клиента создается один раз
@pytest.fixture
def client():
    return TestClient(app)


# Проверка корневого эндпоинта
def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


# Параметризация для проверки бизнес-логики
@pytest.mark.parametrize("verified, images, expected_result", [
    (True, 0, True),  # Верифицирован, нет фото -> Одобрено
    (True, 5, True),  # Верифицирован, есть фото -> Одобрено
    (False, 1, True),  # Не верифицирован, есть фото -> Одобрено
    (False, 0, False),  # Не верифицирован, нет фото -> Отклонено
])
def test_predict_logic(client, verified, images, expected_result):
    payload = {
        "seller_id": 1,
        "is_verified_seller": verified,
        "item_id": 100,
        "name": "Test Item",
        "description": "Desc",
        "category": 1,
        "images_qty": images
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    # Проверяем, что возвращается сырое булево значение (в requests.json() это True/False)
    assert response.json() is expected_result


# Параметризация для проверки валидации полей (ошибки 422)
@pytest.mark.parametrize("invalid_field, invalid_value, error_type", [
    ("seller_id", 0, "greater_than"),  # seller_id должен быть > 0
    ("seller_id", -5, "greater_than"),
    ("item_id", 0, "greater_than"),
    ("images_qty", -1, "greater_than_equal"),  # images_qty >= 0
    ("name", "", "string_too_short"),  # Пустое имя
    ("images_qty", "string", "int_parsing")  # Неверный тип данных
])
def test_validation_errors(client, invalid_field, invalid_value, error_type):
    # Базовый валидный пейлоад
    payload = {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 100,
        "name": "Valid Name",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }

    # Подменяем поле на невалидное
    payload[invalid_field] = invalid_value

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    data = response.json()
    # Проверяем тип ошибки и поле, в котором она возникла
    error_detail = data["detail"][0]
    assert error_detail["type"] == error_type
    assert error_detail["loc"][-1] == invalid_field


# Проверка на пропущенное поле в структуре запроса
def test_missing_field(client):
    payload = {
        # seller_id отсутствует
        "is_verified_seller": False,
        "item_id": 100,
        "name": "Test",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
