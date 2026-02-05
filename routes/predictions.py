import logging
from fastapi import APIRouter, HTTPException, Request, status
from models.schemas import Item, PredictionResponse

logger = logging.getLogger("moderation_service.routes")

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(item: Item, request: Request):
    # Логируем входные данные
    logger.info(f"Received request: seller_id={item.seller_id}, item_id={item.item_id}, features={item.model_dump()}")

    service = request.app.state.prediction_service

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
