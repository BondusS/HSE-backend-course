from fastapi import FastAPI, Depends
from schemas import Item
from services import PredictionService

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/predict")
async def predict(item: Item) -> bool:
    # Логика вынесена в сервис.
    # Возвращаем bool напрямую, FastAPI преобразует это в json 'true' или 'false'
    return PredictionService.predict_approval(item)
