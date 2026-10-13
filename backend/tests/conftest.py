"""pytest configuration and shared fixtures."""
from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# SQLite in-memory for offline tests (no Postgres required)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create all tables in SQLite once per test session."""
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        # SQLite doesn't support Postgres-specific types; ORM uses String/JSON
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fresh DB session per test, rolled back after."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Test client with DB override and LLM health mocked."""
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    # Always mock LLM health check so tests don't need real Ollama
    with patch("app.services.llm.check_health", return_value=(True, "ok")):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm_complete():
    """Mock LLM complete — prevents real API calls in all tests."""
    with patch("app.services.llm.complete") as mock:
        mock.return_value = ("Mocked LLM response [1]", "mock", "mock-model")
        yield mock


@pytest.fixture
def mock_ollama_health():
    """Mock Ollama health check."""
    with patch("app.services.llm.check_health", return_value=(True, "ok")) as mock:
        yield mock


def make_uuid() -> str:
    return str(uuid.uuid4())
