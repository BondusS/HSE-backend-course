# Используем официальный базовый образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости
# --no-cache-dir чтобы не хранить кэш и уменьшить размер образа
RUN pip install --no-cache-dir -r requirements.txt

# Копируем alembic.ini и директорию с миграциями
COPY alembic.ini .
COPY alembic ./alembic

# Копируем скрипт ожидания БД
COPY tests/wait-for-db.py .

# Копируем остальной код проекта в рабочую директорию
COPY . .

# Указываем команду для запуска приложения
# --host 0.0.0.0 делает приложение доступным извне контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
