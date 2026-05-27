# FlowRunner

Intelligent workflow automation — visual node editor, sequential execution engine, and an AI decision node powered by AgentCore.

## Stack

Node.js 20 · TypeScript (strict) · Fastify · PostgreSQL · BullMQ · React 18 · React Flow · Vite · Tailwind

---

## API

All routes under `/api/v1/`. Authentication: `x-api-key` header (required on every request).

### Workflows

| Method | Route | Status | Description |
|--------|-------|--------|-------------|
| `GET` | `/api/v1/workflows` | 200 | List workflows (cursor pagination: `?cursor=<uuid>&limit=20`) |
| `POST` | `/api/v1/workflows` | 201 | Create a workflow |
| `PUT` | `/api/v1/workflows/:id` | 200 | Update name or graph |
| `DELETE` | `/api/v1/workflows/:id` | 204 | Delete workflow and cascade runs |
| `POST` | `/api/v1/workflows/:id/trigger` | 202 | Trigger a run. Returns `run_id` immediately. |

### Runs

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/v1/runs` | List runs (`?status=running&cursor=...&limit=20`) |
| `GET` | `/api/v1/runs/:id` | Run detail (status, timing, context) |
| `GET` | `/api/v1/runs/:id/logs` | Step-by-step logs with input/output/duration |

### Infrastructure

| Route | Description |
|-------|-------------|
| `GET /health` | Liveness — `{"status":"ok"}` |
| `GET /ready` | Readiness — checks DB + Redis |
| `GET /documentation` | Swagger UI |

### POST /api/v1/workflows — request body

```json
{
  "name": "My workflow",
  "graph": {
    "nodes": [
      {
        "id": "node-1",
        "type": "http",
        "position": { "x": 100, "y": 100 },
        "data": {
          "label": "Fetch data",
          "url": "https://api.example.com/data",
          "method": "GET"
        }
      },
      {
        "id": "node-2",
        "type": "ai-agent",
        "position": { "x": 400, "y": 100 },
        "data": {
          "label": "Analyse",
          "goal": "Summarise this JSON: {{node-1_body}}",
          "max_iterations": 3
        }
      }
    ],
    "edges": [
      { "id": "e1-2", "source": "node-1", "target": "node-2" }
    ]
  }
}
```

### POST /api/v1/workflows/:id/trigger — response

```json
{ "run_id": "789aa62f-5f7b-47c9-add1-159502cd60b8", "status": "pending" }
```

Poll `GET /api/v1/runs/:id` until `status === "completed"` or `"failed"`.

### GET /api/v1/runs/:id/logs — response

```json
{
  "run_id": "789aa62f-...",
  "steps": [
    {
      "id": "6c0a8c05-...",
      "node_id": "node-1",
      "node_type": "http",
      "input": { "context": {} },
      "output": { "node-1_status": 200, "node-1_body": "..." },
      "error": null,
      "duration_ms": 312,
      "created_at": "2026-05-27T21:12:19.971Z"
    }
  ]
}
```

---

## Node types

### `http` — HTTP request

```json
{
  "type": "http",
  "data": {
    "url": "https://api.example.com/items",
    "method": "POST",
    "headers": { "Authorization": "Bearer {{context.token}}" },
    "body": "{\"key\": \"{{context.key}}\"}"
  }
}
```

Injects into context: `{ "[nodeId]_status": 200, "[nodeId]_body": "..." }`

### `condition` — if/else branch

```json
{
  "type": "condition",
  "data": {
    "field": "http-1_status",
    "operator": "eq",
    "value": 200,
    "stop_on_false": true
  }
}
```

Operators: `eq`, `neq`, `gt`, `lt`, `contains`. If `stop_on_false: true` and the condition is false, the run fails immediately.

### `transform` — context mapping

```json
{
  "type": "transform",
  "data": {
    "output": {
      "summary": "Status was {{http-1_status}} and body: {{http-1_body}}"
    }
  }
}
```

Resolves `{{key}}` placeholders from the current context and merges the result into the context.

### `delay` — pause

```json
{
  "type": "delay",
  "data": { "ms": 5000 }
}
```

Maximum: 30 000ms (30s).

### `ai-agent` — AgentCore delegation

```json
{
  "type": "ai-agent",
  "data": {
    "goal": "Analyse this text and give a sentiment score: {{context.text}}",
    "max_iterations": 5,
    "budget_usd": 0.05,
    "allowed_tools": ["web_search", "memory_read"],
    "model": "openai/gpt-4o-mini"
  }
}
```

**Fields:**

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `goal` | yes | — | Goal string. Supports `{{key}}` interpolation from context. |
| `max_iterations` | no | `5` | Max agent iterations |
| `budget_usd` | no | `0.05` | Cost cap per agent run |
| `allowed_tools` | no | all | Whitelist of AgentCore tools |
| `model` | no | server default | OpenRouter model override |

Injects into context: `{ "[nodeId]_run_id": "...", "[nodeId]_status": "completed" }`

The node calls `POST /api/v1/agents/run` on AgentCore, then polls `GET /api/v1/agents/{id}` every 2s until the agent completes (timeout: 120s).

---

## Workflow context

The context is a flat JSON object that flows between nodes. Each node receives the full context and returns the keys it adds or modifies. Downstream nodes can reference any key set by previous nodes.

```
initial context: { "input": "Hello world" }
after http node: { "input": "...", "http-1_status": 200, "http-1_body": "..." }
after transform: { "input": "...", "http-1_status": 200, ..., "summary": "..." }
after ai-agent:  { ..., "agent-1_run_id": "uuid", "agent-1_status": "completed" }
```

---

## Setup (local, no Docker)

```bash
# Server
cd flowrunner/server
npm install

# Environment
cp ../../.env.example ../../.env
# Fill: FLOWRUNNER_DATABASE_URL, FLOWRUNNER_API_KEY, AGENTCORE_API_KEY
# Set: AGENTCORE_ORIGIN=http://localhost:8000 (local dev, not Docker)

# Run migrations
node --import tsx/esm scripts/migrate.ts

# Start server (port 3001, hot-reload)
npm run dev

# Client (separate terminal)
cd ../client
npm install

# Client env
echo "VITE_FLOWRUNNER_API_KEY=your-key" > .env.local
echo "VITE_AGENTCORE_API_KEY=your-agentcore-key" >> .env.local

npm run dev   # http://localhost:5173
```

---

## Tests

```bash
cd flowrunner/server
npm test              # 18 tests (Vitest)
npm run typecheck     # TypeScript strict mode check
npm run lint          # ESLint
```

Test layout:
```
tests/
├── setup.ts                      global Vitest setup
└── unit/
    ├── engine.test.ts            sequential execution, context propagation, error handling
    ├── queue.test.ts             BullMQ worker — run persistence, status updates
    └── nodes/
        ├── http.test.ts          HTTP node (fetch mocked)
        └── condition.test.ts     condition operators, stop_on_false
```

---

## Frontend pages

| Page | Route | Description |
|------|-------|-------------|
| Editor | `/editor` | Drag-and-drop React Flow canvas. Add nodes from the left palette. Click a node to configure it. Save via the API. |
| Runs | `/runs` | Table of all runs with status badge and link to detail. Auto-refreshes if any run is active. |
| Run Detail | `/runs/:id` | Step-by-step timeline. Each step shows node type, duration, expandable input/output, red error highlight. |
| Monitor | `/monitor` | Running workflows only. Refreshes every 2s. |

Client API keys are stored in `flowrunner/client/.env.local` (gitignored) and accessed via `import.meta.env.VITE_*`.
