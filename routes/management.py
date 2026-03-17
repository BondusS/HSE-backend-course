import logging
from fastapi import APIRouter, HTTPException, Request, status, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("moderation_service.routes.management")

router = APIRouter()

# --- Модели для создания ---

class UserCreate(BaseModel):
    is_verified_seller: bool

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str
    category: int = Field(..., gt=0)
    images_qty: int = Field(..., ge=0)
    seller_id: int = Field(..., gt=0)

# --- Ручки для создания ---

@router.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, request: Request):
    """
    Создает нового пользователя.
    """
    user_repo = request.app.state.user_repository
    try:
        user_id = await user_repo.create_user(is_verified=user_data.is_verified_seller)
        logger.info(f"Создан новый пользователь с ID: {user_id}")
        return {"id": user_id, "is_verified_seller": user_data.is_verified_seller}
    except Exception as e:
        logger.error(f"Не удалось создать пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя.")

@router.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item_data: ItemCreate, request: Request):
    """
    Создает новое объявление.
    """
    item_repo = request.app.state.item_repository
    try:
        item_id = await item_repo.create_item(
            name=item_data.name,
            description=item_data.description,
            category=item_data.category,
            images_qty=item_data.images_qty,
            seller_id=item_data.seller_id,
        )
        logger.info(f"Создано новое объявление с ID: {item_id}")
        return {"id": item_id, **item_data.model_dump()}
    except Exception as e:
        if "violates foreign key constraint" in str(e):
            logger.warning(f"Попытка создать объявление с несуществующим seller_id: {item_data.seller_id}")
            raise HTTPException(status_code=404, detail=f"Пользователь с ID {item_data.seller_id} не найден.")
        
        logger.error(f"Не удалось создать объявление: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при создании объявления.")

@router.post("/close", status_code=status.HTTP_200_OK)
async def close_item(
    request: Request,
    item_id: int = Query(..., gt=0, description="ID объявления для закрытия.")
):
    """
    Закрывает объявление и удаляет связанные с ним кэшированные предсказания.
    """
    logger.info(f"Получен запрос на закрытие объявления с ID: {item_id}")

    item_repo = request.app.state.item_repository
    redis_repo = request.app.state.redis_repository

    # 1. Помечаем объявление как закрытое в PostgreSQL
    closed_item_id = await item_repo.close_item(item_id)
    if not closed_item_id:
        logger.warning(f"Объявление с ID {item_id} не найдено для закрытия.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с ID {item_id} не найдено."
        )

    logger.info(f"Объявление с ID {item_id} помечено как закрытое в PostgreSQL.")

    # 2. Удаляем кэш предсказаний из Redis
    prediction_cache_key = f"prediction:{item_id}"
    await redis_repo.delete(prediction_cache_key)
    logger.info(f"Кэш предсказаний для item_id={item_id} удален из Redis.")

    # 3. Находим и удаляем все связанные результаты модерации из кэша
    # Это более сложная операция, так как мы не знаем task_id напрямую.
    # В данном случае, мы оставим эту логику для улучшения в будущем,
    # так как для этого потребуется изменение структуры хранения кэша.
    # Пока что, удаляем только кэш предсказаний.

    return {"message": f"Объявление {item_id} успешно закрыто."}
