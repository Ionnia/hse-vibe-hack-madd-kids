import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.adapters.llm.base import BaseLLM
from app.core.constants import ReviewVerdict
from app.schemas.schemas import ReviewResult, TaskSchema, TopicSchema

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def extract_topics(self, text: str) -> list[TopicSchema]:
        prompt = f"""Извлеки ключевые учебные темы из следующего текста. Поля name и text — НА РУССКОМ ЯЗЫКЕ.
Верни JSON объект с полем "topics" — массивом тем. Каждая тема:
- name: краткое название темы (строка, НА РУССКОМ)
- text: краткое резюме темы 2-3 предложения (строка, НА РУССКОМ)
- subject: одно из ["math", "physics", "chemistry", "biology", "programming", "language", "other"]

Текст:
{text[:3000]}

Верни только валидный JSON объект, без markdown."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            topics_raw: list[dict[str, Any]] = data.get("topics", data) if isinstance(data, dict) else data
            if not isinstance(topics_raw, list):
                topics_raw = list(data.values())[0] if data else []
            return [
                TopicSchema(
                    name=t.get("name", "Тема"),
                    text=t.get("text", ""),
                    subject=t.get("subject", "other"),
                )
                for t in topics_raw
                if isinstance(t, dict)
            ]
        except Exception as e:
            logger.error("extract_topics failed: %s", e)
            return []

    async def generate_tutor_task(
        self, topic: TopicSchema, level: str, previous_questions: list[str] | None = None
    ) -> TaskSchema:
        difficulty_map = {"unknown": 1, "weak": 2, "learning": 3, "good": 4, "mastered": 5}
        difficulty = difficulty_map.get(level, 2)

        prev_block = ""
        if previous_questions:
            listed = "\n".join(f"- {q}" for q in previous_questions)
            prev_block = f"\n\nAlready asked questions (DO NOT repeat these):\n{listed}"

        prompt = f"""Сгенерируй учебное задание по следующей теме. Все поля question, answer, explanation, hints — СТРОГО НА РУССКОМ ЯЗЫКЕ.
Уровень: {level} (сложность {difficulty}/5)

Тема: {topic.name}
Содержание: {topic.text}{prev_block}

Верни JSON объект:
- type: "flash" или "exercise"
- question: вопрос студенту (строка, НОВЫЙ, непохожий на уже заданные, НА РУССКОМ)
- answer: правильный ответ (строка, НА РУССКОМ)
- difficulty: {difficulty} (целое число)
- explanation: краткое объяснение (строка, НА РУССКОМ)
- hints: список из 1-2 подсказок (массив строк, НА РУССКОМ)

Верни только валидный JSON, без markdown."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            return TaskSchema(
                type=data.get("type", "flash"),
                question=data.get("question", "Что вы знаете по этой теме?"),
                answer=data.get("answer", topic.text[:200]),
                difficulty=data.get("difficulty", difficulty),
                explanation=data.get("explanation"),
                hints=data.get("hints", []),
            )
        except Exception as e:
            logger.error("generate_tutor_task failed: %s", e)
            return TaskSchema(
                type="flash",
                question=f"Что является ключевой идеей темы «{topic.name}»?",
                answer=topic.text[:300],
                difficulty=difficulty,
            )

    async def evaluate_answer(
        self, question: str, correct_answer: str, user_answer: str
    ) -> ReviewResult:
        prompt = f"""Evaluate the student's answer.

Question: {question}
Correct answer: {correct_answer}
Student's answer: {user_answer}

Return a JSON object with:
- verdict: "correct", "partial", or "incorrect"
- score: float from 0.0 to 1.0
- feedback: short feedback in Russian (1-2 sentences)

Return only valid JSON, no markdown."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            verdict_str = data.get("verdict", "incorrect")
            verdict = ReviewVerdict(verdict_str) if verdict_str in ("correct", "partial", "incorrect") else ReviewVerdict.incorrect
            return ReviewResult(
                verdict=verdict,
                score=float(data.get("score", 0.0)),
                feedback=data.get("feedback", ""),
            )
        except Exception as e:
            logger.error("evaluate_answer failed: %s", e)
            import re
            correct_words = set(re.findall(r"\w+", correct_answer.lower()))
            user_words = set(re.findall(r"\w+", user_answer.lower()))
            overlap = len(correct_words & user_words) / max(len(correct_words), 1)
            if overlap >= 0.7:
                return ReviewResult(verdict=ReviewVerdict.correct, score=overlap, feedback="Верно!")
            elif overlap >= 0.4:
                return ReviewResult(verdict=ReviewVerdict.partial, score=overlap, feedback=f"Частично. Правильный ответ: {correct_answer}")
            return ReviewResult(verdict=ReviewVerdict.incorrect, score=0.0, feedback=f"Неверно. Правильный ответ: {correct_answer}")

    async def answer_question(self, topic_name: str, topic_text: str, question: str) -> str:
        prompt = f"""Ты учебный помощник. Отвечай на вопрос студента строго на основе материала темы. Отвечай на русском языке, кратко и по делу.

Тема: {topic_name}
Материал: {topic_text}

Вопрос студента: {question}

Если ответ нельзя найти в материале — честно скажи об этом."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content or "Не удалось получить ответ."
        except Exception as e:
            logger.error("answer_question failed: %s", e)
            return "Ошибка при обращении к LLM."

    async def normalize_text(self, text: str) -> str:
        import re
        text = text.strip()
        lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()]
        return "\n".join(lines)
