from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# Проверка корневого эндпоинта
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


# Проверка положительного результата предсказания
def test_predict_verified_seller():
    # Верифицированный продавец -> должно быть True (Одобрено), даже если нет картинок
    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Test Item",
        "description": "Desc",
        "category": 1,
        "images_qty": 0  # 0 картинок, но продавец верифицирован
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() == {"result": True}


# Проверка положительного результата
def test_predict_unverified_with_images():
    # Неверифицированный продавец, но есть картинки -> True
    payload = {
        "seller_id": 2,
        "is_verified_seller": False,
        "item_id": 101,
        "name": "Test Item 2",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() == {"result": True}


# Проверка отрицательного результата предсказания
def test_predict_rejection():
    # Неверифицированный продавец и нет картинок -> False (Отклонено)
    payload = {
        "seller_id": 3,
        "is_verified_seller": False,
        "item_id": 102,
        "name": "Bad Item",
        "description": "Desc",
        "category": 1,
        "images_qty": 0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() == {"result": False}


# Проверка валидации значений (на наличие обязательных аргументов)
def test_validation_error_missing_field():
    # Убрано поле 'seller_id'
    payload = {
        "is_verified_seller": False,
        # seller_id отсутствует
        "item_id": 102,
        "name": "Bad Request",
        "description": "Desc",
        "category": 1,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)

    # FastAPI возвращает 422 Unprocessable Entity при ошибке валидации Pydantic
    assert response.status_code == 422

    # Проверяем, что ошибка именно в отсутствии поля
    data = response.json()
    assert data["detail"][0]["type"] == "missing"
    assert data["detail"][0]["loc"] == ["body", "seller_id"]


# Проверка валидации значений (на соответствие типам)
def test_validation_error_wrong_type():
    # Передана строка вместо int в images_qty
    payload = {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 100,
        "name": "Type Error",
        "description": "Desc",
        "category": 1,
        "images_qty": "три"  # Не число
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["type"] == "int_parsing"


# Проверка обработки ошибки на уровне бизнес-логики
def test_business_logic_error():
    # Передача отрицательного количества картинок
    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Negative Images",
        "description": "Desc",
        "category": 1,
        "images_qty": -5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "greater_than_equal"
