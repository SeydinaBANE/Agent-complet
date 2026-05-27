# projet-1 — Portfolio Agentic

## Projets
- `agentcore/` — Python 3.12 / FastAPI / LangGraph. API sur port **8000**.
- `flowrunner/server/` — Node.js 20 / TypeScript / Fastify. API sur port **3001**.
- `flowrunner/client/` — React 18 / Vite / Tailwind. Dev server sur port **5173**.

## Commandes rapides
```bash
make up          # Lancer tous les services (Docker)
make migrate     # Appliquer les migrations BDD
make test        # Tous les tests
make test-ac     # Tests AgentCore uniquement
make test-fr     # Tests FlowRunner uniquement
make lint        # Lint des deux projets
make typecheck   # Vérification types
make dev-ac      # AgentCore en mode hot-reload (sans Docker)
make dev-fr      # FlowRunner server en mode hot-reload
make dev-client  # React dev server
```

## Conventions
- Commits : `feat(scope):`, `fix(scope):`, `test(scope):`, `refactor(scope):`, `docs(scope):`
  - Exemples : `feat(agentcore): add web_search tool`, `fix(flowrunner): handle timeout in http node`
- **Jamais commiter `.env`** — utiliser `.env.example`
- Toujours écrire des tests pour les nouveaux agents et nœuds
- Modèle OpenRouter par défaut : `openai/gpt-4o-mini` (économique)
- Tous les endpoints sous `/api/v1/`

## Variables d'environnement
Copier `.env.example` → `.env` et remplir les valeurs. L'app refuse de démarrer si
`OPENROUTER_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `AGENTCORE_API_KEY` sont manquantes.

## Architecture clé
- AgentCore utilise **ARQ** (Redis queue) pour les runs en arrière-plan
- FlowRunner utilise **BullMQ** (Redis queue) pour les workflow runs
- Le nœud `ai-agent` de FlowRunner appelle AgentCore via `POST /api/v1/agents/run`
- Tous les logs sont en JSON structuré (`structlog` / `pino`) — jamais de `print()`
- Migrations versionnées : Alembic (Python) / db-migrate (Node.js)
