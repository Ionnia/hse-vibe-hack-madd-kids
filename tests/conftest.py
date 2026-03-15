import asyncio
from collections.abc import AsyncGenerator
from typing import Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autocommit=False, autoflush=False)
    async with session_factory() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    from app.api.main import app
    from app.db.session import get_session

    # Override DB dependency with in-memory SQLite
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_session():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()
