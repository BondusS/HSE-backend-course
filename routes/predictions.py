import logging
from fastapi import APIRouter, HTTPException, Request, status, Query
from models.schemas import Item, PredictionResponse

logger = logging.getLogger("moderation_service.routes")

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(item: Item, request: Request):
    """
    Делает предсказание на основе полных данных об объявлении, переданных в теле запроса.
    """
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
    item_id: int = Query(..., gt=0, description="ID объявления для предсказания.")
):
    """
    Делает предсказание только по ID объявления, получая данные из базы данных.
    """
    logger.info(f"Получен запрос simple_predict для item_id: {item_id}")

    # Получаем сервисы и репозитории из состояния приложения
    prediction_service = request.app.state.prediction_service
    item_repository = request.app.state.item_repository

    # Проверка, загружена ли ML-модель
    if not prediction_service or prediction_service.model is None:
        logger.error("Модель недоступна для simple_predict.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Модель в данный момент не загружена."
        )

    # Получаем данные объявления из БД
    item_data = await item_repository.get_item_with_seller_info(item_id)

    # Если объявление не найдено
    if item_data is None:
        logger.warning(f"Объявление с id {item_id} не найдено в базе данных.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с id {item_id} не найдено."
        )
    
    logger.info(f"Найдены данные в БД: {item_data.model_dump_json()}")

    # Выполняем предсказание
    result = prediction_service.predict(item_data)
    logger.info(f"Результат simple_predict для item_id {item_id}: {result}")
    return result
