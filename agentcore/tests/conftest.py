# ruff: noqa: E402
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("AGENTCORE_API_KEY", "test-key")

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


async def _mock_session_gen() -> AsyncGenerator[AsyncMock, None]:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))),
        )
    )
    yield session


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client with ARQ and DB mocked out."""
    mock_arq = AsyncMock()
    mock_arq.enqueue_job = AsyncMock()
    mock_arq.aclose = AsyncMock()

    with patch("agentcore.main.create_pool", AsyncMock(return_value=mock_arq)):
        # Import app AFTER patching create_pool so lifespan uses the mock
        from agentcore.db.session import get_session
        from agentcore.main import app

        app.dependency_overrides[get_session] = _mock_session_gen

        with TestClient(app) as c:
            c.app.state.arq = mock_arq  # type: ignore[attr-defined]
            yield c

        app.dependency_overrides.clear()


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}
