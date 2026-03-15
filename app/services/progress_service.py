from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReviewVerdict
from app.models.models import UserTopicProgress
from app.repositories.repos import ProgressRepository


class ProgressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.progress_repo = ProgressRepository(session)

    async def update(
        self, user_id: UUID, topic_id: UUID, verdict: ReviewVerdict
    ) -> UserTopicProgress:
        was_correct = verdict == ReviewVerdict.correct
        return await self.progress_repo.update_progress(user_id, topic_id, was_correct)
