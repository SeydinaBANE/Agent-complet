# AgentCore

Multi-agent orchestration API — autonomous agents with tools, memory, guardrails, and reliability evaluation.

## Stack
Python 3.12 · FastAPI · LangGraph · OpenRouter · PostgreSQL · Redis · ARQ · Docker

## API

All routes under `/api/v1/`. Auth: `X-API-Key` header.

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/v1/agents/run` | Start an agent run (async, returns `run_id`) |
| `GET` | `/api/v1/agents/{run_id}` | Get run status and cost |
| `POST` | `/api/v1/agents/{run_id}/stop` | Kill switch |
| `GET` | `/api/v1/agents` | List runs (cursor pagination) |
| `WS` | `/api/v1/agents/{run_id}/stream` | Real-time action stream |
| `GET` | `/api/v1/tools` | List available tools |
| `POST` | `/api/v1/eval/run` | Start adversarial eval suite |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (checks DB + Redis) |
| `GET` | `/docs` | OpenAPI docs |
| `GET` | `/metrics` | Prometheus metrics |

## Setup (local, no Docker)

```bash
# Python 3.12 required
pip install -r requirements-dev.txt

# Configure environment
cp ../.env.example ../.env
# Fill OPENROUTER_API_KEY, DATABASE_URL, REDIS_URL, AGENTCORE_API_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn agentcore.main:app --reload --port 8000
```

## Tests

```bash
pytest                              # all tests
pytest tests/unit/                  # unit tests only (no network)
pytest tests/integration/           # integration tests (needs DB + Redis)
pytest -m "not slow"               # skip slow eval tests
pytest --cov=agentcore --cov-report=html  # with coverage report
```
