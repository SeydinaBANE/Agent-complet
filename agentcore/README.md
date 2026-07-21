# AgentCore

Multi-agent orchestration API — autonomous agents with tools, memory, guardrails, and reliability evaluation.

## Stack

Python 3.12 · FastAPI · LangGraph · OpenRouter · PostgreSQL · Redis · ARQ · Docker

## Architecture

AgentCore follows **Hexagonal Architecture** (Ports & Adapters):

```
Ports (interfaces)  →  Adapters (implementations)
    ↓                         ↓
Domain (business logic)  ←  Application (use cases)
    ↓                         ↓
Composition Root (DI wiring)
```

See [CLAUDE.md](../CLAUDE.md) for detailed directory structure.

## API

All routes under `/api/v1/`. Authentication: `X-API-Key` header (required on every request). Missing or invalid key returns `401`.

### Agent runs

| Method | Route | Status | Description |
|--------|-------|--------|-------------|
| `POST` | `/api/v1/agents/run` | 202 | Start an agent run. Returns `run_id` immediately; processing is async. |
| `GET` | `/api/v1/agents/{run_id}` | 200 | Run status, cost, and token counts. |
| `POST` | `/api/v1/agents/{run_id}/stop` | 204 | Kill switch — sets a Redis cancellation flag; agent stops at the next iteration. |
| `GET` | `/api/v1/agents` | 200 | List runs, cursor-based pagination (`?cursor=<uuid>&limit=20`). |
| `WS` | `/api/v1/agents/{run_id}/stream` | — | Real-time event stream over WebSocket. |

### Tools & eval

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/v1/tools` | List available tools and their descriptions. |
| `POST` | `/api/v1/eval/run` | Start an adversarial eval suite against the agent. |

### Infrastructure

| Route | Description |
|-------|-------------|
| `GET /health` | Liveness probe — `{"status":"ok"}` |
| `GET /ready` | Readiness probe — checks DB + Redis connectivity |
| `GET /docs` | Interactive OpenAPI docs (Swagger UI) |
| `GET /metrics` | Prometheus metrics |

### POST /api/v1/agents/run — request body

```json
{
  "goal": "Search for the latest news about LangGraph and summarize the top 3 results",
  "model": "openai/gpt-4o-mini",
  "max_iterations": 10,
  "max_tokens": 4000,
  "budget_usd": 0.10,
  "tools": ["web_search", "http_caller", "memory_read", "memory_write"]
}
```

| Field | Required | Default | Constraints |
|-------|----------|---------|-------------|
| `goal` | yes | — | 1–2000 chars |
| `model` | no | `OPENROUTER_DEFAULT_MODEL` | Any valid OpenRouter model ID |
| `max_iterations` | no | `DEFAULT_MAX_ITERATIONS` | 1–50 |
| `max_tokens` | no | `DEFAULT_MAX_TOKENS` | 100–32000 |
| `budget_usd` | no | `DEFAULT_BUDGET_USD` | 0.001–10.0 |
| `tools` | no | all 4 tools | Whitelist of allowed tool names |

### GET /api/v1/agents/{run_id} — response

```json
{
  "run_id": "d6be4ecb-9814-4851-a9b1-066e3c288418",
  "status": "completed",
  "goal": "Search for the latest news...",
  "model": "openai/gpt-4o-mini",
  "iteration_count": 3,
  "input_tokens": 1240,
  "output_tokens": 387,
  "cost_usd": 0.000248,
  "error": null
}
```

Status values: `pending` → `running` → `completed` | `failed` | `killed`

### WebSocket stream events

```
{ "type": "subscribed",    "run_id": "..." }
{ "type": "planner_start", "goal": "..." }
{ "type": "plan_ready",    "tasks": 3 }
{ "type": "tool_call",     "tool": "web_search", "task": "..." }
{ "type": "tool_result",   "tool": "web_search", "success": true }
{ "type": "synthesizing" }
{ "type": "completed",     "answer": "..." }
```

---

## LangGraph graph

```
START → planner → executor → validator
                     ↑            │
                     └── loop ────┘  (while tasks remain)
                                  │
                                 END  (completed | failed | killed)
```

The planner decomposes the goal into a list of `{task, tool, tool_input}` objects in a single LLM call. The executor runs them one at a time. The validator synthesizes the final answer once all tasks are done.

---

## Available tools

| Name | Description | Key inputs |
|------|-------------|------------|
| `web_search` | DuckDuckGo text search, up to 5 results | `query: str`, `max_results: int` |
| `http_caller` | Arbitrary GET/POST. Blocked: localhost, 169.254.169.254, *.internal | `url`, `method`, `headers`, `body` |
| `memory_read` | Read from Redis key `agent:memory:{key}` | `key: str` |
| `memory_write` | Write to Redis with TTL (default 24h) | `key`, `value`, `ttl` |

---

## Guardrails

| Guardrail | Trigger | Effect |
|-----------|---------|--------|
| Budget | `cost_usd > budget_usd` | Run fails with `BudgetExceededError` |
| Iterations | `iteration_count >= max_iterations` | Run fails with `MaxIterationsError` |
| Scope | URL targets blocked hosts | `ScopeViolationError` — tool call aborted |
| Audit | Every tool call | Logged in `actions` table (immutable) |
| Kill switch | `POST /stop` called | Redis flag checked every iteration |
| LLM retry | 429 or 5xx from OpenRouter | `tenacity` retries up to 3× with exponential backoff |

---

## Setup (local, no Docker)

```bash
cd agentcore

# Python 3.12 required
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Environment (copy from root)
cp ../.env.example ../.env
# Fill: OPENROUTER_API_KEY, DATABASE_URL (asyncpg), REDIS_URL, AGENTCORE_API_KEY

# Run migrations
alembic upgrade head

# Start API server
uvicorn agentcore.main:app --reload --port 8000

# Start background worker (second terminal)
arq agentcore.worker.WorkerSettings
```

---

## Tests

```bash
pytest                                          # all 83 tests
pytest tests/unit/                              # unit tests only (no network)
pytest tests/integration/                       # integration (needs running DB + Redis)
pytest --cov=agentcore --cov-report=html        # coverage report in htmlcov/
pytest -k "guardrail" -v                        # filter by name
```

Coverage is enforced at 80% minimum in CI.

Test layout mirrors hexagonal layers:
```
tests/
├── conftest.py            fixtures — mocked ARQ, mocked DB session, TestClient
├── unit/
│   ├── domain/            domain service tests
│   │   ├── test_budget_policy.py
│   │   ├── test_iteration_policy.py
│   │   ├── test_url_scope_policy.py
│   │   ├── test_graph_transition_policy.py
│   │   ├── test_plan_parser.py
│   │   ├── test_result_summarizer.py
│   │   ├── test_prompts.py
│   │   └── test_audit_service.py
│   ├── adapters/          adapter tests
│   │   ├── test_openrouter_llm_adapter.py
│   │   ├── test_sqlalchemy_run_repository.py
│   │   ├── test_redis_kv_adapter.py
│   │   ├── test_redis_pubsub_adapter.py
│   │   ├── test_httpx_client_adapter.py
│   │   ├── test_tool_registry.py
│   │   ├── test_web_search_tool_adapter.py
│   │   ├── test_http_caller_tool_adapter.py
│   │   ├── test_memory_tool_adapters.py
│   │   ├── test_ddgs_web_search_adapter.py
│   │   └── test_graph_factory.py
│   ├── application/       application service tests
│   │   ├── test_agent_orchestrator.py
│   │   ├── test_agent_run_service.py
│   │   ├── test_run_stream_service.py
│   │   └── test_tool_execution_service.py
│   ├── test_eval.py       adversarial prompts, reliability scoring
│   ├── test_eval_suite.py
│   └── test_worker.py     ARQ job function
└── integration/
    └── test_api_health.py /health + /ready endpoints
```
