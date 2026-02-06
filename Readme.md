## Инструкция по запуску проекта

---

### Устанавливаем необходимые зависимости
```bash
pip install -r requirements.txt
```
```bash
set USE_MLFLOW=true
```
### Поднимаем базу данных Postgres
```bash
docker run --name postgres-bd -e POSTGRES_PASSWORD=paSSw0rd -p 5432:5432 -d postgres
```
Проверяем что контейнер запустился и работает
```bash
docker ps -a
```
### Делаем миграцию
Создаём сеть
```bash
docker network create my-network
```
Подключаем контейнер с базой данных Postgres к сети
```bash
docker network connect my-network postgres-bd
```
Делаем миграцию
```bash
docker run --rm --network=my-network -v "${pwd}:/app" -w /app python:3.12-slim sh -c "pip install alembic asyncpg sqlalchemy && alembic upgrade head" 
```
### Запуск сервера FastAPI
С другого терминала в этой же директории:

Оборачиваем приложене в контейнер, для взаимодействия с базой данных Postgres в сети
```bash
docker build -t hse-backend-app .
```
Запуск серера в сети с базой данных
```bash
docker run --rm --name backend-app-container --network=my-network -p 8000:8000 backend-app
```
### Запуск сервера MlFlow
С другого терминала в этой же директории:
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```
### Тесты
С другого терминала в этой же директории:
```bash
python -m pytest -v
```
### Работоспособность серверов
* FastAPI | http://127.0.0.1:8000/docs#/
* MlFlow | http://127.0.0.1:5000/#/

---

## Версии проекта
* Homework 3 (actual) | 
https://github.com/BondusS/HSE-backend-course
* Homework 2 (исправленно после фидбека) | 
https://github.com/BondusS/HSE-backend-course/tree/30c146bbe25e6ae22db270c1deb570400e0c5af9
* Homework 1 (исправленно после фидбека) | 
https://github.com/BondusS/HSE-backend-course/tree/91a403b70060c3b558d928eea4490813e30661c7
