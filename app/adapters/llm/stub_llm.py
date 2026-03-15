import re

from app.adapters.llm.base import BaseLLM
from app.core.constants import ReviewVerdict
from app.schemas.schemas import ReviewResult, TaskSchema, TopicSchema


class StubLLM(BaseLLM):
    async def extract_topics(self, text: str) -> list[TopicSchema]:
        return [
            TopicSchema(
                name="Introduction to the Subject",
                text="This topic covers the foundational concepts introduced in the provided material. "
                     "It includes key definitions, principles, and terminology that form the basis of understanding.",
                subject="other",
            ),
            TopicSchema(
                name="Core Principles and Applications",
                text="This topic explores the core principles discussed in the material and examines "
                     "how they are applied in practical scenarios. It includes examples and case studies.",
                subject="other",
            ),
        ]

    async def generate_tutor_task(self, topic: TopicSchema, level: str, previous_questions: list[str] | None = None) -> TaskSchema:
        return TaskSchema(
            type="flash",
            question=f"What is the main concept covered in the topic '{topic.name}'?",
            answer=f"The topic '{topic.name}' covers: {topic.text[:200]}...",
            difficulty=2,
            explanation=f"This flashcard tests your understanding of the key ideas in {topic.name}.",
            hints=[
                "Think about the key definitions introduced.",
                "Consider the practical applications mentioned.",
            ],
        )

    async def evaluate_answer(
        self, question: str, correct_answer: str, user_answer: str
    ) -> ReviewResult:
        correct_lower = correct_answer.strip().lower()
        user_lower = user_answer.strip().lower()

        if correct_lower == user_lower:
            return ReviewResult(
                verdict=ReviewVerdict.correct,
                score=1.0,
                feedback="Excellent! Your answer is exactly correct.",
            )

        # Check word overlap
        correct_words = set(re.findall(r"\w+", correct_lower))
        user_words = set(re.findall(r"\w+", user_lower))
        if correct_words and user_words:
            overlap = len(correct_words & user_words) / len(correct_words)
            if overlap >= 0.7:
                return ReviewResult(
                    verdict=ReviewVerdict.correct,
                    score=min(overlap, 1.0),
                    feedback="Great job! Your answer captures the key points.",
                )
            elif overlap >= 0.4:
                return ReviewResult(
                    verdict=ReviewVerdict.partial,
                    score=overlap,
                    feedback=f"Partially correct. You covered {int(overlap * 100)}% of the key points. "
                             f"The correct answer is: {correct_answer}",
                )

        return ReviewResult(
            verdict=ReviewVerdict.incorrect,
            score=0.0,
            feedback=f"Incorrect. The correct answer is: {correct_answer}",
        )

    async def answer_question(self, topic_name: str, topic_text: str, question: str) -> str:
        return f"[Stub] Ответ на вопрос «{question}» по теме «{topic_name}»: {topic_text[:200]}"

    async def normalize_text(self, text: str) -> str:
        # Basic Python string cleaning
        text = text.strip()
        # Collapse multiple whitespace (but preserve newlines)
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            line = re.sub(r"[ \t]+", " ", line).strip()
            cleaned_lines.append(line)
        # Collapse more than 2 consecutive empty lines
        result_lines: list[str] = []
        empty_count = 0
        for line in cleaned_lines:
            if line == "":
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)
        return "\n".join(result_lines)
