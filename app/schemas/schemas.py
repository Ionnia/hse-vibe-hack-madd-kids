from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import (
    InputType,
    MaterialStatus,
    ProgressLevel,
    ReviewVerdict,
    SubjectType,
    TaskType,
)


# ---------- User ----------

class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: str | None = None


class UserRead(BaseModel):
    id: UUID
    telegram_id: int
    username: str | None
    full_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Material ----------

class MaterialCreate(BaseModel):
    user_id: UUID
    title: str | None = None


class MaterialRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    status: MaterialStatus
    raw_text: str | None
    normalized_text: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Asset ----------

class AssetCreate(BaseModel):
    material_id: UUID
    input_type: InputType
    file_path: str | None = None
    telegram_file_id: str | None = None


class AssetRead(BaseModel):
    id: UUID
    material_id: UUID
    input_type: InputType
    file_path: str | None
    telegram_file_id: str | None
    extracted_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Topic ----------

class TopicSchema(BaseModel):
    """Schema for LLM structured output."""
    name: str
    text: str
    subject: Literal["math", "physics", "chemistry", "biology", "programming", "language", "other"]


class TopicRead(BaseModel):
    id: UUID
    material_id: UUID
    name: str
    text: str
    subject: SubjectType
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Chunk ----------

class ChunkPayload(BaseModel):
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    source_asset_id: UUID | None = None


# ---------- Task ----------

class TaskSchema(BaseModel):
    """Schema for LLM structured output."""
    type: Literal["flash", "exercise"]
    question: str
    answer: str
    difficulty: int = Field(ge=1, le=5)
    explanation: str | None = None
    hints: list[str] = Field(default_factory=list)


class TutorTaskRead(BaseModel):
    id: UUID
    topic_id: UUID
    user_id: UUID
    type: TaskType
    question: str
    answer: str
    explanation: str | None
    difficulty: int
    hints: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Review ----------

class ReviewRequest(BaseModel):
    task_id: UUID
    user_answer: str


class ReviewResult(BaseModel):
    verdict: ReviewVerdict
    score: float = Field(ge=0.0, le=1.0)
    feedback: str | None = None


# ---------- Progress ----------

class ProgressRead(BaseModel):
    topic_id: UUID
    level: ProgressLevel
    total_attempts: int
    correct_attempts: int

    model_config = {"from_attributes": True}


# ---------- Repetition ----------

class RepetitionStateRead(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    interval_days: float
    ease_factor: float
    next_review_at: datetime
    last_reviewed_at: datetime | None
    review_count: int

    model_config = {"from_attributes": True}


# ---------- Study session ----------

class StudySessionSummary(BaseModel):
    tasks_completed: int
    correct: int
    incorrect: int
    partial: int
    xp_earned: int


# ---------- Text processing ----------

class NormalizedTextPayload(BaseModel):
    text: str
    source_asset_ids: list[UUID] = Field(default_factory=list)


class ExtractedFragment(BaseModel):
    source_type: InputType
    text: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    metadata: dict = Field(default_factory=dict)


# ---------- Upload ----------

class UploadResponse(BaseModel):
    material_id: UUID
    status: MaterialStatus
    message: str


# ---------- Topic extraction ----------

class TopicExtractionRequest(BaseModel):
    material_id: UUID


class TopicExtractionResponse(BaseModel):
    material_id: UUID
    topics: list[TopicRead]
