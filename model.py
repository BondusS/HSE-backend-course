import os
import pickle
import logging
import numpy as np
from sklearn.linear_model import LogisticRegression

# Настройка логирования для этого модуля
logger = logging.getLogger("moderation_service")

# Константы для MLflow
MLFLOW_Tracking_URI = "sqlite:///mlflow.db"
MLFLOW_EXPERIMENT_NAME = "moderation-experiment"
MLFLOW_MODEL_NAME = "moderation-model"

# Пробуем импортировать MLflow, чтобы сервис не падал, если библиотека не установлена
try:
    import mlflow
    import mlflow.sklearn
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


# Обучаем простую модель на синтетических данных
def train_model():
    logger.info("Training new model on synthetic data...")
    np.random.seed(42)
    # Признаки: [is_verified_seller, images_qty, description_length, category]
    X = np.random.rand(1000, 4)
    # Целевая переменная: 1 = нарушение, 0 = нет нарушения
    y = (X[:, 0] < 0.3) & (X[:, 1] < 0.2)
    y = y.astype(int)

    model = LogisticRegression()
    model.fit(X, y)
    logger.info("Training complete.")
    return model


# Сохраняем модель в локальный файл pickle
def save_model_local(model, path="model.pkl"):
    with open(path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved locally to {path}")


# Загружаем модель из локального файла
def load_model_local(path="model.pkl"):
    if not os.path.exists(path):
        logger.warning(f"Local model file {path} not found.")
        return None
    with open(path, "rb") as f:
        logger.info(f"Model loaded locally from {path}")
        return pickle.load(f)


# Регистрируем модель в MLflow, если она еще не зарегистрирована, и переводим последнюю версию в Production
def setup_mlflow_and_register(model):
    if not MLFLOW_AVAILABLE:
        logger.error("MLflow libraries not installed.")
        return

    # Настройка окружения
    mlflow.set_tracking_uri(MLFLOW_Tracking_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    # Логирование модели
    with mlflow.start_run() as run:
        logger.info("Logging model to MLflow...")
        # log_model сохраняет артефакты и регистрирует модель под именем
        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=MLFLOW_MODEL_NAME
        )

    # Перевод версии в Production
    client = MlflowClient()
    # Получаем последнюю версию модели
    latest_version = client.get_latest_versions(MLFLOW_MODEL_NAME, stages=["None"])[0].version

    client.transition_model_version_stage(
        name=MLFLOW_MODEL_NAME,
        version=latest_version,
        stage="Production"
    )
    logger.info(f"Model version {latest_version} transitioned to Production stage.")


# Загружаем модель из MLflow (stage='Production')
def load_model_mlflow():
    if not MLFLOW_AVAILABLE:
        raise ImportError("MLflow is not installed.")

    mlflow.set_tracking_uri(MLFLOW_Tracking_URI)

    model_uri = f"models:/{MLFLOW_MODEL_NAME}/Production"
    try:
        logger.info(f"Attempting to load model from MLflow URI: {model_uri}")
        model = mlflow.sklearn.load_model(model_uri)
        return model
    except Exception as e:
        logger.error(f"Failed to load model from MLflow: {e}")
        return None


# Основная точка входа, проверяет переменную окружения USE_MLFLOW
def get_model():
    use_mlflow = os.getenv("USE_MLFLOW", "false").lower() == "true"

    if use_mlflow:
        logger.info("USE_MLFLOW=True. Using MLflow registry.")

        # Попытка загрузить существующую модель
        model = load_model_mlflow()

        if model is None:
            logger.info("Production model not found in MLflow. Training and registering new one...")
            model = train_model()
            setup_mlflow_and_register(model)
            # После регистрации снова пробуем загрузить через MLflow API для чистоты эксперимента
            model = load_model_mlflow()

        return model
    else:
        logger.info("USE_MLFLOW=False. Using local file storage.")
        model = load_model_local()
        if model is None:
            logger.info("Local model not found. Training and saving new one...")
            model = train_model()
            save_model_local(model)
        return model
