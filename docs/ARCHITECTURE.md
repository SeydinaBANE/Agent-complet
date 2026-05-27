# Architecture technique

## Vue d'ensemble

Deux services indépendants, intégrés via HTTP :

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser  (http://localhost:5173)                               │
│  React 18 + React Flow + Tailwind                               │
│  Editor / Runs / Monitor                                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST (X-API-Key)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FlowRunner Server  (http://localhost:3001)                     │
│  Node.js 20 · Fastify · TypeScript                              │
│  Workflows CRUD + execution engine + BullMQ queue               │
└───────────────────────┬─────────────────────────────────────────┘
                        │ POST /api/v1/agents/run  (X-API-Key)
                        │ GET  /api/v1/agents/{id}  (polling)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  AgentCore  (http://localhost:8000)                             │
│  Python 3.12 · FastAPI · LangGraph                              │
│  Multi-agent orchestration + tools + guardrails + ARQ queue     │
└──────────┬──────────────────────────────────────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
PostgreSQL      Redis
(runs,          (ARQ queue,
 actions,        BullMQ queue,
 workflows,      pub/sub stream,
 run_steps)      agent memory)
```

---

## AgentCore

### LangGraph StateGraph

```
START
  │
  ▼
┌──────────┐
│ planner  │  Reçoit le goal → appelle le LLM (JSON) → décompose en liste de TaskPlan
└──────┬───┘  [{task, tool, tool_input}, ...]
       │
       ▼
┌──────────┐
│ executor │  Prend la prochaine tâche → vérifie guardrails → exécute l'outil
└──────┬───┘  Publie chaque action sur Redis (pub/sub) → WebSocket client
       │
       ▼
┌───────────┐
│ validator │  Toutes tâches faites → synthèse LLM → final_answer
└──────┬────┘  Si tâches restantes → retour executor
       │
    ┌──┴───────────────────────────────────────┐
    │ _should_continue()                        │
    │  - error / status failed/killed → END     │
    │  - status completed → END                 │
    │  - tasks remaining → executor             │
    └──────────────────────────────────────────┘
```

**AgentState** (TypedDict, immuable entre les nœuds) :

| Champ | Type | Rôle |
|-------|------|------|
| `run_id` | str | UUID du run |
| `goal` | str | Objectif passé par l'utilisateur |
| `model` | str | Modèle OpenRouter à utiliser |
| `max_iterations` | int | Limite d'itérations (guardrail) |
| `budget_usd` | float | Plafond de coût (guardrail) |
| `allowed_tools` | list[str] | Whitelist des outils autorisés |
| `plan` | list[TaskPlan] | Tâches planifiées |
| `current_task_index` | int | Position dans le plan |
| `results` | list[TaskResult] | Résultats accumulés |
| `iteration_count` | int | Compteur d'itérations |
| `cost_usd` | float | Coût cumulé (mis à jour après chaque appel LLM) |
| `input_tokens` / `output_tokens` | int | Tokens accumulés |
| `final_answer` | str \| None | Réponse finale (remplie par validator) |
| `status` | str | `running` \| `completed` \| `failed` \| `killed` |

### Outils agents

| Outil | Fichier | Description |
|-------|---------|-------------|
| `web_search` | `tools/web_search.py` | DuckDuckGo, max 5 résultats |
| `http_caller` | `tools/http_caller.py` | GET/POST arbitraire avec headers |
| `memory_read` | `tools/memory_read.py` | Lecture Redis `agent:memory:{key}` |
| `memory_write` | `tools/memory_write.py` | Écriture Redis TTL 24h |

Les outils acceptent `**_kwargs` pour absorber les paramètres inconnus générés par le LLM.

### Guardrails

| Guardrail | Fichier | Déclenchement |
|-----------|---------|---------------|
| Budget | `guardrails/budget.py` | `cost_usd > budget_usd` → `BudgetExceededError` |
| Iterations | `guardrails/iterations.py` | `iteration_count >= max_iterations` → `MaxIterationsError` |
| Scope | `guardrails/scope.py` | URL vers `localhost`, `169.254.169.254`, `*.internal` → `ScopeViolationError` |
| Audit | `guardrails/audit.py` | Log immuable de chaque action dans la table `actions` |
| Kill switch | API `POST /stop` | Écrit `run:cancel:{run_id}` dans Redis ; executor vérifie à chaque itération |

### File ARQ (background jobs)

```
POST /api/v1/agents/run
  → crée Run (status=pending) en DB
  → enqueue_job("run_agent_job", run_id=..., goal=..., ...)
  → retourne immédiatement { run_id, status: "pending" }

ARQ Worker (process séparé)
  → dépile le job
  → update Run (status=running)
  → graph.ainvoke(initial_state)
  → update Run (status=completed|failed, cost_usd, tokens...)
```

### Schéma PostgreSQL (AgentCore)

```sql
CREATE TABLE runs (
  id UUID PRIMARY KEY,
  goal TEXT NOT NULL,
  model VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL,       -- pending | running | completed | failed | killed
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  iteration_count INT DEFAULT 0,
  input_tokens INT DEFAULT 0,
  output_tokens INT DEFAULT 0,
  cost_usd DECIMAL(10,6) DEFAULT 0,
  error TEXT
);

CREATE TABLE actions (
  id UUID PRIMARY KEY,
  run_id UUID REFERENCES runs(id),
  agent VARCHAR(50) NOT NULL,        -- planner | executor | validator
  tool VARCHAR(50),
  input JSONB DEFAULT '{}',
  output JSONB,
  created_at TIMESTAMPTZ
);
```

### Streaming WebSocket

```
Client → WS /api/v1/agents/{run_id}/stream
AgentCore → subscribe Redis channel "run:{run_id}"

Graph publie des événements à chaque étape :
  { type: "planner_start",  goal: "..." }
  { type: "plan_ready",     tasks: 3 }
  { type: "tool_call",      tool: "web_search", task: "..." }
  { type: "tool_result",    tool: "web_search", success: true }
  { type: "synthesizing" }
  { type: "completed",      answer: "..." }
```

---

## FlowRunner

### Moteur d'exécution

```
POST /api/v1/workflows/:id/trigger
  → crée Run (status=pending) en DB
  → enqueue BullMQ job { workflowId, runId, context }
  → retourne { run_id, status: "pending" }

BullMQ Worker
  → charge le workflow (graph JSONB depuis DB)
  → runWorkflow(nodes, initialContext, runId)
      pour chaque nœud :
        input = contexte courant
        output = await executeNode(node, context, runId)
        context = { ...context, ...output }    ← propagation
        persiste le step (input, output, durée, erreur)
  → update Run (status=completed|failed)
```

Le contexte est un objet JSON plat qui s'enrichit à chaque nœud. Chaque nœud reçoit le contexte complet et retourne les clés qu'il ajoute ou modifie.

### Types de nœuds

| Type | Fichier | Comportement |
|------|---------|-------------|
| `http` | `nodes/http.ts` | `fetch(url, {method, headers, body})` → injecte `{[nodeId]_status, [nodeId]_body}` |
| `condition` | `nodes/condition.ts` | Évalue `context[field] operator value` ; lève une erreur si `false` et `stop_on_false: true` |
| `transform` | `nodes/transform.ts` | Template `{{key}}` → interpolation depuis le contexte |
| `delay` | `nodes/delay.ts` | `setTimeout(ms)`, max 30 000ms |
| `ai-agent` | `nodes/ai-agent.ts` | `POST agentcore/run` → poll `GET /agents/{id}` toutes les 2s → injecte `{[nodeId]_run_id, [nodeId]_status}` |

### Schéma PostgreSQL (FlowRunner)

```sql
CREATE TABLE workflows (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  graph JSONB NOT NULL,    -- { nodes: [...], edges: [...] } — format React Flow
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ
);

CREATE TABLE runs (
  id UUID PRIMARY KEY,
  workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
  status VARCHAR(20),      -- pending | running | completed | failed
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  context JSONB DEFAULT '{}',
  error TEXT,
  created_at TIMESTAMPTZ
);

CREATE TABLE run_steps (
  id UUID PRIMARY KEY,
  run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
  node_id VARCHAR(100),
  node_type VARCHAR(50),
  input JSONB,
  output JSONB,
  error TEXT,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_runs_workflow_id ON runs(workflow_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX idx_run_steps_run_id ON run_steps(run_id);
```

### Frontend React

| Page | Route | Données |
|------|-------|---------|
| Editor | `/editor` | React Flow canvas + palette de nœuds + config par nœud. Sauvegarde via `PUT /api/v1/workflows/:id`. |
| Runs | `/runs` | Tableau paginé. Polling 5s si des runs sont `running`. |
| Run Detail | `/runs/:id` | Timeline step-by-step. Polling 2s si `running`. Input/output expandable. Erreur en rouge. |
| Monitor | `/monitor` | Runs `running` uniquement. Polling 2s. |

---

## Sécurité

| Mécanisme | Implémentation |
|-----------|----------------|
| Authentification | Header `X-API-Key` sur tous les endpoints. Comparaison avec `hmac.compare_digest` (Python) / comparaison directe (Node.js) |
| CORS | AgentCore accepte uniquement `FLOWRUNNER_ORIGIN`. FlowRunner : `@fastify/cors` configuré. |
| Rate limiting | `slowapi` (Python) sur AgentCore. `@fastify/rate-limit` (Node.js) sur FlowRunner. |
| Validation inputs | Pydantic v2 (Python) + Zod-like via Fastify schemas (TypeScript). |
| Secrets | Jamais dans le code. Lus depuis `.env` au démarrage. L'app refuse de démarrer si une variable manque. |
| Scope blocklist | L'outil `http_caller` ne peut pas appeler `localhost`, les IPs privées, ni les endpoints cloud metadata. |

---

## Observabilité

| Signal | Outil | Endpoint |
|--------|-------|---------|
| Logs structurés | `structlog` (Python) / `pino` (Node.js) | stdout JSON |
| Métriques Prometheus | `prometheus-fastapi-instrumentator` | `GET /metrics` |
| Tracing LLM | Chaque appel OpenRouter loggue `input_tokens`, `output_tokens`, `cost_usd` | DB + logs |
| Streaming temps réel | Redis pub/sub → WebSocket | `WS /api/v1/agents/{run_id}/stream` |
