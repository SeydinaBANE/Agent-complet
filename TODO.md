# TODO

## Phase 1 — Fondations ✓
- [x] Scaffolding monorepo (dossiers, .gitignore, docker-compose.yml)
- [x] .env.example avec toutes les variables
- [x] CLAUDE.md, Makefile, .pre-commit-config.yaml
- [x] GitHub Actions CI
- [x] scripts/init-db.sql
- [x] AgentCore : FastAPI skeleton + `/health` + `/ready`
- [x] AgentCore : config pydantic-settings + validation au démarrage
- [x] FlowRunner server : Fastify skeleton + `/health`

## Phase 2 — AgentCore core ✓
- [x] Migrations Alembic (tables `runs`, `actions`)
- [x] ARQ job queue — background runs
- [x] LangGraph graph (planner → executor → validator)
- [x] Outils : `web_search`, `http_caller`, `memory_read`, `memory_write`
- [x] Guardrails : budget tokens, max iterations, scope blacklist, audit log
- [x] WebSocket stream `/api/v1/agents/{run_id}/stream`
- [x] Retry/backoff `tenacity` sur appels OpenRouter
- [x] Tracking coût (`input_tokens`, `output_tokens`, `cost_usd` dans table `runs`)
- [x] Kill switch `POST /api/v1/agents/{run_id}/stop`
- [x] Prometheus metrics sur `/metrics`

## Phase 3 — FlowRunner server ✓
- [x] Migrations SQL (tables `workflows`, `runs`, `run_steps`)
- [x] BullMQ job queue + worker
- [x] Engine : exécution séquentielle des nœuds avec context propagation
- [x] Nœud `http` — GET/POST vers URL externe
- [x] Nœud `condition` — if/else sur valeur JSON
- [x] Nœud `transform` — template interpolation
- [x] Nœud `delay` — pause configurable (max 30s)
- [x] Nœud `ai-agent` — appelle AgentCore, poll jusqu'à completion
- [x] Pagination cursor-based sur `GET /api/v1/runs` et `GET /api/v1/workflows`

## Phase 4 — FlowRunner client React ✓
- [x] Setup Vite + React 18 + Tailwind + React Flow
- [x] Page `/editor` — canvas + palette nœuds + panneau config
- [x] Page `/runs` — tableau avec badge statut + lien vers détail
- [x] Page `/runs/:id` — timeline step-by-step (input/output/durée, highlight erreur)
- [x] Page `/monitor` — runs en cours, polling 2s, statut temps réel

## Phase 5 — Qualité & finition
- [x] AgentCore : module `eval/` (tests adversariaux + rapport HTML)
- [x] Tests unitaires AgentCore — couverture 90% (64 tests)
- [ ] Tests intégration AgentCore — endpoints + BDD réelle (Docker testcontainers)
- [x] Tests FlowRunner server — engine nœuds + queue (18 tests)
- [ ] Tests FlowRunner client — composants clés (Vitest + Testing Library)
- [x] README.md racine (getting started en 5 commandes)
- [ ] README.md agentcore/ + README.md flowrunner/
- [x] OpenAPI docs : `/docs` (FastAPI) + `/documentation` (Fastify Swagger)
- [ ] `docker compose build` testé end-to-end
