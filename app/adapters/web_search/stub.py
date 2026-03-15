from app.adapters.web_search.base import BaseWebSearch, SearchResult


class StubWebSearch(BaseWebSearch):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"[Stub] Результат по запросу: {query}",
                url="https://example.com",
                snippet=f"Stub-сниппет для запроса «{query}». Используется в тестах.",
            )
        ]
