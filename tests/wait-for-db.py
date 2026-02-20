import asyncio
import asyncpg
import os
import sys
import subprocess

async def check_db_ready():
    """
    Проверяет готовность базы данных к созданию пула соединений.
    Пытается создать пул в цикле в течение 20 секунд.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.stderr.write("Переменная окружения DATABASE_URL не установлена.\n")
        sys.exit(1)

    print("--- Ожидание готовности базы данных... ---")
    for i in range(20):  # Пытаемся в течение 20 секунд
        try:
            # Пытаемся создать пул, как это делает приложение
            pool = await asyncpg.create_pool(dsn=db_url, timeout=5, min_size=1, max_size=1)
            await pool.close()
            sys.stdout.write("База данных готова! (Пул соединений успешно создан и закрыт)\n")
            return True
        except Exception as e:
            sys.stderr.write(f"Ожидание базы данных... Попытка {i+1}/20. Ошибка: {e}\n")
            await asyncio.sleep(1)
    
    sys.stderr.write("--- База данных недоступна после 20 секунд ожидания. ---\n")
    return False

async def main():
    if await check_db_ready():
        # Если БД готова, запускаем pytest
        print("--- Запуск тестов... ---")
        # Запускаем только интеграционные тесты
        cmd = ["python", "-m", "pytest", "-v", "-m", "integration"]
        # Используем subprocess.run для синхронного запуска pytest
        # Это позволяет избежать проблем с asyncio event loop в pytest
        process = subprocess.run(cmd)
        sys.exit(process.returncode)
    else:
        sys.exit(1)

if __name__ == "__main__":
    # Устанавливаем политику цикла событий для Windows, если это Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
