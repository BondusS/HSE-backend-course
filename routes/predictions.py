import logging
from fastapi import APIRouter, HTTPException, Request, status, Query, Depends
from models.schemas import Item, PredictionResponse, Account
from services.prediction import ItemNotFoundError
from pydantic import BaseModel
from app.dependencies import get_current_account

logger = logging.getLogger("moderation_service.routes")

router = APIRouter()

class AsyncModerationResponse(BaseModel):
    task_id: int
    status: str
    message: str

class ModerationStatusResponse(BaseModel):
    task_id: int
    status: str
    is_violation: bool | None = None
    probability: float | None = None
    error_message: str | None = None


@router.post("/predict", response_model=PredictionResponse)
async def predict(item: Item, request: Request, current_account: Account = Depends(get_current_account)):
    logger.info(f"Получен запрос: seller_id={item.seller_id}, item_id={item.item_id}")
    service = request.app.state.prediction_service
    if not service or service.model is None:
        logger.error("Модель недоступна.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Модель в данный момент не загружена."
        )
    result = service.predict(item)
    logger.info(f"Результат предсказания: {result}")
    return result


@router.post("/simple_predict", response_model=PredictionResponse)
async def simple_predict(
    request: Request,
    item_id: int = Query(..., gt=0, description="ID объявления для предсказания."),
    current_account: Account = Depends(get_current_account)
):
    logger.info(f"Получен запрос simple_predict для item_id: {item_id}")
    prediction_service = request.app.state.prediction_service
    item_repository = request.app.state.item_repository
    redis_repository = request.app.state.redis_repository
    cache_key = f"prediction:{item_id}"
    cached_result = await redis_repository.get(cache_key)
    if cached_result:
        logger.info(f"Результат для item_id {item_id} найден в кэше.")
        return PredictionResponse(**cached_result)
    logger.info(f"Результат для item_id {item_id} не найден в кэше, выполняем предсказание.")
    if not prediction_service or prediction_service.model is None:
        logger.error("Модель недоступна для simple_predict.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Модель в данный момент не загружена."
        )
    try:
        result = await prediction_service.simple_predict(item_id, item_repository)
        logger.info(f"Simple prediction result for item_id {item_id}: {result}")
        await redis_repository.set(cache_key, result.dict(), ttl=3600)
        logger.info(f"Результат для item_id {item_id} сохранен в кэш.")
        return result
    except ItemNotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred in simple_predict service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при выполнении предсказания."
        )


@router.post("/async_predict", response_model=AsyncModerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def async_predict(
    request: Request,
    item_id: int = Query(..., gt=0, description="ID объявления для асинхронной модерации."),
    current_account: Account = Depends(get_current_account)
):
    logger.info(f"Получен запрос async_predict для item_id: {item_id}")
    item_repository = request.app.state.item_repository
    moderation_repo = request.app.state.moderation_result_repository
    kafka_producer = request.app.state.kafka_producer
    item_exists = await item_repository.get_item_with_seller_info(item_id)
    if not item_exists:
        logger.warning(f"Объявление с id {item_id} не найдено для асинхронной модерации.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с id {item_id} не найдено."
        )
    task_id = await moderation_repo.create_pending_result(item_id)
    logger.info(f"Создана задача модерации task_id={task_id} для item_id={item_id}.")
    try:
        await kafka_producer.send_moderation_request(item_id=item_id, task_id=task_id, topic="moderation")
        logger.info(f"Сообщение о модерации для task_id={task_id} отправлено в Kafka.")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение в Kafka для task_id={task_id}: {e}", exc_info=True)
        await moderation_repo.update_result(task_id, "failed", error_message=f"Ошибка Kafka: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить запрос модерации в очередь."
        )
    return AsyncModerationResponse(
        task_id=task_id,
        status="pending",
        message="Moderation request accepted"
    )


@router.get("/moderation_result/{task_id}", response_model=ModerationStatusResponse)
async def get_moderation_result(task_id: int, request: Request, current_account: Account = Depends(get_current_account)):
    logger.info(f"Получен запрос статуса модерации для task_id: {task_id}")
    moderation_repo = request.app.state.moderation_result_repository
    redis_repository = request.app.state.redis_repository
    cache_key = f"moderation_result:{task_id}"
    cached_result = await redis_repository.get(cache_key)
    if cached_result:
        logger.info(f"Результат для task_id={task_id} найден в кэше.")
        return ModerationStatusResponse(**cached_result)
    logger.info(f"Результат для task_id={task_id} не найден в кэше, запрашиваем из БД.")
    result = await moderation_repo.get_result_by_id(task_id)
    if not result:
        logger.warning(f"Задача модерации с task_id={task_id} не найдена.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача модерации с task_id={task_id} не найдена."
        )
    if result.get("status") != "pending":
        logger.info(f"Результат для task_id={task_id} является финальным, кэшируем его.")
        await redis_repository.set(cache_key, dict(result), ttl=3600)
    return ModerationStatusResponse(**result)
