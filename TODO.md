# TODO

## Phase 1 — Fondations
- [x] Scaffolding monorepo (dossiers, .gitignore, docker-compose.yml)
- [x] .env.example avec toutes les variables
- [x] CLAUDE.md, Makefile, .pre-commit-config.yaml
- [x] GitHub Actions CI
- [ ] scripts/init-db.sql testé avec `docker compose up postgres`
- [ ] AgentCore : FastAPI skeleton + `/health` + `/ready`
- [ ] AgentCore : config pydantic-settings + validation au démarrage
- [ ] FlowRunner server : Fastify skeleton + `/health`

## Phase 2 — AgentCore core
- [ ] Migrations Alembic (tables `runs`, `actions`)
- [ ] ARQ job queue — background runs
- [ ] LangGraph graph (planner → executor → validator)
- [ ] Outils : `web_search`, `http_caller`, `memory_read`, `memory_write`
- [ ] Guardrails : budget tokens, max iterations, scope blacklist, audit log
- [ ] WebSocket stream `/api/v1/agents/{run_id}/stream`
- [ ] Retry/backoff `tenacity` sur appels OpenRouter
- [ ] Tracking coût (`input_tokens`, `output_tokens`, `cost_usd` dans table `runs`)
- [ ] Kill switch `POST /api/v1/agents/{run_id}/stop`
- [ ] Prometheus metrics sur `/metrics`

## Phase 3 — FlowRunner server
- [ ] Migrations db-migrate (tables `workflows`, `runs`, `run_steps`)
- [ ] BullMQ job queue
- [ ] Engine : exécution séquentielle des nœuds avec context propagation
- [ ] Nœud `http` — GET/POST vers URL externe
- [ ] Nœud `condition` — if/else sur valeur JSON
- [ ] Nœud `transform` — JSONPath/template
- [ ] Nœud `delay` — pause configurable
- [ ] Nœud `ai-agent` — appelle AgentCore
- [ ] Pagination cursor-based sur `GET /api/v1/runs`
- [ ] Retry automatique sur nœuds en échec (configurable par nœud)

## Phase 4 — FlowRunner client React
- [ ] Setup Vite + React 18 + Tailwind + React Flow
- [ ] Page `/editor` — canvas + palette nœuds + panneau config
- [ ] Page `/runs` — tableau avec filtres statut/workflow + badge coloré
- [ ] Page `/runs/:id` — timeline step-by-step (input/output/durée par nœud)
- [ ] Page `/monitor` — runs en cours, polling 2s, statut temps réel

## Phase 5 — Qualité & finition
- [ ] AgentCore : module `eval/` (tests adversariaux + rapport HTML)
- [ ] Tests unitaires AgentCore — couverture 80%+ (guardrails, tools)
- [ ] Tests intégration AgentCore — endpoints + BDD réelle
- [ ] Tests FlowRunner server — engine nœuds + endpoints
- [ ] Tests FlowRunner client — composants clés (Vitest + Testing Library)
- [ ] README.md racine (getting started en 5 commandes)
- [ ] README.md agentcore/ + README.md flowrunner/
- [ ] OpenAPI docs : `/docs` (FastAPI) + `/documentation` (Fastify Swagger)
- [ ] `docker compose build` testé en CI
