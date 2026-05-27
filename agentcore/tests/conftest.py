import pytest
from fastapi.testclient import TestClient

from agentcore.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}
