## Инструкция по запуску проекта

---

### Устанавливаем необходимые зависимости
```bash
pip install -r requirements.txt
```
```bash
set USE_MLFLOW=true
```
### Запуск сервера FastAPI и базы данных Postgres в сети Docker Compose
```bash
docker-compose up --build
```
### Запуск сервера MlFlow
С другого терминала в этой же директории:
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```
### Запуск миграции
```bash
docker-compose build backend-app
```
```bash
docker-compose run --rm backend-app alembic upgrade head
```
### Тесты
С другого терминала в этой же директории:
```bash
docker-compose -f docker-compose.tests.yml build backend-tests 
```
```bash
docker-compose -f docker-compose.tests.yml up --build --abort-on-container-exit 
```
### Работоспособность серверов
* FastAPI | http://127.0.0.1:8000/docs#/
* MlFlow | http://127.0.0.1:5000/

---

## Версии проекта
* Homework 3 (actual) | 
https://github.com/BondusS/HSE-backend-course
* Homework 2 (исправленно после фидбека) | 
https://github.com/BondusS/HSE-backend-course/tree/30c146bbe25e6ae22db270c1deb570400e0c5af9
* Homework 1 (исправленно после фидбека) | 
https://github.com/BondusS/HSE-backend-course/tree/91a403b70060c3b558d928eea4490813e30661c7
