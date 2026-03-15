from abc import ABC, abstractmethod

from app.schemas.schemas import ReviewResult, TaskSchema, TopicSchema


class BaseLLM(ABC):
    @abstractmethod
    async def extract_topics(self, text: str) -> list[TopicSchema]:
        """Extract topics from text."""
        ...

    @abstractmethod
    async def generate_tutor_task(
        self, topic: TopicSchema, level: str, previous_questions: list[str] | None = None
    ) -> TaskSchema:
        """Generate a tutor task for the given topic."""
        ...

    @abstractmethod
    async def evaluate_answer(
        self, question: str, correct_answer: str, user_answer: str
    ) -> ReviewResult:
        """Evaluate user's answer to a question."""
        ...

    @abstractmethod
    async def normalize_text(self, text: str) -> str:
        """Normalize and clean input text."""
        ...

    @abstractmethod
    async def answer_question(self, topic_name: str, topic_text: str, question: str) -> str:
        """Answer a user question based on topic content."""
        ...
