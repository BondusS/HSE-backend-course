import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from services.prediction import PredictionService
from model import get_model
from routes.predictions import router as predictions_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("moderation_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Загрузка модели при старте
    try:
        model = get_model()
        app.state.prediction_service = PredictionService(model)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        app.state.prediction_service = None

    yield

    # Очистка ресурсов при выключении
    app.state.prediction_service = None
    logger.info("Service shutting down.")


app = FastAPI(lifespan=lifespan)

# Подключение роутера
app.include_router(predictions_router)


# Обработчики ошибок

@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal error processing request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error. Please try again later."},
    )
