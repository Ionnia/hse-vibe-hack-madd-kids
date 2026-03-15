from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.base import BaseLLM
from app.adapters.llm.factory import get_llm
from app.repositories.repos import ReviewLogRepository, TutorTaskRepository
from app.schemas.schemas import ReviewResult


class ReviewService:
    def __init__(self, session: AsyncSession, llm: BaseLLM | None = None) -> None:
        self.session = session
        self.llm = llm or get_llm()
        self.task_repo = TutorTaskRepository(session)
        self.review_repo = ReviewLogRepository(session)

    async def review(self, user_id: UUID, task_id: UUID, user_answer: str) -> ReviewResult:
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        result = await self.llm.evaluate_answer(
            question=task.question,
            correct_answer=task.answer,
            user_answer=user_answer,
        )

        await self.review_repo.create(
            task_id=task_id,
            user_id=user_id,
            user_answer=user_answer,
            verdict=result.verdict,
            score=result.score,
            feedback=result.feedback,
        )

        return result
