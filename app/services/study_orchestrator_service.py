from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.base import BaseLLM
from app.adapters.llm.factory import get_llm
from app.core.constants import ReviewVerdict
from app.models.models import TutorTask
from app.repositories.repos import RepetitionRepository, TopicRepository
from app.schemas.schemas import ReviewResult
from app.services.progress_service import ProgressService
from app.services.repetition_service import RepetitionService
from app.services.review_service import ReviewService
from app.services.tutor_task_service import TutorTaskService


class StudyOrchestratorService:
    def __init__(self, session: AsyncSession, llm: BaseLLM | None = None) -> None:
        self.session = session
        self.llm = llm or get_llm()
        self.topic_repo = TopicRepository(session)
        self.repetition_repo = RepetitionRepository(session)
        self.tutor_task_service = TutorTaskService(session, self.llm)
        self.review_service = ReviewService(session, self.llm)
        self.progress_service = ProgressService(session)
        self.repetition_service = RepetitionService(session)

    async def request_next_task(self, user_id: UUID) -> TutorTask | None:
        # Get due repetitions
        due = await self.repetition_service.get_due_topics(user_id)
        if not due:
            # Fall back to any topic this user has progress on
            return None

        # Pick the most overdue topic
        most_overdue = min(due, key=lambda s: s.next_review_at)
        topic_id = most_overdue.topic_id

        return await self.tutor_task_service.get_next_task(user_id, topic_id)

    async def submit_answer(
        self, user_id: UUID, task_id: UUID, answer: str
    ) -> tuple[ReviewResult, object]:
        result = await self.review_service.review(user_id, task_id, answer)

        # Get task to find topic_id
        from app.repositories.repos import TutorTaskRepository
        task_repo = TutorTaskRepository(self.session)
        task = await task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        was_correct = result.verdict == ReviewVerdict.correct
        progress = await self.progress_service.update(user_id, task.topic_id, result.verdict)
        await self.repetition_service.update_interval(user_id, task.topic_id, was_correct)

        return result, progress
