from app.adapters.llm.base import BaseLLM


def get_llm() -> BaseLLM:
    from app.core.config import settings

    if settings.llm_provider == "openai":
        from app.adapters.llm.openai_llm import OpenAILLM
        return OpenAILLM(api_key=settings.llm_api_key, model=settings.llm_model)

    if settings.llm_provider == "ollama":
        from app.adapters.llm.stub_llm import StubLLM
        return StubLLM()  # replace with OllamaLLM when needed

    from app.adapters.llm.stub_llm import StubLLM
    return StubLLM()
