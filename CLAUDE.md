# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Services

| Service | Stack | Port |
|---------|-------|------|
| `agentcore/` | Python 3.12 / FastAPI / LangGraph / ARQ | 8000 |
| `flowrunner/server/` | Node.js 20 / TypeScript / Fastify / BullMQ | 3001 |
| `flowrunner/client/` | React 18 / Vite / Tailwind / React Flow | 5173 |

## Commands

```bash
# Docker (all services)
make up          # Start (detached)
make down        # Stop
make logs        # Stream logs
make build       # Rebuild images
make clean       # Remove containers + volumes + caches

# Database
make migrate     # Alembic (Python) + db-migrate (Node.js)

# Tests
make test        # All tests with coverage
make test-ac     # AgentCore only: cd agentcore && pytest -v
make test-fr     # FlowRunner only: cd flowrunner/server && npm test (vitest)

# Single test
cd agentcore && pytest tests/unit/domain/test_budget_policy.py -v
cd agentcore && pytest -m "not slow"         # skip slow tests
cd flowrunner/server && npx vitest run tests/unit/nodes/http.test.ts

# Lint / Types
make lint        # ruff (Python) + eslint (Node.js)
make typecheck   # mypy strict (Python) + tsc --noEmit (Node.js)

# Dev (hot-reload, no Docker)
make dev-ac      # uvicorn agentcore.main:app --reload --port 8000
make dev-fr      # tsx watch src/index.ts
make dev-client  # vite dev server

# Install deps
make install     # pip install -r requirements-dev.txt + npm install x2 + pre-commit
```

## Architecture

Two independent services connected via HTTP. FlowRunner orchestrates workflows; AgentCore executes AI agents.

```
Browser (5173)  →  FlowRunner Server (3001)  →  AgentCore (8000)
                                    ↓                   ↓
                                 PostgreSQL           Redis
                                 BullMQ queue         ARQ queue + pub/sub + memory
```

### AgentCore — LangGraph pipeline (Hexagonal Architecture)

Entry: `agentcore/main.py` → FastAPI app with ARQ pool in `app.state.arq`.
Worker: `agentcore/worker.py` → `WorkerSettings` (max 10 jobs, 300s timeout).

Graph flow (`agentcore/adapters/langgraph/graph_factory.py`): `START → planner → executor → validator → END`

#### Hexagonal Layers

**Ports** (`agentcore/ports/`) — Interfaces (Protocol classes):
- `llm_port.py` — LLM interaction (`chat`, `chat_json`)
- `tool_port.py` — Tool execution (`name`, `run`)
- `tool_registry_port.py` — Tool lookup (`get`, `list_tools`)
- `run_repository_port.py` — Run persistence (`create`, `mark_running`, `mark_finished`, `get_by_id`, `list`)
- `kv_store_port.py` — Key-value storage (`get`, `set`)
- `http_client_port.py` — HTTP requests (`request`)
- `pubsub_port.py` — Pub/sub messaging (`publish`, `subscribe`)
- `queue_port.py` — Job queue (`enqueue_agent_job`)
- `web_search_port.py` — Web search (`search`)
- `audit_port.py` — Audit logging (`log_action`)

**Adapters** (`agentcore/adapters/`) — Concrete implementations:
- `llm/openrouter_llm_adapter.py` — OpenAI SDK via OpenRouter
- `db/sqlalchemy_run_repository.py` — SQLAlchemy async persistence
- `db/sqlalchemy_audit_adapter.py` — Audit logging to database
- `redis/redis_kv_adapter.py` — Redis key-value store (24h TTL)
- `redis/redis_pubsub_adapter.py` — Redis pub/sub
- `http/httpx_client_adapter.py` — HTTP client
- `queue/arq_queue_adapter.py` — ARQ job queue
- `tools/web_search_tool_adapter.py` — DuckDuckGo search
- `tools/http_caller_tool_adapter.py` — HTTP caller
- `tools/memory_read_tool_adapter.py` — Memory read
- `tools/memory_write_tool_adapter.py` — Memory write
- `tools/ddgs_web_search_adapter.py` — DuckDuckGo search port
- `tools/tool_registry.py` — Tool registry
- `langgraph/graph_factory.py` — LangGraph graph builder

**Domain** (`agentcore/domain/`) — Business logic:
- `entities.py` — `TaskPlan`, `TaskResult`, `AgentState`, `RunRecord`
- `errors.py` — Domain exceptions (`BudgetExceededError`, `MaxIterationsError`, etc.)
- `prompts.py` — LLM prompt templates
- `services/budget_policy.py` — Cost computation and budget checking
- `services/iteration_policy.py` — Iteration limit checking
- `services/url_scope_policy.py` — URL scope validation
- `services/graph_transition_policy.py` — Graph routing decisions
- `services/plan_parser.py` — LLM response parsing
- `services/result_summarizer.py` — Task result formatting
- `services/audit_service.py` — Audit logging service

**Application** (`agentcore/application/`) — Use cases:
- `dto.py` — `AgentDefaults` configuration DTO
- `services/agent_orchestrator.py` — Core orchestrator (plan, execute, finalize)
- `services/agent_run_service.py` — Run management (start, list, get)
- `services/run_stream_service.py` — Event streaming
- `services/tool_execution_service.py` — Tool execution

**Composition Root**:
- `api/deps.py` — FastAPI dependency injection
- `worker.py` — Background job composition

#### Guardrails

- `budget.py` (cost_usd > budget_usd)
- `iterations.py` (iteration_count >= max_iterations)
- `scope.py` (blocks localhost/private IPs)
- `audit.py` (audit logging via AuditService)

Kill switch: write `run:cancel:{run_id}` to Redis via KvStorePort.

#### Tests

Tests mirror hexagonal layers:
- `tests/unit/domain/` — Domain service tests
- `tests/unit/adapters/` — Adapter tests
- `tests/unit/application/` — Application service tests
- `tests/unit/test_eval_suite.py` — Eval suite tests

### FlowRunner — workflow engine

Entry: `flowrunner/server/src/index.ts`.
Engine: `src/engine/runner.ts` (workflow runner) + `src/engine/node-executor.ts` (per-node dispatch).
Queue: `src/queue.ts` — BullMQ worker.

Node types (`src/nodes/`): `http.ts`, `condition.ts`, `transform.ts` (template `{{key}}`), `delay.ts` (max 30s), `ai-agent.ts` (polls AgentCore every 2s).

Context propagation: flat JSON object passed through each node; each node receives full context and returns new/modified keys.

Routes (`src/routes/`): `workflows.ts` (CRUD + trigger), `runs.ts` (list + detail + steps), `health.ts`.

### Frontend

Pages in `flowrunner/client/src/pages/`: Editor (`/editor` — React Flow canvas), Runs (`/runs` — polling 5s), Run Detail (`/runs/:id` — polling 2s), Monitor (`/monitor` — running only, polling 2s).

## Conventions

- **All endpoints** prefixed `/api/v1/`
- **Auth**: `X-API-Key` header on all endpoints
- **Logs**: JSON structured only — `structlog` (Python) / `pino` (Node.js). Never `print()`.
- **Default model**: `openai/gpt-4o-mini` (OpenRouter)
- **Commit scopes**: `feat(agentcore):`, `fix(flowrunner):`, `test(agentcore):`, etc.

## Environment variables

Required at startup (app refuses to start if missing): `OPENROUTER_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `AGENTCORE_API_KEY`.

`DATABASE_URL` must use the `postgresql+asyncpg://` driver (not plain `postgresql://`) — AgentCore uses SQLAlchemy async engine which requires it. The CI and `.env.example` already use the correct prefix.

Optional with defaults: `OPENROUTER_DEFAULT_MODEL` (gpt-4o-mini), `FLOWRUNNER_ORIGIN` (http://localhost:5173), `DEFAULT_MAX_ITERATIONS` (10), `DEFAULT_BUDGET_USD` (0.10).
