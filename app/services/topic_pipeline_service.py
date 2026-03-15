from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.base import BaseLLM
from app.adapters.llm.factory import get_llm
from app.core.constants import MaterialStatus, SubjectType
from app.models.models import Topic
from app.repositories.repos import MaterialRepository, TopicRepository
from app.services.chunking_service import ChunkingService
from app.services.normalization_service import NormalizationService
from app.services.topic_extraction_service import TopicExtractionService


class TopicPipelineService:
    def __init__(self, session: AsyncSession, llm: BaseLLM | None = None) -> None:
        self.session = session
        self.material_repo = MaterialRepository(session)
        self.topic_repo = TopicRepository(session)
        self.normalization = NormalizationService()
        self.chunking = ChunkingService()
        self.extraction = TopicExtractionService(llm or get_llm())

    async def run(self, material_id: UUID) -> list[Topic]:
        material = await self.material_repo.get_by_id(material_id)
        if material is None:
            raise ValueError(f"Material {material_id} not found")

        # Normalize
        await self.material_repo.update_status(material_id, MaterialStatus.normalizing)
        raw = material.raw_text or ""
        normalized = self.normalization.normalize(raw)
        await self.material_repo.update_texts(material_id, normalized_text=normalized)
        await self.material_repo.update_status(material_id, MaterialStatus.normalized)

        # Chunk
        chunks = self.chunking.chunk(normalized)

        # Extract topics
        await self.material_repo.update_status(material_id, MaterialStatus.extracting)
        topic_schemas = await self.extraction.extract_topics(chunks)

        # Save topics
        topics: list[Topic] = []
        for schema in topic_schemas:
            subject = SubjectType(schema.subject) if schema.subject in SubjectType._value2member_map_ else SubjectType.other
            topic = await self.topic_repo.create(
                material_id=material_id,
                name=schema.name,
                text=schema.text,
                subject=subject,
            )
            topics.append(topic)

        await self.material_repo.update_status(material_id, MaterialStatus.topics_extracted)
        await self.material_repo.update_status(material_id, MaterialStatus.ready)

        return topics
