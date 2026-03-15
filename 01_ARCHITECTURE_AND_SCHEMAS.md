# Задача 1 — Архитектура, сущности и схемы

Ты senior Python architect.  
Нужно описать **обновлённую MVP-архитектуру** на основе следующего дизайна:

## Логика системы

### Input layer
Пользователь в Telegram может отправить:

- image
- audio / voice
- text

### Ingestion layer
Backend приводит всё к тексту:

- image -> OCR -> text
- audio -> transcription -> text
- text -> pass-through

### Processing layer
Далее текст проходит через:

- normalization
- chunking
- LLM topic extraction

LLM должен возвращать **structured output** через Pydantic.

### Core knowledge object
Главный объект MVP:

```python
class Topic(BaseModel):
    name: str
    text: str
    subject: Literal["math", "physics", "other"]
```

Можно расширить subject, но логика должна остаться простой.

### Tutor layer
Отдельный tutor pipeline генерирует следующее задание пользователю.

Главный tutor object:

```python
class Task(BaseModel):
    type: Literal["flash", "exercise"]
    question: str
    answer: str
    difficulty: int
```

### Learning loop
Backend:

- выбирает topic
- запрашивает у LLM следующий task
- отправляет task пользователю
- получает ответ
- обновляет progress / repetition state
- планирует следующее повторение

## Что нужно выдать

### 1. Architecture summary
Кратко опиши блоки:

- Telegram / aiogram
- FastAPI backend
- ingestion pipeline
- topic extraction pipeline
- tutor pipeline
- scheduler / repetition loop
- database

### 2. Project tree
Предложи простую структуру проекта, например:

- `app/api/`
- `app/bot/`
- `app/core/`
- `app/db/`
- `app/models/`
- `app/repositories/`
- `app/schemas/`
- `app/services/`
- `app/adapters/`
- `app/tasks/`
- `tests/`

### 3. Domain model
Нужны сущности минимум:

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

### 4. Pydantic schemas
Опиши схемы, которые нужны для structured output и API:

- Topic
- Task
- extracted text fragment
- normalized text
- upload response
- progress response
- review result
- tutor task payload

### 5. Workflow description
Кратко распиши 4 workflow:

1. upload -> extraction -> normalization -> topics -> db
2. topic -> tutor task generation -> user
3. user answer -> review -> progress update
4. scheduler -> next repetition -> delivery

## Формат ответа

Сначала:
1. Architecture summary
2. Project tree
3. Domain model
4. Pydantic schemas
5. Workflow description

После этого остановись.  
Код пока не пиши.
