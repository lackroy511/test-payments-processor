# Payments Processor

Асинхронный процессор платежей.

## Архитектура

Три микросервиса в `src/`, общий код в `src/core/`:
- **payments_api**: REST API, создание платежей и Outbox Message
- **payments_publisher**: Читает Outbox Message, публикует в очередь 
- **payments_consumer**: Читает очередь, обрабатывает платежи, шлет событие по WebHook

### Data Flow
```
POST /payments -> payments_api -> payments_publisher -> payments_consumer
```

**Ключевые механизмы:**
- **Outbox pattern** — запись в БД и публикация атомарны через outbox-таблицу
- **DLQ** — `payments.dlq`: недоставленные сообщения
- **Retry + Backoff** — декоратор с exponential backoff (3 попытки, 0.1 -> 5с)
- **UoW** — Unit of Work для сервисов
- **Идемпотентность** — через уникальный `idempotency_key` в БД
- **Аутентификация** — `X-API-Key` на всех ручках API

## Стек

Python 3.14+, PostgreSQL 18, RabbitMQ 4.3.2, SQLAlchemy async + asyncpg, Alembic, pydantic-settings,
FastAPI, FastStream, Docker Compose

## Запуск
- `cp .env.example .env`
- Заполнить `.env` по примеру `.env.example`
- `docker compose up -d`

## URL
- OpenAPI: http://127.0.0.1:8000/api/payments/doc/
- RabbitMQ Management: http://127.0.0.1:15672/

## Запуск для разработки в dev-контейнере VS Code
- `cp .env.example .env`
- Заполнить `.env` по примеру `.env.example`
- `F1` -> `Dev Containers: Reopen in Container`


```bash
uv sync --group dev          # установка зависимостей
alembic upgrade head         # накатить миграции
ruff check . && ty src/      # линтер + типы
```

Пакетный менеджер — **uv**. Форматирование: `ruff format .`, сортировка импортов: `isort .`.
