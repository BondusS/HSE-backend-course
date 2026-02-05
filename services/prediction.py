import numpy as np
from models.schemas import Item


class PredictionService:
    def __init__(self, model):
        self.model = model

    def predict(self, item: Item) -> dict:
        if self.model is None:
            raise RuntimeError("Model is not loaded")

        # Преобразование признаков
        feat_verified = 1.0 if item.is_verified_seller else 0.0
        feat_images = item.images_qty / 10.0
        feat_desc_len = len(item.description) / 1000.0
        feat_category = item.category / 100.0

        # Формируем вектор признаков (порядок важен и должен совпадать с обучением в model.py)
        # [is_verified_seller, images_qty, description_length, category]
        features = np.array([[feat_verified, feat_images, feat_desc_len, feat_category]])

        try:
            # Предсказание класса (0 или 1)
            prediction = self.model.predict(features)[0]
            proba = self.model.predict_proba(features)[0][1]

            return {
                "is_violation": bool(prediction == 1),
                "probability": float(proba)
            }
        except Exception as e:
            # Пробрасываем ошибку выше, чтобы main.py её поймал
            raise e
