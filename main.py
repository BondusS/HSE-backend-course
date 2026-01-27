import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from schemas import Item, PredictionResponse
from services import PredictionService
from model import get_model

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("moderation_service")

# Глобальные переменные для хранения состояния (модели/сервиса)
ml_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Загрузка модели при старте
    try:
        model = get_model()
        ml_models["prediction_service"] = PredictionService(model)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        ml_models["prediction_service"] = None

    yield

    # Очистка ресурсов при выключении
    ml_models.clear()
    logger.info("Service shutting down.")


app = FastAPI(lifespan=lifespan)


# Обработчики ошибок

@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal error processing request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error. Please try again later."},
    )


# 422 обрабатывается FastAPI автоматически

# Эндпоинты

@app.post("/predict", response_model=PredictionResponse)
async def predict(item: Item):
    # Логируем входные данные
    logger.info(f"Received request: seller_id={item.seller_id}, item_id={item.item_id}, features={item.model_dump()}")

    service = ml_models.get("prediction_service")

    # Проверка загружена ли модель (503)
    if not service or service.model is None:
        logger.error("Model is not available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not currently loaded."
        )

    # Выполнение предсказания (500 обрабатывается exception_handler, если упадет)
    result = service.predict(item)

    # Логируем результат
    logger.info(f"Prediction result: {result}")

    return result
