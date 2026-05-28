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
cd agentcore && pytest tests/unit/test_agents.py -v
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

### AgentCore — LangGraph pipeline

Entry: `agentcore/main.py` → FastAPI app with ARQ pool in `app.state.arq`.
Worker: `agentcore/worker.py` → `WorkerSettings` (max 10 jobs, 300s timeout).

Graph flow (`agentcore/agents/graph.py`): `START → planner → executor → validator → END`

- **planner** (`agents/planner.py`) — calls LLM to decompose `goal` into `list[TaskPlan]`
- **executor** (`agents/executor.py`) — runs tools one by one, checks guardrails, publishes Redis events
- **validator** (`agents/validator.py`) — synthesizes `final_answer`; loops back to executor if tasks remain
- **state** (`agents/state.py`) — `AgentState` TypedDict carries `run_id`, `goal`, `plan`, `results`, `cost_usd`, `iteration_count`, `status`, etc.

Tools (`agentcore/tools/`): `web_search` (DuckDuckGo), `http_caller`, `memory_read`, `memory_write` (Redis TTL 24h). All tools accept `**_kwargs` to absorb unknown LLM-generated params.

Guardrails (`agentcore/guardrails/`): `budget.py` (cost_usd > budget_usd), `iterations.py` (iteration_count >= max_iterations), `scope.py` (blocks localhost/private IPs), `audit.py` (immutable DB log). Kill switch: write `run:cancel:{run_id}` to Redis.

Eval suite (`agentcore/eval/`): `suite.py`, `adversarial.py`, `report.py` — run via `tests/unit/test_eval_suite.py`.

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

Optional with defaults: `OPENROUTER_DEFAULT_MODEL` (gpt-4o-mini), `FLOWRUNNER_ORIGIN` (http://localhost:5173), `DEFAULT_MAX_ITERATIONS` (10), `DEFAULT_BUDGET_USD` (0.10).
