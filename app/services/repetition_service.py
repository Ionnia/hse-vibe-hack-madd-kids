from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RepetitionState
from app.repositories.repos import RepetitionRepository


class RepetitionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RepetitionRepository(session)

    async def update_interval(
        self, user_id: UUID, topic_id: UUID, was_correct: bool
    ) -> RepetitionState:
        state = await self.repo.get_or_create(user_id, topic_id)

        if was_correct:
            new_interval = state.interval_days * state.ease_factor
        else:
            new_interval = 1.0

        new_interval = max(1.0, new_interval)
        next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)

        return await self.repo.update_state(
            user_id=user_id,
            topic_id=topic_id,
            interval_days=new_interval,
            ease_factor=state.ease_factor,
            next_review_at=next_review,
        )

    async def get_due_topics(self, user_id: UUID) -> list[RepetitionState]:
        return await self.repo.get_due_repetitions(user_id)
