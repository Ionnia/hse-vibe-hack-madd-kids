# Задача 3 — Ingestion pipeline: image/audio/text -> unified text

Теперь реализуй ingestion pipeline на основе обновлённой архитектуры.

## Цель

Система должна уметь принимать пользовательский контент из Telegram и приводить его к единому текстовому представлению.

## Поддерживаемые input types

- image
- audio / voice
- text

## Pipeline

- image -> OCR -> text
- audio -> transcription -> text
- text -> pass-through

Результат должен храниться как extracted text + metadata.

## Что нужно реализовать

### 1. Adapters
Создай интерфейсы и базовые реализации:

- `app/adapters/storage/base.py`
- `app/adapters/storage/local.py`

- `app/adapters/ocr/base.py`
- `app/adapters/ocr/stub_ocr.py`

- `app/adapters/transcription/base.py`
- `app/adapters/transcription/stub_transcription.py`

- `app/adapters/input_classifier.py`

Нужны typed interfaces.

### 2. DTO / schemas
Добавь DTO для:

- uploaded asset descriptor
- extracted text fragment
- extracted document payload
- source metadata
- confidence/timestamps/pages where relevant

### 3. Services
Создай:

- `app/services/file_ingestion_service.py`
- `app/services/text_extraction_service.py`
- `app/services/material_ingestion_pipeline.py`

#### `FileIngestionService`
Должен:
- принимать uploaded file / message metadata
- сохранять asset
- определять media type

#### `TextExtractionService`
Должен:
- вызывать OCR для image
- вызывать transcription для audio
- пропускать text как есть

#### `MaterialIngestionPipeline`
Должен:
- создать material
- создать asset
- извлечь text
- сохранить extracted result
- обновить status material

### 4. Celery task
Создай:

- `app/tasks/material_ingestion_tasks.py`

Нужно:
- асинхронно запускать ingestion
- делать idempotency check
- переводить status:
  - uploaded
  - parsing
  - parsed
  - failed

### 5. Bot upload handler
Создай:

- `app/bot/handlers/upload.py`

Он должен:
- принимать photo
- принимать voice/audio
- принимать text
- создавать material
- отправлять задачу в Celery
- отвечать пользователю, что материал принят в обработку

### 6. API routes
Добавь route'ы:

- список материалов пользователя
- получить material by id
- получить status material

## Важно

- Здесь не нужно делать OCR и Whisper по-настоящему, если это замедляет MVP
- Можно сделать stub adapters с понятным интерфейсом
- Архитектура должна позволять потом легко заменить stub на production adapter

## Формат ответа

Пиши код файлов.  
Сначала adapters, потом services, потом tasks, потом bot/api updates.
