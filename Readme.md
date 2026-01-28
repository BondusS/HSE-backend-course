## Инструкция по запуску проекта

---

#### Устанавливаем необходимые зависимости
```bash
pip install -r requirements.txt
```
```bash
set USE_MLFLOW=true
```
#### Запуск сервера FastAPI
```bash
uvicorn main:app --reload
```
#### Запуск сервера MlFlow
С другого терминала в этой же директории:
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```
#### Тесты
С другого терминала в этой же директории:
```bash
python -m pytest -v
```
#### Работоспособность серверов
* FastAPI | http://127.0.0.1:8000/docs#/
* MlFlow | http://127.0.0.1:5000/#/

---

### Версии проекта
* Homework 2 (actual) | https://github.com/BondusS/HSE-backend-course
* Homework 1 (исправленно после фидбека) | https://github.com/BondusS/HSE-backend-course/tree/91a403b70060c3b558d928eea4490813e30661c7
