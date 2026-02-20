import asyncio
import json
import logging
from datetime import datetime, timezone
from aiokafka import AIOKafkaProducer

logger = logging.getLogger("moderation_service.kafka_client")

class KafkaProducerClient:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        """Инициализирует и запускает Kafka Producer."""
        logger.info(f"Запуск Kafka Producer с серверами: {self.bootstrap_servers}")
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            loop=asyncio.get_running_loop()
        )
        try:
            await self.producer.start()
            logger.info("Kafka Producer успешно запущен.")
        except Exception as e:
            logger.error(f"Ошибка при запуске Kafka Producer: {e}", exc_info=True)
            raise

    async def stop(self):
        """Останавливает Kafka Producer."""
        if self.producer:
            logger.info("Остановка Kafka Producer.")
            await self.producer.stop()
            logger.info("Kafka Producer остановлен.")

    async def send_moderation_request(self, item_id: int, task_id: int, topic: str = "moderation"):
        """
        Отправляет сообщение о запросе модерации в Kafka-топик.
        Сообщение содержит item_id и timestamp.
        """
        if not self.producer:
            raise RuntimeError("Kafka Producer не запущен.")

        message = {
            "item_id": item_id,
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Отправка сообщения в топик '{topic}': {message}")
        try:
            await self.producer.send_and_wait(topic, message)
            logger.info(f"Сообщение для item_id={item_id}, task_id={task_id} успешно отправлено.")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Kafka для item_id={item_id}, task_id={task_id}: {e}", exc_info=True)
            raise
