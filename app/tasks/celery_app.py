from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "tutor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.material_ingestion_tasks",
        "app.tasks.topic_extraction_tasks",
    ],
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    "send-due-repetitions": {
        "task": "app.tasks.topic_extraction_tasks.send_due_repetitions",
        "schedule": 300.0,  # every 5 minutes
    },
    "enrich-pending-topics": {
        "task": "app.tasks.topic_extraction_tasks.enrich_pending_topics",
        "schedule": 3600.0,  # every hour
    },
}
