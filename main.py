from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

app = FastAPI()


class Item(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int = Field(..., ge=0, description="Количество изображений, должно быть >= 0")


class PredictionResponse(BaseModel):
    result: bool


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Обработчик /predict
@app.post("/predict", response_model=PredictionResponse)
async def predict(item: Item):

    if item.images_qty < 0:
        raise HTTPException(status_code=400, detail="Images quantity cannot be negative")

    if item.is_verified_seller:
        is_approved = True
    elif item.images_qty > 0:
        is_approved = True
    else:
        is_approved = False

    # Возвращаем JSON {"result": bool}
    return {"result": is_approved}