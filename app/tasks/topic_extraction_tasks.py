import asyncio
import logging
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.topic_extraction_tasks.run_topic_pipeline", bind=True, max_retries=3)
def run_topic_pipeline(self, material_id: str) -> dict:
    """Celery task to run topic extraction pipeline for a material."""
    try:
        result = asyncio.run(_run_pipeline_async(material_id))
        return result
    except Exception as exc:
        logger.exception("Topic pipeline failed for %s: %s", material_id, exc)
        raise self.retry(exc=exc, countdown=120)


async def _run_pipeline_async(material_id: str) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    from app.services.topic_pipeline_service import TopicPipelineService

    mat_uuid = UUID(material_id)

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        try:
            pipeline = TopicPipelineService(session)
            topics = await pipeline.run(mat_uuid)
            await session.commit()
            logger.info("Topic pipeline for %s produced %d topics", material_id, len(topics))
            return {"material_id": material_id, "topics": len(topics)}
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await engine.dispose()


@celery_app.task(name="app.tasks.topic_extraction_tasks.send_due_repetitions")
def send_due_repetitions() -> dict:
    """Periodic task to notify users about due repetitions."""
    try:
        result = asyncio.run(_send_due_repetitions_async())
        return result
    except Exception as exc:
        logger.exception("send_due_repetitions failed: %s", exc)
        return {"error": str(exc)}


async def _send_due_repetitions_async() -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    from app.models.models import RepetitionState
    from datetime import datetime, timezone
    from sqlalchemy import select

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(RepetitionState).where(RepetitionState.next_review_at <= now)
        )
        due_states = result.scalars().all()
        logger.info("Found %d due repetitions", len(due_states))
        # In a real system, we'd send Telegram notifications here
        return {"due_count": len(due_states)}
    await engine.dispose()
