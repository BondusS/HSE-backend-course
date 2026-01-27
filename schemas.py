from pydantic import BaseModel, Field, ConfigDict

class Item(BaseModel):
    seller_id: int = Field(..., gt=0, description="ID продавца, должен быть > 0")
    is_verified_seller: bool
    item_id: int = Field(..., gt=0, description="ID товара, должен быть > 0")
    name: str = Field(..., min_length=1, max_length=100, description="Название товара")
    description: str = Field(..., max_length=1000, description="Описание товара")
    category: int = Field(..., gt=0, description="Категория товара")
    images_qty: int = Field(..., ge=0, description="Количество изображений, должно быть >= 0")

class PredictionResponse(BaseModel):
    is_violation: bool
    probability: float
