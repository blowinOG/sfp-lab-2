# Vault

Сервис управления пользователями и OAuth-клиентами.

В текущей версии реализован базовый контур: модели данных, аутентификация, GraphQL API и простая админка.

## Стек технологий

  * **FastAPI** — асинхронный веб-фреймворк.
  * **Ariadne** — schema-first GraphQL для Python.
  * **graphql-core** — реализация GraphQL-спецификации.
  * **SQLAlchemy 2.x** — ORM с аннотированным стилем.
  * **Alembic** — миграции схемы БД.
  * **Argon2id** — хэширование паролей.
  * **zxcvbn** — оценка стойкости паролей.
  * **python-jose** — JWT (HS256).
  * **pydantic-settings** — конфигурация через переменные окружения.
  * **SQLite** — БД для разработки.

## Установка

    git clone https://github.com/blowinOG/sfp-lab-2
    cd Vault_lab1
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

## Настройка

Скопируй .env.example в .env:

    copy .env.example .env

Сгенерируй секреты и вставь их в .env (выполни команду дважды — для JWT_SECRET и PASSWORD_PEPPER):

    python -c "import secrets; print(secrets.token_urlsafe(48))"

## Запуск

Применить миграции:

    alembic upgrade head

Запустить сервер:

    python run.py

  * **REST API** — http://127.0.0.1:8000/auth/
  * **Swagger UI** — http://127.0.0.1:8000/docs
  * **GraphQL Playground** — http://127.0.0.1:8000/graphql/
  * **Админка** — http://127.0.0.1:8000/admin/

## Тесты

    pytest

Используется отдельная тестовая БД, которая создается и удаляется автоматически.