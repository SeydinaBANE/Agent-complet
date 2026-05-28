from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_requires_api_key(client: TestClient) -> None:
    response = client.post("/api/v1/agents/run", json={"goal": "test"})
    assert response.status_code == 401


def test_run_accepted_with_api_key(client: TestClient, api_headers: dict) -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={"goal": "Search for the latest news about AI"},
        headers=api_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "pending"


def test_list_tools(client: TestClient, api_headers: dict) -> None:
    response = client.get("/api/v1/tools", headers=api_headers)
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all("name" in t for t in tools)
