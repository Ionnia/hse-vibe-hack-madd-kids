import asyncio
import logging
from functools import partial

from app.adapters.web_search.base import BaseWebSearch, SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoWebSearch(BaseWebSearch):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        loop = asyncio.get_running_loop()
        try:
            results = await loop.run_in_executor(None, partial(self._sync_search, query, max_results))
            return results
        except Exception as e:
            logger.error("DuckDuckGo search failed for query '%s': %s", query, e)
            return []

    def _sync_search(self, query: str, max_results: int) -> list[SearchResult]:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                    )
                )
        return results
