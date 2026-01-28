import mimetypes
import sys
from mlflow.cli import server

# Принудительно исправляем MIME-тип для JS
mimetypes.add_type("application/javascript", ".js")
mimetypes.init()

if __name__ == "__main__":
    # Эмулируем аргументы командной строки
    sys.argv = ["mlflow ui --backend-store-uri sqlite:///mlflow.db"]
    server()
