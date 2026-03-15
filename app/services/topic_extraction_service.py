from app.adapters.llm.base import BaseLLM
from app.adapters.llm.factory import get_llm
from app.schemas.schemas import ChunkPayload, TopicSchema


class TopicExtractionService:
    def __init__(self, llm: BaseLLM | None = None) -> None:
        self.llm = llm or get_llm()

    async def extract_topics(self, chunks: list[ChunkPayload]) -> list[TopicSchema]:
        if not chunks:
            return []

        # Combine chunks into a single text for topic extraction
        combined = "\n\n".join(chunk.text for chunk in chunks)
        topics = await self.llm.extract_topics(combined)
        return topics
