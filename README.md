# Тестовый проект Payments Processor

Сервис приёма и обработки платежей. Состоит из трёх компонентов:

- **API** (FastAPI) — REST-интерфейс для создания платежей
- **Publisher** (FastStream) — outbox-воркер, публикует события в RabbitMQ
- **Consumer** (FastStream) — заготовка для обработки входящих событий

## Ключевые особенности
- **Outbox pattern**
- **Идемпотентность**
- **DLQ**
- **Retry + Backoff**

## Стек
Python 3.14+, PostgreSQL 18, RabbitMQ 4.3.2, SQLAlchemy async, Alembic, pydantic-settings, Docker Compose

## Запуск
- `cp .env.example .env`
- заполнить `.env` по примеру `.env.example`
- `docker compose up -d`

## Адреса
| Сервис              | URL                                       |
|---------------------|-------------------------------------------|
| OpenAPI             | http://127.0.0.1:8000/api/payments/doc/   |
| RabbitMQ Management | http://127.0.0.1:15672/                   |