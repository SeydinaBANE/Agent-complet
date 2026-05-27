# FlowRunner

Intelligent workflow automation — visual node editor, sequential execution engine, and an AI decision node powered by AgentCore.

## Stack
Node.js 20 · TypeScript · Fastify · PostgreSQL · BullMQ · React 18 · React Flow · Vite · Tailwind

## API

All routes under `/api/v1/`. Auth: `x-api-key` header.

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/v1/workflows` | List workflows (cursor pagination) |
| `POST` | `/api/v1/workflows` | Create workflow |
| `PUT` | `/api/v1/workflows/:id` | Update workflow |
| `DELETE` | `/api/v1/workflows/:id` | Delete workflow |
| `POST` | `/api/v1/workflows/:id/trigger` | Trigger a run (async, returns `run_id`) |
| `GET` | `/api/v1/runs` | List runs with optional `?status=` filter |
| `GET` | `/api/v1/runs/:id` | Get run detail |
| `GET` | `/api/v1/runs/:id/logs` | Step-by-step logs |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness |
| `GET` | `/documentation` | Swagger UI |

## Node types

| Type | Description |
|------|-------------|
| `http` | GET/POST to an external URL |
| `condition` | if/else on a context field |
| `transform` | Template-based context mapping |
| `delay` | Pause (max 30s) |
| `ai-agent` | Delegates goal to AgentCore, polls until done |

## Setup (local, no Docker)

```bash
# Node 20 required
cd server && npm install
cp ../../.env.example ../../.env  # fill FLOWRUNNER_DATABASE_URL, FLOWRUNNER_API_KEY, AGENTCORE_API_KEY
npm run db:migrate
npm run dev          # server on :3001

cd ../client && npm install
npm run dev          # React on :5173
```

## Integration with AgentCore

The `ai-agent` node sends:
```json
POST http://agentcore:8000/api/v1/agents/run
{
  "goal": "Analyse: {{context.text}}",
  "max_iterations": 3,
  "allowed_tools": ["web_search"]
}
```
Template placeholders (`{{context.key}}`) are resolved against the current workflow context before the request. The node polls `GET /api/v1/agents/{run_id}` every 2s until `status === "completed"`, then injects `{ node-id_run_id, node-id_status }` into the workflow context for downstream nodes.

**Node data fields:**
| Field | Default | Description |
|-------|---------|-------------|
| `goal` | required | Goal string, supports `{{key}}` interpolation |
| `max_iterations` | `5` | Max agent iterations |
| `budget_usd` | `0.05` | Cost cap per run |
| `allowed_tools` | all | Whitelist of tools the agent may use |
| `model` | server default | OpenRouter model override |

## Tests

```bash
cd server
npm test                  # 18 tests (engine, nodes, queue worker)
npm run typecheck         # TypeScript strict check
npm run lint              # ESLint
```
