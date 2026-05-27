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

## Architecture

```
POST /api/v1/agents/run → ARQ queue → LangGraph StateGraph
                                           ↓
                                   planner  (decompose goal into tasks)
                                           ↓
                                   executor (run tool, check guardrails)
                                           ↓
                                   validator (synthesize answer / retry)
```

The graph is async and runs in a background ARQ worker. Results stream via Redis pub/sub to the WebSocket endpoint.

## Guardrails

- **Budget**: `budget_usd` per run — aborts if `cost_usd` exceeded
- **Iterations**: default max 10 — prevents loops
- **Scope**: blocks `localhost`, `169.254.169.254`, `*.internal`
- **Kill switch**: `POST /stop` sets a Redis cancel key; executor checks it every iteration
- **Retry**: `tenacity` retries LLM calls up to 3× with exponential backoff on 429/5xx

## Tests

```bash
pytest                              # all tests (64 tests · 90% coverage)
pytest tests/unit/                  # unit tests only (no network)
pytest tests/integration/           # integration tests (needs DB + Redis)
pytest --cov=agentcore --cov-report=html  # with HTML coverage report
```
