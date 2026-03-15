import uuid
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    InputType,
    MaterialStatus,
    ProgressLevel,
    ReviewVerdict,
    SubjectType,
    TaskType,
)
from app.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    materials: Mapped[list["StudyMaterial"]] = relationship("StudyMaterial", back_populates="user")
    gamification: Mapped["GamificationProfile"] = relationship("GamificationProfile", back_populates="user", uselist=False)


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[MaterialStatus] = mapped_column(
        SAEnum(MaterialStatus, name="materialstatus", create_type=True),
        default=MaterialStatus.uploaded,
        nullable=False,
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="materials")
    assets: Mapped[list["MaterialAsset"]] = relationship("MaterialAsset", back_populates="material")
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="material")
    chunks: Mapped[list["TopicChunk"]] = relationship("TopicChunk", back_populates="material")


class MaterialAsset(Base):
    __tablename__ = "material_assets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    material_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_materials.id", ondelete="CASCADE"), nullable=False)
    input_type: Mapped[InputType] = mapped_column(
        SAEnum(InputType, name="inputtype", create_type=True),
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    telegram_file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    material: Mapped["StudyMaterial"] = relationship("StudyMaterial", back_populates="assets")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    material_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_materials.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[SubjectType] = mapped_column(
        SAEnum(SubjectType, name="subjecttype", create_type=True),
        default=SubjectType.other,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enrichment_sources: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    material: Mapped["StudyMaterial"] = relationship("StudyMaterial", back_populates="topics")
    chunks: Mapped[list["TopicChunk"]] = relationship("TopicChunk", back_populates="topic")
    tutor_tasks: Mapped[list["TutorTask"]] = relationship("TutorTask", back_populates="topic")
    progress: Mapped[list["UserTopicProgress"]] = relationship("UserTopicProgress", back_populates="topic")


class TopicChunk(Base):
    __tablename__ = "topic_chunks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    topic_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    material_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_materials.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    source_asset_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    topic: Mapped["Topic | None"] = relationship("Topic", back_populates="chunks")
    material: Mapped["StudyMaterial"] = relationship("StudyMaterial", back_populates="chunks")


class TutorTask(Base):
    __tablename__ = "tutor_tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    topic_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="tasktype", create_type=True),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    hints: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="tutor_tasks")
    review_logs: Mapped[list["ReviewLog"]] = relationship("ReviewLog", back_populates="task")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tutor_tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[ReviewVerdict] = mapped_column(
        SAEnum(ReviewVerdict, name="reviewverdict", create_type=True),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    task: Mapped["TutorTask"] = relationship("TutorTask", back_populates="review_logs")


class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[ProgressLevel] = mapped_column(
        SAEnum(ProgressLevel, name="progresslevel", create_type=True),
        default=ProgressLevel.unknown,
        nullable=False,
    )
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="progress")


class RepetitionState(Base):
    __tablename__ = "repetition_states"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    interval_days: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class GamificationProfile(Base):
    __tablename__ = "gamification_profiles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="gamification")
