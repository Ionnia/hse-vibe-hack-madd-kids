# Задача 6 — Docker, migrations, tests и README

Теперь доведи проект до состояния запускаемого MVP skeleton.

## Цель

Нужно, чтобы проект можно было:

- склонировать
- настроить через `.env`
- поднять через docker compose
- применить миграции
- запустить:
  - API
  - bot
  - worker
  - beat

## Что нужно реализовать

### 1. Infra files
Создай:

- `Dockerfile.api`
- `Dockerfile.bot`
- `Dockerfile.worker`
- `docker-compose.yml`
- `.env.example`
- `requirements.txt` или `pyproject.toml`

### 2. Alembic
Создай:

- `alembic.ini`
- `alembic/env.py`
- initial migration

### 3. Tests
Создай минимальные тесты:

- config smoke test
- health route test
- model creation test
- repository smoke test
- ingestion pipeline smoke test
- topic extraction pipeline smoke test
- tutor loop smoke test
- repetition logic smoke test

Stub adapters использовать можно.

### 4. README
Создай `README.md` со следующими разделами:

1. Project overview
2. MVP architecture
3. Stack
4. Project structure
5. Local setup
6. Env variables
7. Migrations
8. Running API / bot / worker / beat
9. Telegram commands
10. Current MVP scope
11. Future roadmap

### 5. Consistency pass
Проверь:
- imports
- module paths
- enum names
- model names
- celery task names
- bot router includes
- API router includes

## Важно

- Не переписывай проект заново
- Дострой уже предложенную структуру
- Делай output максимально practical

## Формат ответа

Пиши код файлов.  
В конце дай короткий checklist запуска.
