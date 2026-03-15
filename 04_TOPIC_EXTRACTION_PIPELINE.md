# Задача 4 — Normalization, chunking и topic extraction через structured output

Теперь реализуй второй основной pipeline: из extracted text получить topics.

## Цель

После ingestion система должна уметь:

- очищать текст
- нормализовать текст
- разбивать на chunks
- извлекать topics через LLM
- сохранять topics в DB

## Важное требование

LLM должен возвращать **structured output**, совместимый с Pydantic.

Основная схема:

```python
class Topic(BaseModel):
    name: str
    text: str
    subject: Literal["math", "physics", "other"]
```

Если хочешь — можешь расширить до:
- chemistry
- biology
- programming
- language
- other

Но всё должно остаться простым и стабильным.

## Что нужно реализовать

### 1. Adapters
Создай:

- `app/adapters/llm/base.py`
- `app/adapters/llm/stub_llm.py`

LLM interface должен уметь:
- normalize text
- extract topics from text/chunks
- optionally classify subject
- later support tutor task generation

### 2. DTO / schemas
Добавь DTO для:

- normalized text payload
- chunk payload
- topic extraction request
- topic extraction response

### 3. Services
Создай:

- `app/services/normalization_service.py`
- `app/services/chunking_service.py`
- `app/services/topic_extraction_service.py`
- `app/services/topic_pipeline_service.py`

#### `NormalizationService`
Должен:
- убирать мусор
- объединять фрагменты текста
- нормализовать пробелы
- чистить артефакты OCR/transcription
- готовить unified text

#### `ChunkingService`
Должен:
- резать текст на manageable chunks
- хранить metadata:
  - chunk index
  - char start/end
  - source asset id
  - source page/timestamp if available

#### `TopicExtractionService`
Должен:
- взять normalized text или chunks
- вызвать LLM structured extraction
- вернуть list[Topic]

#### `TopicPipelineService`
Должен:
- взять extracted text
- нормализовать
- разбить на chunks
- извлечь topics
- сохранить topics и chunks
- обновить material status:
  - normalized
  - topics_extracted
  - ready
  - failed

### 4. Celery task
Создай task для topic extraction pipeline.

### 5. API routes
Добавь route'ы:
- получить topics по material
- получить topic by id

### 6. Bot handlers
Добавь:
- `app/bot/handlers/topics.py`

Команда:
- `/topics`

Можно сделать поведение:
- показать последние materials
- дать выбрать material
- показать список topics

## Важно

- Не делай пока сложный RAG
- Не нужен vector DB на этом этапе
- Основной knowledge object сейчас — Topic
- Chunking нужен для устойчивости extraction pipeline

## Формат ответа

Пиши код файлов.  
Сначала adapters, затем services, затем tasks, затем routes/handlers.
