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
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await engine.dispose()

    # Trigger enrichment for each extracted topic
    for topic in topics:
        enrich_topic_task.delay(str(topic.id))

    return {"material_id": material_id, "topics": len(topics)}


@celery_app.task(name="app.tasks.topic_extraction_tasks.enrich_topic_task", bind=True, max_retries=3)
def enrich_topic_task(self, topic_id: str) -> dict:
    """Celery task to enrich a topic with web search results."""
    try:
        result = asyncio.run(_enrich_topic_async(topic_id))
        return result
    except Exception as exc:
        logger.exception("enrich_topic_task failed for %s: %s", topic_id, exc)
        raise self.retry(exc=exc, countdown=60)


async def _enrich_topic_async(topic_id: str) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    from app.services.topic_enrichment_service import TopicEnrichmentService

    t_uuid = UUID(topic_id)

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        try:
            service = TopicEnrichmentService(session)
            enriched = await service.enrich(t_uuid)
            await session.commit()
            return {"topic_id": topic_id, "enriched": enriched}
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await engine.dispose()


@celery_app.task(name="app.tasks.topic_extraction_tasks.enrich_pending_topics")
def enrich_pending_topics() -> dict:
    """Periodic task to enrich topics that haven't been enriched yet."""
    try:
        result = asyncio.run(_enrich_pending_async())
        return result
    except Exception as exc:
        logger.exception("enrich_pending_topics failed: %s", exc)
        return {"error": str(exc)}


async def _enrich_pending_async() -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from sqlalchemy import select
    from app.core.config import settings
    from app.models.models import Topic

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            select(Topic.id).where(Topic.enriched_at.is_(None)).limit(20)
        )
        topic_ids = [str(row[0]) for row in result.all()]
        await engine.dispose()

    for tid in topic_ids:
        enrich_topic_task.delay(tid)

    logger.info("enrich_pending_topics: queued %d topics for enrichment", len(topic_ids))
    return {"queued": len(topic_ids)}


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
