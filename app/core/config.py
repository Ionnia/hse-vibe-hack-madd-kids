from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # DB
    database_url: str = Field(default="postgresql+asyncpg://tutor:tutor@localhost:5432/tutor")
    database_url_sync: str = Field(default="postgresql://tutor:tutor@localhost:5432/tutor")

    # Telegram
    telegram_token: str = Field(default="")
    telegram_webhook_url: str = Field(default="")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")

    # LLM
    llm_provider: str = Field(default="stub")  # stub, openai, ollama
    llm_model: str = Field(default="gpt-4o-mini")
    llm_api_key: str = Field(default="")
    llm_base_url: str = Field(default="http://localhost:11434")

    # Storage
    storage_backend: str = Field(default="local")
    storage_local_path: str = Field(default="./uploads")

    # OCR
    ocr_backend: str = Field(default="stub")

    # Transcription
    transcription_backend: str = Field(default="stub")  # stub, whisper_api, local_whisper
    whisper_model_size: str = Field(default="base")     # tiny, base, small, medium, large

    # Web Search
    web_search_backend: str = Field(default="duckduckgo")  # stub, duckduckgo
    web_search_results_count: int = Field(default=5)

    class Config:
        env_file = ".env"


settings = Settings()
