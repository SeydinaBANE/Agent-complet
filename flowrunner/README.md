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

## Tests

```bash
cd server
npm test                  # all tests
npm run typecheck         # TypeScript check
npm run lint              # ESLint
```
