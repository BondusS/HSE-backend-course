import os
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression

# Попытка импорта MLflow, чтобы код не падал, если библиотека не установлена
try:
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

MODEL_PATH = "model.pkl"


# Обучаем простую модель на синтетических данных
def train_model():
    np.random.seed(42)
    # Признаки: [is_verified_seller, images_qty, description_length, category]
    X = np.random.rand(1000, 4)

    y = (X[:, 0] < 0.3) & (X[:, 1] < 0.2)  # Целевая переменная: 1 = нарушение, 0 = нет нарушения
    y = y.astype(int)

    model = LogisticRegression()
    model.fit(X, y)
    return model


def save_model_local(model, path=MODEL_PATH):
    with open(path, "wb") as f:
        pickle.dump(model, f)


def load_model_local(path=MODEL_PATH):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_model_mlflow(model_name="moderation-model", stage="Production"):
    if not MLFLOW_AVAILABLE:
        raise ImportError("MLflow not installed")

    model_uri = f"models:/{model_name}/{stage}"
    return mlflow.sklearn.load_model(model_uri)


# Универсальная функция получения модели. Проверяет переменную окружения USE_MLFLOW
def get_model():
    use_mlflow = os.getenv("USE_MLFLOW", "false").lower() == "true"

    if use_mlflow:
        print("Loading model from MLflow...")
        try:
            return load_model_mlflow()
        except Exception as e:
            print(f"Failed to load from MLflow: {e}. Fallback to local.")

    # Локальная загрузка/обучение
    if not os.path.exists(MODEL_PATH):
        print("Model file not found. Training new model...")
        model = train_model()
        save_model_local(model)

    print(f"Loading model from {MODEL_PATH}...")
    return load_model_local()
