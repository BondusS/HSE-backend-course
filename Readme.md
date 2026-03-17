## Инструкция по запуску проекта

---

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```
При необходимости работы с MLflow, установите переменную окружения:
```bash
set USE_MLFLOW=true
```

### 2. Запуск всех сервисов
Команда запустит FastAPI, Postgres, Redis, Redpanda, Prometheus и Grafana.
```bash
docker-compose up --build -d
```
**Конфигурация БД:**
- **Хост:** `localhost`
- **Порт:** `5435`
- **Пользователь:** `postgres`
- **Пароль:** `postgres`
- **Имя БД:** `hw`

### 3. Применение миграций базы данных
После запуска контейнеров, примените миграции для создания таблиц в базе данных.
```bash
docker-compose exec backend-app alembic upgrade head
```

### 4. Авторизация
Для доступа к эндпоинтам предсказаний требуется авторизация.

**Шаг 1: Создайте пользователя**
Подразумевается, что таблица `account` заполняется извне. Для тестирования вы можете создать пользователя, запустив интеграционные тесты (`pytest -m integration`), которые создают тестовый аккаунт, или добавив запись в таблицу `account` вручную.

**Шаг 2: Получите токен**
Отправьте POST-запрос на эндпоинт `/login` с вашим логином и паролем.
```bash
# Замените testuser и testpassword на актуальные данные
curl -X POST "http://localhost:8000/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser&password=testpassword" -c cookies.txt
```
В ответ вы получите JWT-токен, который также будет сохранен в `HttpOnly` cookie `access_token`.

**Шаг 3: Выполните запрос к защищенному эндпоинту**
Используйте полученные cookie для аутентификации при последующих запросах.
```bash
# Пример запроса к защищенному эндпоинту
curl -X POST "http://localhost:8000/simple_predict?item_id=1" -b cookies.txt
```

### 5. Тестирование
Для запуска всех тестов:
```bash
docker-compose -f docker-compose.tests.yml up --build --abort-on-container-exit
```
Для запуска только интеграционных тестов (требуют запущенной инфраструктуры):
```bash
pytest -m integration
```
Для запуска только юнит-тестов:
```bash
pytest -m "not integration"
```

### 6. Доступные сервисы
* **FastAPI (документация)**: http://127.0.0.1:8000/docs
* **FastAPI (метрики)**: http://127.0.0.1:8000/metrics
* **Redpanda Console**: http://127.0.0.1:8080/
* **Prometheus**: http://127.0.0.1:9090/
* **Grafana**: http://127.0.0.1:3000/ (логин: `admin`, пароль: `admin`)
* **MLflow UI** (если используется): http://127.0.0.1:5000/

---

## Настройка мониторинга в Grafana

1.  **Войдите в Grafana**:
    *   Перейдите по адресу http://localhost:3000.
    *   Используйте логин `admin` и пароль `admin`.

2.  **Подключите Prometheus как источник данных**:
    *   Перейдите в `Connections` → `Data Sources` → `Add data source`.
    *   Выберите `Prometheus`.
    *   В поле `Prometheus server URL` укажите `http://prometheus:9090`.
    *   Нажмите `Save & Test`.

3.  **Создайте дашборд**:
    *   Перейдите в `Dashboards` → `New` → `New dashboard`.
    *   Нажмите `Add visualization` для создания панелей.

### Примеры PromQL-запросов для панелей

*   **RPS (запросов в секунду)**:
    ```promql
    sum(rate(http_requests_total[1m])) by (handler)
    ```
*   **Латентность запросов (p95)**:
    ```promql
    histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))
    ```
*   **Частота ошибок сервера (5xx)**:
    ```promql
    (sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))) * 100
    ```
*   **Количество предсказаний (violation vs no_violation)**:
    ```promql
    sum(rate(predictions_total[5m])) by (result)
    ```
*   **Время инференса ML-модели (p95)**:
    ```promql
    histogram_quantile(0.95, sum(rate(prediction_duration_seconds_bucket[5m])) by (le))
    ```
*   **Время выполнения запросов к БД (p95)**:
    ```promql
    histogram_quantile(0.95, sum(rate(db_query_duration_seconds_bucket[5m])) by (le, query_type))
    ```

---

## Версии проекта
* Homework 7 (актуальная версия) | https://github.com/BondusS/HSE-backend-course
* Homework 6 (версия без ревью) | https://github.com/BondusS/HSE-backend-course/tree/895e36e8d71d4e87fc6bb6c0d3c03191c5bbee6d
* Homework 5 (версия без ревью) | https://github.com/BondusS/HSE-backend-course/tree/fce182f4ac0f4a277c1f11d147b135d1c4893576
* Homework 4 (с корректировками после ревью) | https://github.com/BondusS/HSE-backend-course/tree/c031f4633af9dc81bcd1516f9a94542ba6a89fda
* Homework 3 (исправленно после фидбека) | https://github.com/BondusS/HSE-backend-course/tree/fefab2d0a4174bbd06ea2aa184b332f961500372
* Homework 2 (исправленно после фидбека) | https://github.com/BondusS/HSE-backend-course/tree/30c146bbe25e6ae22db270c1deb570400e0c5af9
* Homework 1 (исправленно после фидбека) | https://github.com/BondusS/HSE-backend-course/tree/91a403b70060c3b558d928eea4490813e30661c7
