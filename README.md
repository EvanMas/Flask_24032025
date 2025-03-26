# Установка и запуск Flask-проекта

# Особенности проекта
  * RESTful API с CRUD операциями
  * Работа с SQLAlchemy ORM
  * Миграции базы данных через Flask-Migrate
  * Поддержка сортировки и фильтрации
  * Пример интеграции с внешними API

## Технологии
- Flask
- SQLAlchemy
- Flask-Migrate
- REST API

## Требования
- Python 3.10
- virtualenvwrapper (pip install virtualenvwrapper)
- Git

## Быстрая установка (Linux)

```bash
# 1. Клонирование репозитория
git clone <repository-url> <folder-name>

# 2. Создание виртуального окружения
mkvirtualenv flask_venv --python=/usr/bin/python3.10

# 3. Активация окружения
source flask_venv/bin/activate

# 4. Установка зависимостей
pip install -r requirements.txt

# 5. Инициализация базы данных
flask db upgrade
```

