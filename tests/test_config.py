import pytest

from app.core.config import Settings


def test_settings_loads_without_errors():
    s = Settings()
    assert s.database_url.startswith("postgresql")
    assert s.llm_provider == "stub"
    assert s.storage_backend == "local"
    assert s.ocr_backend == "stub"
    assert s.transcription_backend == "stub"


def test_settings_defaults():
    s = Settings()
    assert s.celery_broker_url == "redis://localhost:6379/0"
    assert s.celery_result_backend == "redis://localhost:6379/1"
    assert s.llm_model == "gpt-4o-mini"
    assert s.storage_local_path == "./uploads"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    s = Settings()
    assert s.llm_provider == "openai"
    assert s.storage_backend == "s3"
