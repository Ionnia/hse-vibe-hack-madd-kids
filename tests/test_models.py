from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.constants import (
    InputType,
    MaterialStatus,
    ProgressLevel,
    ReviewVerdict,
    SubjectType,
    TaskType,
)
from app.models.models import (
    GamificationProfile,
    MaterialAsset,
    RepetitionState,
    ReviewLog,
    StudyMaterial,
    Topic,
    TopicChunk,
    TutorTask,
    User,
    UserTopicProgress,
)


def test_user_instantiation():
    user = User(telegram_id=12345, username="testuser", full_name="Test User")
    assert user.telegram_id == 12345
    assert user.username == "testuser"


def test_study_material_instantiation():
    uid = uuid4()
    m = StudyMaterial(user_id=uid, title="Test Material", status=MaterialStatus.uploaded)
    assert m.status == MaterialStatus.uploaded


def test_material_asset_instantiation():
    mid = uuid4()
    asset = MaterialAsset(material_id=mid, input_type=InputType.text)
    assert asset.input_type == InputType.text


def test_topic_instantiation():
    mid = uuid4()
    topic = Topic(material_id=mid, name="Test Topic", text="Some text", subject=SubjectType.other)
    assert topic.subject == SubjectType.other


def test_topic_chunk_instantiation():
    tid = uuid4()
    mid = uuid4()
    chunk = TopicChunk(
        topic_id=tid,
        material_id=mid,
        chunk_index=0,
        text="chunk text",
        char_start=0,
        char_end=10,
    )
    assert chunk.chunk_index == 0


def test_tutor_task_instantiation():
    tid = uuid4()
    uid = uuid4()
    task = TutorTask(
        topic_id=tid,
        user_id=uid,
        type=TaskType.flash,
        question="What is 2+2?",
        answer="4",
        difficulty=1,
        hints=[],
    )
    assert task.type == TaskType.flash


def test_review_log_instantiation():
    task_id = uuid4()
    user_id = uuid4()
    log = ReviewLog(
        task_id=task_id,
        user_id=user_id,
        user_answer="4",
        verdict=ReviewVerdict.correct,
        score=1.0,
    )
    assert log.verdict == ReviewVerdict.correct


def test_user_topic_progress_instantiation():
    uid = uuid4()
    tid = uuid4()
    prog = UserTopicProgress(user_id=uid, topic_id=tid, level=ProgressLevel.unknown)
    assert prog.level == ProgressLevel.unknown


def test_repetition_state_instantiation():
    uid = uuid4()
    tid = uuid4()
    now = datetime.now(timezone.utc)
    state = RepetitionState(
        user_id=uid,
        topic_id=tid,
        interval_days=1.0,
        ease_factor=2.5,
        next_review_at=now,
    )
    assert state.interval_days == 1.0


def test_gamification_profile_instantiation():
    uid = uuid4()
    profile = GamificationProfile(user_id=uid, xp=0, level=1, streak_days=0)
    assert profile.xp == 0


def test_material_status_enum():
    assert MaterialStatus.uploaded == "uploaded"
    assert MaterialStatus.ready == "ready"
    assert MaterialStatus.failed == "failed"


def test_task_type_enum():
    assert TaskType.flash == "flash"
    assert TaskType.exercise == "exercise"


def test_subject_type_enum():
    subjects = [s.value for s in SubjectType]
    assert "math" in subjects
    assert "other" in subjects
