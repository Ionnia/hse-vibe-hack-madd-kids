import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.stub_llm import StubLLM
from app.core.constants import ReviewVerdict, SubjectType
from app.repositories.repos import MaterialRepository, TopicRepository, UserRepository
from app.services.review_service import ReviewService
from app.services.tutor_task_service import TutorTaskService


async def _create_user_and_topic(session: AsyncSession, telegram_id: int):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=telegram_id)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id, title="Test")
    await session.flush()

    topic_repo = TopicRepository(session)
    topic = await topic_repo.create(
        material_id=material.id,
        name="Algebra Basics",
        text="Introduction to algebraic expressions and equations.",
        subject=SubjectType.math,
    )
    await session.flush()
    return user, topic


@pytest.mark.asyncio
async def test_tutor_task_service_generates_task(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 9001001)

    service = TutorTaskService(session, llm=StubLLM())
    task = await service.get_next_task(user_id=user.id, topic_id=topic.id)
    await session.flush()

    assert task is not None
    assert task.question
    assert task.answer
    assert task.difficulty >= 1


@pytest.mark.asyncio
async def test_review_service_correct_answer(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 9001002)

    tutor_service = TutorTaskService(session, llm=StubLLM())
    task = await tutor_service.get_next_task(user_id=user.id, topic_id=topic.id)
    await session.flush()

    review_service = ReviewService(session, llm=StubLLM())
    result = await review_service.review(
        user_id=user.id,
        task_id=task.id,
        user_answer=task.answer,  # exact correct answer
    )
    await session.flush()

    assert result.verdict == ReviewVerdict.correct
    assert result.score == 1.0


@pytest.mark.asyncio
async def test_review_service_incorrect_answer(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 9001003)

    tutor_service = TutorTaskService(session, llm=StubLLM())
    task = await tutor_service.get_next_task(user_id=user.id, topic_id=topic.id)
    await session.flush()

    review_service = ReviewService(session, llm=StubLLM())
    result = await review_service.review(
        user_id=user.id,
        task_id=task.id,
        user_answer="zzz completely wrong answer xyz",
    )
    await session.flush()

    assert result.verdict in (ReviewVerdict.incorrect, ReviewVerdict.partial)


@pytest.mark.asyncio
async def test_stub_llm_generate_task():
    llm = StubLLM()
    from app.schemas.schemas import TopicSchema
    schema = TopicSchema(name="Test Topic", text="Topic content about math.", subject="math")
    task = await llm.generate_tutor_task(schema, level="unknown")
    assert task.question
    assert task.answer
    assert 1 <= task.difficulty <= 5
    assert isinstance(task.hints, list)


@pytest.mark.asyncio
async def test_stub_llm_evaluate_answer():
    llm = StubLLM()
    result = await llm.evaluate_answer(
        question="What is 2+2?",
        correct_answer="4",
        user_answer="4",
    )
    assert result.verdict == ReviewVerdict.correct
    assert result.score == 1.0
