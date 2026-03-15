# Tutor Bot

A personalized AI-powered study assistant delivered via Telegram. Upload study materials (photos, voice notes, or text), and the bot extracts topics, generates flashcards and exercises, and uses spaced repetition to help you learn efficiently.

## Architecture

```
tutor/
├── app/
│   ├── api/          # FastAPI REST API
│   ├── bot/          # Aiogram 3.x Telegram bot
│   ├── core/         # Config, constants, logging
│   ├── db/           # SQLAlchemy 2.0 async engine
│   ├── models/       # ORM models
│   ├── repositories/ # Async CRUD repositories
│   ├── schemas/      # Pydantic v2 schemas
│   ├── services/     # Business logic
│   ├── adapters/     # Storage, OCR, transcription, LLM
│   └── tasks/        # Celery tasks
├── alembic/          # Database migrations
└── tests/            # pytest test suite
```

## Services

- **API** — FastAPI app on port 8000
- **Bot** — Aiogram 3.x Telegram bot
- **Worker** — Celery worker for background tasks
- **Beat** — Celery beat scheduler for periodic tasks
- **PostgreSQL** — Primary database
- **Redis** — Celery broker and result backend

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- A Telegram bot token (get it from [@BotFather](https://t.me/BotFather))

### 2. Configuration

```bash
cp .env.example .env
# Edit .env and set TELEGRAM_TOKEN at minimum
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

### 4. Run database migrations

```bash
docker-compose exec api alembic upgrade head
```

## Local Development

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start PostgreSQL and Redis

```bash
docker-compose up -d postgres redis
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn app.api.main:app --reload
```

### 5. Start the bot

```bash
python -m app.bot.main
```

### 6. Start Celery worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## Running Tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory database and do not require a running PostgreSQL instance.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check (tests DB connection) |
| GET | `/materials?user_id=...` | List user's materials |
| GET | `/materials/{id}` | Get material by ID |
| GET | `/materials/{id}/status` | Get material processing status |
| GET | `/materials/{id}/topics` | List topics for a material |
| GET | `/topics/{id}` | Get topic by ID |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and get welcome message |
| `/help` | Show available commands |
| `/topics` | List your study topics |
| `/study` | Start a study session |
| `/progress` | View your learning progress |

## Material Upload

Send any of the following to the bot:
- **Photo** — Text extracted via OCR
- **Voice / Audio** — Transcribed to text
- **Text message** — Stored directly

## Processing Pipeline

1. **Ingest** — Save file, create `StudyMaterial` record
2. **Extract** — OCR / transcribe / passthrough
3. **Normalize** — Clean and normalize text
4. **Chunk** — Split into overlapping chunks
5. **Extract Topics** — LLM extracts structured topics
6. **Generate Tasks** — LLM creates flashcards/exercises per topic
7. **Review** — LLM evaluates user answers
8. **Repetition** — SM2 algorithm schedules next review

## LLM Providers

Configure via `LLM_PROVIDER` env var:
- `stub` — deterministic stub for development/testing
- `openai` — OpenAI API (requires `LLM_API_KEY`)
- `ollama` — Local Ollama (requires `LLM_BASE_URL`)

## Configuration

All settings are in `app/core/config.py` and read from environment variables or `.env` file. See `.env.example` for all available options.

## Database Schema

- `users` — Telegram users
- `study_materials` — Uploaded learning materials
- `material_assets` — Individual files (images, audio, text)
- `topics` — Extracted study topics
- `topic_chunks` — Text chunks for processing
- `tutor_tasks` — Generated flashcards and exercises
- `review_logs` — Answer review history
- `user_topic_progress` — Per-topic learning progress
- `repetition_states` — SM2 spaced repetition state
- `gamification_profiles` — XP, level, streaks
