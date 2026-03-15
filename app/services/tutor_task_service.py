from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.base import BaseLLM
from app.adapters.llm.factory import get_llm
from app.core.constants import TaskType
from app.models.models import TutorTask
from app.repositories.repos import ProgressRepository, TopicRepository, TutorTaskRepository
from app.schemas.schemas import TopicSchema


class TutorTaskService:
    def __init__(self, session: AsyncSession, llm: BaseLLM | None = None) -> None:
        self.session = session
        self.llm = llm or get_llm()
        self.topic_repo = TopicRepository(session)
        self.task_repo = TutorTaskRepository(session)
        self.progress_repo = ProgressRepository(session)

    async def get_next_task(self, user_id: UUID, topic_id: UUID) -> TutorTask:
        topic = await self.topic_repo.get_by_id(topic_id)
        if topic is None:
            raise ValueError(f"Topic {topic_id} not found")

        progress = await self.progress_repo.get_or_create(user_id, topic_id)
        level = progress.level.value

        # Load recent questions for this topic to avoid repetition
        prev_tasks = await self.task_repo.get_by_user_and_topic(user_id, topic_id)
        previous_questions = [t.question for t in prev_tasks[-10:]]

        topic_schema = TopicSchema(
            name=topic.name,
            text=topic.text,
            subject=topic.subject.value,  # type: ignore[arg-type]
        )

        task_schema = await self.llm.generate_tutor_task(
            topic_schema, level, previous_questions=previous_questions
        )

        task = await self.task_repo.create(
            topic_id=topic_id,
            user_id=user_id,
            task_type=TaskType(task_schema.type),
            question=task_schema.question,
            answer=task_schema.answer,
            difficulty=task_schema.difficulty,
            explanation=task_schema.explanation,
            hints=task_schema.hints,
        )
        return task
