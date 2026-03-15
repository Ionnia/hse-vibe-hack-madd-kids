# Задача 2 — Foundation: config, DB, models, schemas, API и bot skeleton

Теперь реализуй **базовый каркас проекта кодом**.

## Цель

Нужно подготовить всё, чтобы на следующих этапах было куда встроить:

- ingestion
- topic extraction
- tutor generation
- repetition loop

## Формат вывода

Пиши реальные файлы в формате:

```python
# path: app/core/config.py
...
```

## Что нужно реализовать

### 1. Core
Создай:

- `app/core/config.py`
- `app/core/logging.py`
- `app/core/constants.py`

Нужны:
- Pydantic settings
- env variables
- DB settings
- Telegram settings
- Celery settings
- LLM settings
- OCR/transcription settings
- material statuses
- task/review/progress enums

### 2. FastAPI
Создай:

- `app/api/main.py`
- `app/api/routes/health.py`

Нужны:
- app factory или простой app init
- `/health`
- `/ready`
- базовая router setup

### 3. Celery
Создай:

- `app/tasks/celery_app.py`

Нужны:
- celery init
- beat placeholder
- autodiscover tasks

### 4. DB base and session
Создай:

- `app/db/base.py`
- `app/db/session.py`

### 5. SQLAlchemy models
Создай модели:

- User
- StudyMaterial
- MaterialAsset
- Topic
- TopicChunk
- TutorTask
- ReviewLog
- UserTopicProgress
- RepetitionState
- GamificationProfile

Требования:
- SQLAlchemy 2.0 style
- typing
- relationships
- created_at / updated_at
- enum statuses
- clean naming

### 6. Pydantic schemas
Создай схемы для:

- user
- material
- topic
- tutor task
- review
- progress
- extracted fragment DTO
- normalized text DTO

### 7. Repositories
Создай базовые repositories / CRUD layer для:
- users
- materials
- topics
- tutor tasks
- progress
- repetitions

### 8. Bot skeleton
Создай:

- `app/bot/main.py`
- `app/bot/router.py`
- `app/bot/handlers/start.py`
- `app/bot/handlers/help.py`

Команды:
- `/start`
- `/help`

Также можно сразу добавить заглушки:
- `/upload`
- `/topics`
- `/study`
- `/progress`

## Важно

- Пока не делай ingestion/business logic
- Сделай запускаемый skeleton
- Добавь docstrings
- Соблюдай consistency imports

## Формат ответа

Пиши только код файлов.  
Без длинной теории.
