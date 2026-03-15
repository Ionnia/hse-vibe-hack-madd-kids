from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos import (
    MaterialRepository,
    ProgressRepository,
    RepetitionRepository,
    TopicRepository,
    TutorTaskRepository,
    UserRepository,
)
from app.core.constants import MaterialStatus, SubjectType, TaskType


@pytest.mark.asyncio
async def test_user_get_by_telegram_id_returns_none_for_missing(session: AsyncSession):
    repo = UserRepository(session)
    result = await repo.get_by_telegram_id(999999999)
    assert result is None


@pytest.mark.asyncio
async def test_user_create_and_get(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(telegram_id=111111, username="testuser", full_name="Test User")
    await session.commit()

    found = await repo.get_by_telegram_id(111111)
    assert found is not None
    assert found.username == "testuser"


@pytest.mark.asyncio
async def test_user_get_or_create(session: AsyncSession):
    repo = UserRepository(session)
    user1 = await repo.get_or_create(telegram_id=222222, username="user2")
    await session.commit()
    user2 = await repo.get_or_create(telegram_id=222222, username="user2")
    assert user1.id == user2.id


@pytest.mark.asyncio
async def test_material_create_and_get(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=333333)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id, title="Test Material")
    await session.flush()

    found = await mat_repo.get_by_id(material.id)
    assert found is not None
    assert found.title == "Test Material"
    assert found.status == MaterialStatus.uploaded


@pytest.mark.asyncio
async def test_material_update_status(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=444444)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id)
    await session.flush()

    await mat_repo.update_status(material.id, MaterialStatus.ready)
    await session.flush()

    found = await mat_repo.get_by_id(material.id)
    assert found.status == MaterialStatus.ready


@pytest.mark.asyncio
async def test_topic_create_and_get(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=555555)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id)
    await session.flush()

    topic_repo = TopicRepository(session)
    topic = await topic_repo.create(
        material_id=material.id,
        name="Test Topic",
        text="Topic content",
        subject=SubjectType.other,
    )
    await session.flush()

    topics = await topic_repo.get_by_material_id(material.id)
    assert len(topics) == 1
    assert topics[0].name == "Test Topic"


@pytest.mark.asyncio
async def test_progress_get_or_create(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=666666)
    await session.flush()

    mat_repo = MaterialRepository(session)
    material = await mat_repo.create(user_id=user.id)
    await session.flush()

    topic_repo = TopicRepository(session)
    topic = await topic_repo.create(
        material_id=material.id,
        name="Topic",
        text="text",
        subject=SubjectType.other,
    )
    await session.flush()

    prog_repo = ProgressRepository(session)
    prog = await prog_repo.get_or_create(user.id, topic.id)
    assert prog.total_attempts == 0
    assert prog.correct_attempts == 0
