import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.stub_llm import StubLLM
from app.core.constants import InputType, MaterialStatus, SubjectType
from app.repositories.repos import MaterialRepository, TopicRepository, UserRepository
from app.schemas.schemas import ChunkPayload
from app.services.chunking_service import ChunkingService
from app.services.normalization_service import NormalizationService
from app.services.topic_extraction_service import TopicExtractionService
from app.services.topic_pipeline_service import TopicPipelineService


@pytest.mark.asyncio
async def test_stub_llm_extract_topics():
    llm = StubLLM()
    topics = await llm.extract_topics("Some study text about mathematics.")
    assert len(topics) == 2
    assert topics[0].name
    assert topics[0].text
    assert topics[0].subject in ("math", "physics", "chemistry", "biology", "programming", "language", "other")


@pytest.mark.asyncio
async def test_topic_extraction_service_returns_topics():
    service = TopicExtractionService(llm=StubLLM())
    chunks = [
        ChunkPayload(chunk_index=0, text="Introduction to Algebra", char_start=0, char_end=22),
        ChunkPayload(chunk_index=1, text="Linear equations and solutions", char_start=23, char_end=53),
    ]
    topics = await service.extract_topics(chunks)
    assert len(topics) >= 1


@pytest.mark.asyncio
async def test_topic_extraction_empty_chunks():
    service = TopicExtractionService(llm=StubLLM())
    topics = await service.extract_topics([])
    assert topics == []


def test_chunking_service_basic():
    service = ChunkingService()
    text = "A" * 2500
    chunks = service.chunk(text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 2
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.char_start >= 0
        assert chunk.char_end > chunk.char_start
        assert len(chunk.text) > 0


def test_chunking_service_short_text():
    service = ChunkingService()
    text = "Short text."
    chunks = service.chunk(text)
    assert len(chunks) == 1
    assert chunks[0].text == "Short text."


def test_normalization_service():
    service = NormalizationService()
    raw = "  Hello   World  \n\n\n\n\nExtra newlines  "
    normalized = service.normalize(raw)
    assert "  " not in normalized
    assert normalized.startswith("Hello")


@pytest.mark.asyncio
async def test_topic_pipeline_service(session: AsyncSession, tmp_path):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=8001001)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id, title="Pipeline test")
    await mat_repo.update_texts(
        material.id,
        raw_text="This is a comprehensive study material about mathematics, covering algebra, "
                 "geometry, and calculus. The material also discusses problem-solving strategies "
                 "and mathematical reasoning.",
    )
    await session.flush()

    pipeline = TopicPipelineService(session, llm=StubLLM())
    topics = await pipeline.run(material.id)
    await session.commit()

    assert len(topics) >= 1
    topic_repo = TopicRepository(session)
    saved = await topic_repo.get_by_material_id(material.id)
    assert len(saved) == len(topics)
