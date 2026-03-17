import numpy as np
import time
from models.schemas import Item
from repositories.items import ItemRepository
from app.metrics import PREDICTIONS_TOTAL, PREDICTION_DURATION, PREDICTION_ERRORS_TOTAL, MODEL_PREDICTION_PROBABILITY

class ItemNotFoundError(Exception):
    """Кастомное исключение для случаев, когда объявление не найдено в базе данных."""
    pass

class PredictionService:
    def __init__(self, model):
        self.model = model

    def predict(self, item: Item) -> dict:
        """Синхронный метод, выполняющий только расчеты по данным модели."""
        if self.model is None:
            PREDICTION_ERRORS_TOTAL.labels(error_type="model_unavailable").inc()
            raise RuntimeError("Модель не загружена")

        # Преобразование признаков
        feat_verified = 1.0 if item.is_verified_seller else 0.0
        feat_images = item.images_qty / 10.0
        feat_desc_len = len(item.description) / 1000.0
        feat_category = item.category / 100.0

        features = np.array([[feat_verified, feat_images, feat_desc_len, feat_category]])

        try:
            start_time = time.time()
            prediction = self.model.predict(features)[0]
            proba = self.model.predict_proba(features)[0][1]
            end_time = time.time()

            PREDICTION_DURATION.observe(end_time - start_time)
            MODEL_PREDICTION_PROBABILITY.observe(proba)

            result = "violation" if prediction == 1 else "no_violation"
            PREDICTIONS_TOTAL.labels(result=result).inc()

            return {
                "is_violation": bool(prediction == 1),
                "probability": float(proba)
            }
        except Exception as e:
            PREDICTION_ERRORS_TOTAL.labels(error_type="prediction_error").inc()
            raise e

    async def simple_predict(self, item_id: int, item_repository: ItemRepository) -> dict:
        """
        Оркестрирует получение данных и предсказание.
        1. Получает данные из репозитория.
        2. Вызывает основной метод predict.
        """
        # Получаем данные объявления из БД
        item_data = await item_repository.get_item_with_seller_info(item_id)

        # Если объявление не найдено, выбрасываем кастомное исключение
        if item_data is None:
            raise ItemNotFoundError(f"Объявление с id {item_id} не найдено.")
        
        # Выполняем предсказание, используя основной синхронный метод
        return self.predict(item_data)
