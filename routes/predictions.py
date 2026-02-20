import logging
from fastapi import APIRouter, HTTPException, Request, status, Query
from models.schemas import Item, PredictionResponse
from services.prediction import ItemNotFoundError

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
    Делает предсказание только по ID объявления, делегируя логику сервисному слою.
    """
    logger.info(f"Получен запрос simple_predict для item_id: {item_id}")

    prediction_service = request.app.state.prediction_service
    item_repository = request.app.state.item_repository

    if not prediction_service or prediction_service.model is None:
        logger.error("Модель недоступна для simple_predict.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Модель в данный момент не загружена."
        )

    try:
        result = await prediction_service.simple_predict(item_id, item_repository)
        logger.info(f"Simple prediction result for item_id {item_id}: {result}")
        return result
    except ItemNotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Обработка других неожиданных ошибок из сервисного слоя
        logger.error(f"An unexpected error occurred in simple_predict service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при выполнении предсказания."
        )
