import logging
import asyncio
import sys
import os
from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from services.prediction import PredictionService
from model import get_model
from routes.predictions import router as predictions_router
from routes.management import router as management_router
from repositories.items import ItemRepository
from repositories.users import UserRepository
from repositories.moderation_results import ModerationResultRepository
from app.clients.kafka import KafkaProducerClient # Импортируем Kafka Producer

# Решение для известной проблемы с asyncio и Docker в Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("moderation_service")

# Получаем строку подключения из переменной окружения.
# Имя хоста 'postgres-db' соответствует имени сервиса в docker-compose.yml.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:paSSw0rd@postgres-db:5432/postgres"
)

# Получаем адрес Kafka брокера из переменной окружения
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "redpanda:29092" # Имя сервиса Redpanda в Docker Compose
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Код при старте приложения ---
    logger.info(f"Подключаемся к базе данных по адресу: {DATABASE_URL.split('@')[-1]}")
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        app.state.pool = pool
        logger.info("Пул соединений с базой данных успешно создан.")
    except Exception as e:
        logger.error(f"Не удалось создать пул соединений с базой данных: {e}")
        app.state.pool = None
        raise

    # Инициализируем репозитории
    app.state.item_repository = ItemRepository(app.state.pool)
    app.state.user_repository = UserRepository(app.state.pool)
    app.state.moderation_result_repository = ModerationResultRepository(app.state.pool) # Новый репозиторий

    # Инициализируем и запускаем Kafka Producer
    app.state.kafka_producer = KafkaProducerClient(KAFKA_BOOTSTRAP_SERVERS)
    try:
        await app.state.kafka_producer.start()
    except Exception as e:
        logger.error(f"Не удалось запустить Kafka Producer: {e}")
        app.state.kafka_producer = None
        raise

    # Загрузка ML-модели
    try:
        model = get_model()
        app.state.prediction_service = PredictionService(model)
        logger.info("Модель успешно загружена.")
    except Exception as e:
        logger.error(f"Не удалось загрузить модель: {e}")
        app.state.prediction_service = None
    
    yield

    # --- Код при выключении приложения ---
    if app.state.pool:
        await app.state.pool.close()
        logger.info("Пул соединений с базой данных закрыт.")
    
    if app.state.kafka_producer:
        await app.state.kafka_producer.stop()
    
    app.state.prediction_service = None
    logger.info("Сервис выключается.")


app = FastAPI(lifespan=lifespan)

# Подключение роутеров
app.include_router(predictions_router)
app.include_router(management_router)


# Обработчики ошибок
@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    logger.error(f"Внутренняя ошибка при обработке запроса {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера. Пожалуйста, попробуйте позже."},
    )
