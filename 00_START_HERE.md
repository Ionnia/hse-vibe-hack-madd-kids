# AI Tutor MVP — обновлённый пакет задач для Claude

Этот пакет отражает **обновлённую архитектуру с доски**: не сложный multi-agent, а простой и контролируемый pipeline:

1. Telegram user sends:
   - image
   - audio
   - text

2. Backend converts everything to text:
   - image -> OCR -> text
   - audio -> transcription -> text
   - text -> pass-through

3. Text goes through:
   - normalization
   - chunking
   - topic extraction via LLM structured output

4. Topics are stored in DB

5. Tutor generates the next learning task:
   - flashcard
   - exercise

6. Backend sends task to user and tracks repetitions / progress

## Ключевой принцип

Не делать полноценную autonomous multi-agent систему.

Делать:

- один backend orchestrator
- один ingestion pipeline
- один extraction pipeline
- один tutor pipeline
- чёткие Pydantic схемы
- LLM structured output
- простую DB-модель
- простую repetition loop

## Главная идея MVP

Не “умный чат обо всём”, а **task-based AI tutor**:

- сначала извлекаем темы из материала
- потом по темам генерируем учебные задания
- затем ведём цикл повторений

## Стек

- Python
- FastAPI
- aiogram
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Celery + Celery Beat
- Pydantic v2
- OCR adapter
- Transcription adapter
- LLM adapter

## Рекомендуемый порядок загрузки в Claude

1. `01_ARCHITECTURE_AND_SCHEMAS.md`
2. `02_FOUNDATION_AND_DOMAIN.md`
3. `03_INGESTION_PIPELINE.md`
4. `04_TOPIC_EXTRACTION_PIPELINE.md`
5. `05_TUTOR_AND_REPETITION_LOOP.md`
6. `06_INFRA_TESTS_AND_README.md`

## Режим работы с Claude

Перед первым файлом можно дать короткую инструкцию:

> Do not give long explanations.  
> Write implementation-oriented output.  
> Return real files in the format `# path: ...`.  
> Prefer a runnable MVP skeleton over abstract architecture.  
> If some external providers are uncertain, create interfaces and stub adapters.

## Что важно не потерять

- structured output через Pydantic
- `Topic` как основная сущность MVP
- `Task` как основная tutor-сущность
- минимальный repetition loop
- Telegram-first UX
