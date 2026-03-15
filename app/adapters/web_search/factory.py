from app.adapters.web_search.base import BaseWebSearch


def get_web_search() -> BaseWebSearch:
    from app.core.config import settings

    if settings.web_search_backend == "duckduckgo":
        from app.adapters.web_search.duckduckgo import DuckDuckGoWebSearch
        return DuckDuckGoWebSearch()

    from app.adapters.web_search.stub import StubWebSearch
    return StubWebSearch()
