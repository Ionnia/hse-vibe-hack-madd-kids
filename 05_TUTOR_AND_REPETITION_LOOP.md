# Задача 5 — Tutor pipeline, task generation и repetition loop

Теперь реализуй core tutor loop.

## Главная идея этапа

Не чат.  
Не open-ended assistant.  
А **task-based tutor**.

Система должна:

1. выбрать тему
2. сгенерировать следующее задание по теме
3. отправить задание пользователю
4. принять ответ
5. проверить ответ
6. обновить progress и repetition state
7. запланировать следующее повторение

## Основная tutor schema

```python
class Task(BaseModel):
    type: Literal["flash", "exercise"]
    question: str
    answer: str
    difficulty: int
```

Можно расширить полями:
- explanation: str | None
- topic_id: UUID
- hints: list[str] = []

## Что нужно реализовать

### 1. LLM extension
Расширь LLM adapter, чтобы он умел:

- generate_tutor_task(topic, progress)
- evaluate_user_answer(task, user_answer)
- optionally simplify_or_harden_next_task(...)

### 2. DTO / schemas
Добавь схемы:

- tutor task payload
- review request
- review result
- study session summary
- next repetition suggestion

### 3. Services
Создай:

- `app/services/tutor_task_service.py`
- `app/services/review_service.py`
- `app/services/progress_service.py`
- `app/services/repetition_service.py`
- `app/services/study_orchestrator_service.py`

#### `TutorTaskService`
Должен:
- выбрать topic
- учесть progress
- запросить у LLM task
- сохранить TutorTask

#### `ReviewService`
Должен:
- принять ответ пользователя
- сравнить с эталоном через LLM или rule-based logic
- вернуть verdict
- записать ReviewLog

#### `ProgressService`
Должен:
- обновлять состояние по topic:
  - unknown
  - weak
  - learning
  - good
  - mastered

#### `RepetitionService`
Должен:
- хранить repetition state
- пересчитывать next review time
- можно сделать simplified FSRS-like logic:
  - correct -> interval grows
  - wrong -> interval shrinks

#### `StudyOrchestratorService`
Должен координировать high-level flow:
- request next task
- submit answer
- get feedback
- schedule next repetition

### 4. Celery / beat
Добавь:
- периодический поиск due repetitions
- отправку повторений в Telegram

### 5. Bot handlers
Создай:

- `app/bot/handlers/study.py`
- `app/bot/handlers/review.py`
- `app/bot/handlers/progress.py`

Команды и сценарии:
- `/study` — получить следующее задание
- пользователь отвечает
- бот даёт feedback
- `/progress` — показать прогресс

### 6. Gamification
Добавь лёгкую механику:
- XP за правильный ответ
- streak
- level

Но не усложняй.

## Важно

- Нужен реалистичный MVP loop
- Всё должно крутиться вокруг Topic + Task + Review
- Это главный demo-flow проекта

## Формат ответа

Пиши код файлов.  
Сначала adapters extension, потом services, потом tasks, потом handlers/router updates.
