from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.repos import TopicRepository
from app.schemas.schemas import TopicRead

router = APIRouter(tags=["topics"])


@router.get("/materials/{material_id}/topics", response_model=list[TopicRead])
async def list_topics_for_material(
    material_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[TopicRead]:
    repo = TopicRepository(session)
    topics = await repo.get_by_material_id(material_id)
    return [TopicRead.model_validate(t) for t in topics]


@router.get("/topics/{topic_id}", response_model=TopicRead)
async def get_topic(
    topic_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> TopicRead:
    repo = TopicRepository(session)
    topic = await repo.get_by_id(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicRead.model_validate(topic)
