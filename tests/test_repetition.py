from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SubjectType
from app.repositories.repos import MaterialRepository, RepetitionRepository, TopicRepository, UserRepository
from app.services.repetition_service import RepetitionService


async def _create_user_and_topic(session: AsyncSession, telegram_id: int):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=telegram_id)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id)
    await session.flush()

    topic_repo = TopicRepository(session)
    topic = await topic_repo.create(
        material_id=material.id,
        name="Test Topic",
        text="Topic text",
        subject=SubjectType.other,
    )
    await session.flush()
    return user, topic


@pytest.mark.asyncio
async def test_repetition_update_correct(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 10001001)

    service = RepetitionService(session)
    state = await service.update_interval(user.id, topic.id, was_correct=True)
    await session.flush()

    # Correct: interval should increase (1.0 * 2.5 = 2.5)
    assert state.interval_days == pytest.approx(2.5)
    assert state.review_count == 1
    assert state.next_review_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_repetition_update_incorrect(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 10001002)

    service = RepetitionService(session)

    # First do a correct review to increase interval
    await service.update_interval(user.id, topic.id, was_correct=True)
    await session.flush()

    # Then incorrect - should reset to 1.0
    state = await service.update_interval(user.id, topic.id, was_correct=False)
    await session.flush()

    assert state.interval_days == pytest.approx(1.0)
    assert state.review_count == 2


@pytest.mark.asyncio
async def test_repetition_get_due_topics(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 10001003)

    service = RepetitionService(session)
    # Initially next_review_at is set to now, so should be due
    due = await service.get_due_topics(user.id)
    assert len(due) >= 1
    assert any(str(d.topic_id) == str(topic.id) for d in due)


@pytest.mark.asyncio
async def test_repetition_not_due_after_correct(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 10001004)

    service = RepetitionService(session)
    state = await service.update_interval(user.id, topic.id, was_correct=True)
    await session.flush()

    # Next review should be in the future
    assert state.next_review_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_repetition_state_initial_values(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 10001005)

    repo = RepetitionRepository(session)
    state = await repo.get_or_create(user.id, topic.id)

    assert state.interval_days == pytest.approx(1.0)
    assert state.ease_factor == pytest.approx(2.5)
    assert state.review_count == 0
    assert state.last_reviewed_at is None


@pytest.mark.asyncio
async def test_repetition_interval_grows_with_multiple_correct(session: AsyncSession):
    user, topic = await _create_user_and_topic(session, 10001006)

    service = RepetitionService(session)

    state1 = await service.update_interval(user.id, topic.id, was_correct=True)
    await session.flush()
    interval1 = state1.interval_days

    state2 = await service.update_interval(user.id, topic.id, was_correct=True)
    await session.flush()
    interval2 = state2.interval_days

    assert interval2 > interval1
