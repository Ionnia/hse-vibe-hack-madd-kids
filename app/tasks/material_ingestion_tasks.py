import asyncio
import logging
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.material_ingestion_tasks.ingest_material", bind=True, max_retries=3)
def ingest_material(
    self,
    material_id: str,
    user_id: str,
    input_type: str,
    filename: str | None = None,
    telegram_file_id: str | None = None,
    raw_text: str | None = None,
) -> dict:
    """Celery task to run the material ingestion pipeline."""
    try:
        result = asyncio.run(_ingest_material_async(
            material_id=material_id,
            user_id=user_id,
            input_type=input_type,
            filename=filename,
            telegram_file_id=telegram_file_id,
            raw_text=raw_text,
        ))
        return result
    except Exception as exc:
        logger.exception("Material ingestion failed for %s: %s", material_id, exc)
        raise self.retry(exc=exc, countdown=60)


async def _ingest_material_async(
    material_id: str,
    user_id: str,
    input_type: str,
    filename: str | None,
    telegram_file_id: str | None,
    raw_text: str | None,
) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    from app.core.constants import MaterialStatus
    from app.repositories.repos import MaterialRepository
    from app.services.topic_pipeline_service import TopicPipelineService

    mat_uuid = UUID(material_id)

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        material_repo = MaterialRepository(session)

        try:
            # Run topic pipeline (assumes material already ingested)
            pipeline = TopicPipelineService(session)
            topics = await pipeline.run(mat_uuid)
            await session.commit()

            logger.info("Material %s ingested with %d topics", material_id, len(topics))
            return {"material_id": material_id, "topics_count": len(topics), "status": "ready"}

        except Exception as exc:
            await session.rollback()
            await material_repo.update_status(mat_uuid, MaterialStatus.failed)
            await session.commit()
            raise exc
        finally:
            await engine.dispose()
