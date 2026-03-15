import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.factory import get_llm
from app.adapters.web_search.factory import get_web_search
from app.core.config import settings
from app.repositories.repos import TopicRepository

logger = logging.getLogger(__name__)


class TopicEnrichmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.topic_repo = TopicRepository(session)
        self.llm = get_llm()
        self.searcher = get_web_search()

    async def enrich(self, topic_id: UUID) -> bool:
        """Search the web for topic info, synthesize via LLM, update topic text."""
        topic = await self.topic_repo.get_by_id(topic_id)
        if topic is None:
            logger.warning("enrich: topic %s not found", topic_id)
            return False

        if topic.enriched_at is not None:
            logger.info("enrich: topic %s already enriched, skipping", topic_id)
            return False

        query = f"{topic.name} {topic.subject.value}"
        logger.info("enrich: searching web for '%s'", query)

        search_results = await self.searcher.search(
            query, max_results=settings.web_search_results_count
        )

        if not search_results:
            logger.warning("enrich: no search results for topic %s", topic_id)
            return False

        logger.info("enrich: got %d results, enriching via LLM", len(search_results))
        enriched_text = await self.llm.enrich_topic(
            topic_name=topic.name,
            topic_text=topic.text,
            search_results=search_results,
        )

        sources = [r.url for r in search_results if r.url]
        await self.topic_repo.update_enrichment(
            topic_id=topic_id,
            enriched_text=enriched_text,
            sources=sources,
        )

        logger.info("enrich: topic %s enriched successfully (%d sources)", topic_id, len(sources))
        return True
