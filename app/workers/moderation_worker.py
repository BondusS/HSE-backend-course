import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import asyncpg

# Import project-specific modules
from services.prediction import PredictionService, ItemNotFoundError
from repositories.items import ItemRepository
from repositories.moderation_results import ModerationResultRepository
from model import get_model # To load the ML model

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("moderation_worker")

# Configuration from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:paSSw0rd@postgres-db:5432/postgres")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")
MODERATION_TOPIC = "moderation"
DLQ_TOPIC = "moderation_dlq"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

class WorkerDependencies:
    """Helper class to hold worker dependencies (DB pool, repos, ML model, Kafka producer)."""
    def __init__(self):
        self.db_pool: asyncpg.Pool | None = None
        self.item_repo: ItemRepository | None = None
        self.moderation_repo: ModerationResultRepository | None = None
        self.prediction_service: PredictionService | None = None
        self.kafka_producer: AIOKafkaProducer | None = None

    async def initialize(self):
        logger.info("Инициализация зависимостей воркера...")
        # DB Pool
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL)
            self.item_repo = ItemRepository(self.db_pool)
            self.moderation_repo = ModerationResultRepository(self.db_pool)
            logger.info("Пул соединений с БД для воркера создан.")
        except Exception as e:
            logger.error(f"Ошибка инициализации пула БД для воркера: {e}", exc_info=True)
            sys.exit(1)

        # ML Model
        try:
            model = get_model()
            self.prediction_service = PredictionService(model)
            logger.info("ML модель для воркера загружена.")
        except Exception as e:
            logger.error(f"Ошибка загрузки ML модели для воркера: {e}", exc_info=True)
            sys.exit(1)

        # Kafka Producer (for DLQ/retries)
        self.kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            loop=asyncio.get_running_loop()
        )
        try:
            await self.kafka_producer.start()
            logger.info("Kafka Producer для DLQ/retries запущен.")
        except Exception as e:
            logger.error(f"Ошибка запуска Kafka Producer для DLQ/retries: {e}", exc_info=True)
            sys.exit(1)

    async def shutdown(self):
        logger.info("Остановка зависимостей воркера...")
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Пул соединений с БД для воркера закрыт.")
        if self.kafka_producer:
            await self.kafka_producer.stop()
            logger.info("Kafka Producer для DLQ/retries остановлен.")

async def process_message(msg, deps: WorkerDependencies):
    """Обрабатывает одно сообщение из Kafka."""
    message_data = {} # Инициализация для избежания UnboundLocalError
    task_id = None
    item_id = None
    try:
        message_data = json.loads(msg.value.decode('utf-8'))
        item_id = message_data.get("item_id")
        task_id = message_data.get("task_id")
        retry_count = message_data.get("retry_count", 0)

        if item_id is None or task_id is None:
            raise ValueError(f"Некорректное сообщение: item_id или task_id отсутствуют. Сообщение: {message_data}")

        logger.info(f"Обработка сообщения: item_id={item_id}, task_id={task_id}, retry={retry_count}")

        # Проверяем, что зависимости инициализированы
        if not all([deps.item_repo, deps.moderation_repo, deps.prediction_service, deps.kafka_producer]):
            raise RuntimeError("Зависимости воркера не инициализированы.")

        # 1. Получаем данные объявления из БД
        item_data = await deps.item_repo.get_item_with_seller_info(item_id)
        if item_data is None:
            raise ItemNotFoundError(f"Объявление с id {item_id} не найдено в БД.")

        # 2. Вызываем ML-сервис для предсказания
        prediction_result = deps.prediction_service.predict(item_data)
        is_violation = prediction_result["is_violation"]
        probability = prediction_result["probability"]

        # 3. Обновляем запись в moderation_results
        await deps.moderation_repo.update_result(
            task_id,
            "completed",
            is_violation=is_violation,
            probability=probability,
            error_message=None
        )
        logger.info(f"Задача task_id={task_id} для item_id={item_id} успешно завершена. Результат: {prediction_result}")

    except ItemNotFoundError as e:
        error_msg = str(e)
        logger.warning(f"Ошибка обработки task_id={task_id}: {error_msg}")
        await handle_error(message_data, error_msg, retry_count, deps)
    except Exception as e:
        error_msg = f"Непредвиденная ошибка при обработке task_id={task_id}: {e}"
        logger.error(error_msg, exc_info=True)
        await handle_error(message_data, error_msg, retry_count, deps)

async def handle_error(original_message_data: dict, error_msg: str, current_retry_count: int, deps: WorkerDependencies):
    """Обрабатывает ошибки, реализуя логику повторных попыток или отправку в DLQ."""
    task_id = original_message_data.get("task_id")
    item_id = original_message_data.get("item_id")

    if current_retry_count < MAX_RETRIES:
        next_retry_count = current_retry_count + 1
        logger.warning(f"Повторная попытка для task_id={task_id}, item_id={item_id}. Попытка {next_retry_count}/{MAX_RETRIES}. Задержка {RETRY_DELAY_SECONDS}с.")
        
        # Обновляем статус в БД на "retrying" (или оставляем "pending" и просто логируем)
        # Для простоты оставим "pending" и будем полагаться на retry_count в сообщении
        
        # Отправляем сообщение обратно в основной топик с увеличенным счетчиком
        retry_message = original_message_data.copy()
        retry_message["retry_count"] = next_retry_count
        retry_message["last_error"] = error_msg
        
        # Используем asyncio.sleep для задержки перед отправкой
        await asyncio.sleep(RETRY_DELAY_SECONDS)
        await deps.kafka_producer.send_and_wait(MODERATION_TOPIC, retry_message)
        
    else:
        logger.error(f"Достигнуто максимальное количество повторных попыток для task_id={task_id}, item_id={item_id}. Отправка в DLQ.")
        # Обновляем статус в БД на "failed"
        await deps.moderation_repo.update_result(
            task_id,
            "failed",
            error_message=f"Макс. попыток ({MAX_RETRIES}) исчерпано: {error_msg}"
        )
        # Отправляем в DLQ
        dlq_message = {
            "original_message": original_message_data,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retry_count": current_retry_count
        }
        await deps.kafka_producer.send_and_wait(DLQ_TOPIC, dlq_message)

async def consume_messages(deps: WorkerDependencies):
    """Основная функция потребителя Kafka."""
    consumer = AIOKafkaConsumer(
        MODERATION_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="moderation_workers_group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest", # Начинаем читать с самого начала, если нет сохраненного оффсета
        enable_auto_commit=True,
        loop=asyncio.get_running_loop()
    )
    logger.info(f"Запуск Kafka Consumer для топика '{MODERATION_TOPIC}'...")
    try:
        await consumer.start()
        logger.info("Kafka Consumer успешно запущен.")
        async for msg in consumer:
            logger.info(f"Получено сообщение: Topic={msg.topic}, Partition={msg.partition}, Offset={msg.offset}, Key={msg.key}, Value={msg.value}")
            await process_message(msg, deps)
    except Exception as e:
        logger.error(f"Критическая ошибка в Kafka Consumer: {e}", exc_info=True)
    finally:
        logger.info("Остановка Kafka Consumer.")
        await consumer.stop()

async def main_worker():
    deps = WorkerDependencies()
    await deps.initialize()
    try:
        await consume_messages(deps)
    finally:
        await deps.shutdown()

if __name__ == "__main__":
    # Устанавливаем политику цикла событий для Windows, если необходимо
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main_worker())
