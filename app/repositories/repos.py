from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MaterialStatus, ProgressLevel, ReviewVerdict
from app.models.models import (
    MaterialAsset,
    RepetitionState,
    ReviewLog,
    StudyMaterial,
    Topic,
    TutorTask,
    User,
    UserTopicProgress,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, username: str | None = None, full_name: str | None = None) -> User:
        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, telegram_id: int, username: str | None = None, full_name: str | None = None) -> User:
        # Use upsert to avoid race condition on concurrent /start
        now = datetime.now(timezone.utc)
        from uuid import uuid4
        stmt = (
            pg_insert(User)
            .values(
                id=uuid4(),
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["telegram_id"],
                set_={"username": username, "full_name": full_name, "updated_at": now},
            )
            .returning(User)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


class MaterialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, title: str | None = None) -> StudyMaterial:
        material = StudyMaterial(user_id=user_id, title=title)
        self.session.add(material)
        await self.session.flush()
        return material

    async def get_by_id(self, material_id: UUID) -> StudyMaterial | None:
        result = await self.session.execute(
            select(StudyMaterial).where(StudyMaterial.id == material_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> list[StudyMaterial]:
        result = await self.session.execute(
            select(StudyMaterial).where(StudyMaterial.user_id == user_id).order_by(StudyMaterial.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, material_id: UUID, status: MaterialStatus) -> None:
        await self.session.execute(
            update(StudyMaterial)
            .where(StudyMaterial.id == material_id)
            .values(status=status)
        )

    async def update_texts(
        self,
        material_id: UUID,
        raw_text: str | None = None,
        normalized_text: str | None = None,
    ) -> None:
        values: dict = {}
        if raw_text is not None:
            values["raw_text"] = raw_text
        if normalized_text is not None:
            values["normalized_text"] = normalized_text
        if values:
            await self.session.execute(
                update(StudyMaterial).where(StudyMaterial.id == material_id).values(**values)
            )


class AssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        material_id: UUID,
        input_type,
        file_path: str | None = None,
        telegram_file_id: str | None = None,
        extracted_text: str | None = None,
    ) -> MaterialAsset:
        asset = MaterialAsset(
            material_id=material_id,
            input_type=input_type,
            file_path=file_path,
            telegram_file_id=telegram_file_id,
            extracted_text=extracted_text,
        )
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def get_by_material_id(self, material_id: UUID) -> list[MaterialAsset]:
        result = await self.session.execute(
            select(MaterialAsset).where(MaterialAsset.material_id == material_id)
        )
        return list(result.scalars().all())


class TopicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, material_id: UUID, name: str, text: str, subject) -> Topic:
        topic = Topic(material_id=material_id, name=name, text=text, subject=subject)
        self.session.add(topic)
        await self.session.flush()
        return topic

    async def get_by_material_id(self, material_id: UUID) -> list[Topic]:
        result = await self.session.execute(
            select(Topic).where(Topic.material_id == material_id).order_by(Topic.created_at)
        )
        return list(result.scalars().all())

    async def get_by_id(self, topic_id: UUID) -> Topic | None:
        result = await self.session.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def update_enrichment(
        self, topic_id: UUID, enriched_text: str, sources: list[str]
    ) -> None:
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(Topic)
            .where(Topic.id == topic_id)
            .values(text=enriched_text, enriched_at=now, enrichment_sources=sources)
        )


class TutorTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        topic_id: UUID,
        user_id: UUID,
        task_type,
        question: str,
        answer: str,
        difficulty: int = 1,
        explanation: str | None = None,
        hints: list[str] | None = None,
    ) -> TutorTask:
        task = TutorTask(
            topic_id=topic_id,
            user_id=user_id,
            type=task_type,
            question=question,
            answer=answer,
            difficulty=difficulty,
            explanation=explanation,
            hints=hints or [],
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: UUID) -> TutorTask | None:
        result = await self.session.execute(select(TutorTask).where(TutorTask.id == task_id))
        return result.scalar_one_or_none()

    async def get_by_user_and_topic(self, user_id: UUID, topic_id: UUID) -> list[TutorTask]:
        result = await self.session.execute(
            select(TutorTask)
            .where(TutorTask.user_id == user_id, TutorTask.topic_id == topic_id)
            .order_by(TutorTask.created_at.desc())
        )
        return list(result.scalars().all())


class ReviewLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        task_id: UUID,
        user_id: UUID,
        user_answer: str,
        verdict: ReviewVerdict,
        score: float,
        feedback: str | None = None,
    ) -> ReviewLog:
        log = ReviewLog(
            task_id=task_id,
            user_id=user_id,
            user_answer=user_answer,
            verdict=verdict,
            score=score,
            feedback=feedback,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_by_task_id(self, task_id: UUID) -> list[ReviewLog]:
        result = await self.session.execute(
            select(ReviewLog).where(ReviewLog.task_id == task_id).order_by(ReviewLog.created_at)
        )
        return list(result.scalars().all())


class ProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, user_id: UUID, topic_id: UUID) -> UserTopicProgress:
        result = await self.session.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.topic_id == topic_id,
            )
        )
        progress = result.scalar_one_or_none()
        if progress is None:
            progress = UserTopicProgress(user_id=user_id, topic_id=topic_id)
            self.session.add(progress)
            await self.session.flush()
        return progress

    async def update_progress(
        self, user_id: UUID, topic_id: UUID, was_correct: bool
    ) -> UserTopicProgress:
        progress = await self.get_or_create(user_id, topic_id)
        progress.total_attempts += 1
        if was_correct:
            progress.correct_attempts += 1

        ratio = progress.correct_attempts / max(progress.total_attempts, 1)
        if ratio >= 0.9 and progress.total_attempts >= 5:
            progress.level = ProgressLevel.mastered
        elif ratio >= 0.75:
            progress.level = ProgressLevel.good
        elif ratio >= 0.5:
            progress.level = ProgressLevel.learning
        elif progress.total_attempts > 0:
            progress.level = ProgressLevel.weak

        await self.session.flush()
        return progress

    async def get_by_user(self, user_id: UUID) -> list[UserTopicProgress]:
        result = await self.session.execute(
            select(UserTopicProgress).where(UserTopicProgress.user_id == user_id)
        )
        return list(result.scalars().all())


class RepetitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, user_id: UUID, topic_id: UUID) -> RepetitionState:
        result = await self.session.execute(
            select(RepetitionState).where(
                RepetitionState.user_id == user_id,
                RepetitionState.topic_id == topic_id,
            )
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = RepetitionState(
                user_id=user_id,
                topic_id=topic_id,
                next_review_at=datetime.now(timezone.utc),
            )
            self.session.add(state)
            await self.session.flush()
        return state

    async def update_state(
        self, user_id: UUID, topic_id: UUID, interval_days: float, ease_factor: float, next_review_at: datetime
    ) -> RepetitionState:
        state = await self.get_or_create(user_id, topic_id)
        state.interval_days = interval_days
        state.ease_factor = ease_factor
        state.next_review_at = next_review_at
        state.last_reviewed_at = datetime.now(timezone.utc)
        state.review_count += 1
        await self.session.flush()
        return state

    async def get_due_repetitions(self, user_id: UUID) -> list[RepetitionState]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RepetitionState).where(
                RepetitionState.user_id == user_id,
                RepetitionState.next_review_at <= now,
            )
        )
        return list(result.scalars().all())
