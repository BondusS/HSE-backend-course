### Инструкция по запуску проекта

---
* Устанавливаем необходимые зависимости
```bash
pip install -r requirements.txt
```
* Создание и обучение модели
```bash
uvicorn main:app --reload
```
* Тесты
```bash
python -m pytest -v
```
