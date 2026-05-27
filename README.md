# Portfolio Agentic

Two integrated projects demonstrating full-stack agentic AI development.

## Projects

| Project | Stack | Port | Description |
|---------|-------|------|-------------|
| `agentcore/` | Python · FastAPI · LangGraph | 8000 | Multi-agent orchestration — autonomous agents with tools, memory, and guardrails |
| `flowrunner/` | Node.js · React · React Flow | 3001 / 5173 | Intelligent workflow automation with a visual editor and an AI decision node |

**Integration:** FlowRunner's `ai-agent` node calls AgentCore to delegate complex decisions mid-workflow.

## Getting started

```bash
# 1. Clone and copy environment config
cp .env.example .env
# Fill in OPENROUTER_API_KEY, AGENTCORE_API_KEY, FLOWRUNNER_API_KEY

# 2. Install local dev dependencies
make install

# 3. Start all services
make up

# 4. Run database migrations
make migrate

# 5. Open
# AgentCore API docs → http://localhost:8000/docs
# FlowRunner API    → http://localhost:3001/documentation
# React editor      → http://localhost:5173
```

## Development

```bash
make dev-ac      # AgentCore with hot-reload (no Docker)
make dev-fr      # FlowRunner server with hot-reload
make dev-client  # React dev server
```

## Testing

```bash
make test        # All tests
make test-ac     # AgentCore only (pytest)
make test-fr     # FlowRunner only (Vitest)
```

## Architecture

```
agentcore/
├── agentcore/
│   ├── api/         REST + WebSocket routes
│   ├── agents/      LangGraph nodes (planner, executor, validator, guard)
│   ├── tools/       Agent tools (web_search, http_caller, memory r/w)
│   ├── guardrails/  Budget, iteration limits, scope blacklist, audit log
│   ├── memory/      Redis + PostgreSQL persistence
│   └── eval/        Adversarial test suite + reliability scoring
└── tests/

flowrunner/
├── server/
│   └── src/
│       ├── routes/  REST API
│       ├── engine/  Sequential node executor
│       └── nodes/   http, condition, transform, delay, ai-agent
└── client/
    └── src/
        └── pages/   Editor, Runs, Monitor
```
