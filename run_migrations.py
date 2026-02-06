import logging
import psycopg2
import os
from pgmigrate import migrate, CONFIG_DEFAULTS, _init_cursor, _get_database_user, _get_callbacks

# Настраиваем логирование для вывода информации
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s: %(message)s')

def main():
    """
    Запускает миграцию базы данных, подключаясь через psycopg2 напрямую,
    передавая параметры как именованные аргументы, чтобы избежать проблем с парсингом DSN.
    """
    conn_instance = None
    try:
        print("Попытка прямого подключения через psycopg2 с использованием именованных аргументов...")
        
        # Это самый фундаментальный способ подключения, который обходит любой парсинг строк.
        conn_instance = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="postgres",
            user="postgres",
            password="paSSw0rd"
        )
        
        print("Соединение успешно установлено!")

        # Теперь, когда у нас есть валидное соединение, собираем объект конфигурации,
        # который нужен функции `migrate` для выполнения ее работы.
        base_dir = os.path.abspath('.')
        config = CONFIG_DEFAULTS._replace(
            base_dir=base_dir,
            target='latest',
            schema='public',
            disable_schema_check=True
        )
        
        cursor = _init_cursor(conn_instance, config.session)
        user = _get_database_user(cursor)
        callbacks = _get_callbacks(config.callbacks, config.base_dir)

        # Собираем финальный, полный объект конфигурации для функции migrate
        final_config = config._replace(
            conn_instance=conn_instance,
            cursor=cursor,
            user=user,
            callbacks=callbacks
        )

        print("Конфигурация и соединение успешны. Запускаем миграцию...")
        migrate(final_config)
        print("Миграция успешно завершена.")

    except Exception as e:
        logging.error("Во время миграции произошла ошибка: %s", e, exc_info=True)
        # Перевыбрасываем исключение, чтобы было понятно, что скрипт не удался
        raise
    finally:
        # Гарантируем, что соединение будет закрыто в любом случае
        if conn_instance:
            conn_instance.close()
            print("Соединение закрыто.")

if __name__ == '__main__':
    main()
