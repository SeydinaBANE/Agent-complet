# Guide de déploiement

## Prérequis

| Outil | Version minimale | Vérification |
|-------|-----------------|--------------|
| Docker | 24+ | `docker --version` |
| Docker Compose | 2.20+ (plugin V2) | `docker compose version` |
| Git | 2.x | `git --version` |

Pour le développement local sans Docker :

| Outil | Version |
|-------|---------|
| Python | 3.12+ |
| Node.js | 20+ |
| pip | récent |
| npm | 9+ |

---

## Déploiement Docker Compose (recommandé)

### 1. Cloner et configurer l'environnement

```bash
git clone <repo-url> projet-1
cd projet-1

# Copier le template d'environnement
cp .env.example .env
```

Ouvrir `.env` et remplir les valeurs obligatoires :

```bash
# Obtenir une clé sur https://openrouter.ai → API Keys
OPENROUTER_API_KEY=sk-or-v1-...

# Générer deux clés aléatoires (une par service)
openssl rand -hex 32   # → AGENTCORE_API_KEY
openssl rand -hex 32   # → FLOWRUNNER_API_KEY
```

### 2. Lancer tous les services

```bash
docker compose up -d
```

Cette commande démarre 5 conteneurs dans l'ordre :

| Conteneur | Port | Attend |
|-----------|------|--------|
| `postgres` | 5432 | — |
| `redis` | 6379 | — |
| `agentcore` | 8000 | postgres healthy + redis healthy |
| `agentcore-worker` | — | postgres healthy + redis healthy |
| `flowrunner` | 3001 | postgres healthy + redis healthy + agentcore healthy |

Les migrations de base de données s'exécutent automatiquement au démarrage de chaque service.

### 3. Vérifier que tout tourne

```bash
# Statut des conteneurs
docker compose ps

# Health checks
curl http://localhost:8000/health    # → {"status":"ok"}
curl http://localhost:8000/ready     # → {"status":"ok","db":"ok","redis":"ok"}
curl http://localhost:3001/health    # → {"status":"ok"}

# Logs en temps réel
docker compose logs -f agentcore
docker compose logs -f flowrunner
```

### 4. Accéder aux interfaces

| Interface | URL |
|-----------|-----|
| React editor | http://localhost:5173 (dev) |
| AgentCore API docs | http://localhost:8000/docs |
| FlowRunner Swagger | http://localhost:3001/documentation |
| Prometheus metrics | http://localhost:8000/metrics |

> Le client React (`localhost:5173`) nécessite un serveur Vite séparé (voir section Développement local). En production, le build statique est servi par un CDN ou Nginx.

### 5. Arrêter les services

```bash
docker compose down          # arrête sans supprimer les volumes
docker compose down -v       # arrête ET supprime les données (reset complet)
```

---

## Variables d'environnement

Toutes les variables sont lues depuis le fichier `.env` à la racine. L'application refuse de démarrer si une variable obligatoire est absente.

### OpenRouter (LLM)

| Variable | Obligatoire | Défaut | Description |
|----------|-------------|--------|-------------|
| `OPENROUTER_API_KEY` | oui | — | Clé API OpenRouter. Obtenir sur openrouter.ai |
| `OPENROUTER_DEFAULT_MODEL` | non | `openai/gpt-4o-mini` | Modèle utilisé si non précisé dans la requête. Voir [openrouter.ai/models](https://openrouter.ai/models) |

**Modèles disponibles (exemples) :**

| Modèle | Coût approx. | Usage recommandé |
|--------|-------------|-----------------|
| `openai/gpt-4o-mini` | ~$0.15/M tokens | Défaut — économique, rapide |
| `openai/gpt-4o` | ~$5/M tokens | Tâches complexes |
| `anthropic/claude-3-haiku` | ~$0.25/M tokens | Alternative économique |
| `mistralai/mistral-7b-instruct` | ~$0.06/M tokens | Budget très serré |

### Base de données

| Variable | Obligatoire | Défaut | Description |
|----------|-------------|--------|-------------|
| `POSTGRES_USER` | non | `postgres` | Utilisateur PostgreSQL (Docker uniquement) |
| `POSTGRES_PASSWORD` | non | `postgres` | Mot de passe PostgreSQL (Docker uniquement) |
| `POSTGRES_DB` | non | `portfolio` | Nom de la base initiale (Docker uniquement) |
| `DATABASE_URL` | oui | — | URL de connexion AgentCore. Format : `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `FLOWRUNNER_DATABASE_URL` | oui | — | URL de connexion FlowRunner. Format : `postgresql://user:pass@host:5432/dbname` |

> `DATABASE_URL` doit utiliser le driver `asyncpg` (`postgresql+asyncpg://`). FlowRunner utilise `postgres.js` et ne requiert pas ce préfixe.

**En Docker :** utiliser le nom de service comme hostname (`postgres`).
**En local :** utiliser `localhost`.

### Redis

| Variable | Obligatoire | Défaut | Description |
|----------|-------------|--------|-------------|
| `REDIS_URL` | non | `redis://localhost:6379` | URL Redis partagée par les deux services |

**En Docker :** `redis://redis:6379`
**En local :** `redis://localhost:6379`

### Sécurité

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `AGENTCORE_API_KEY` | oui | Clé d'accès à l'API AgentCore. Générer avec `openssl rand -hex 32` |
| `FLOWRUNNER_API_KEY` | oui | Clé d'accès à l'API FlowRunner. Générer avec `openssl rand -hex 32` |

### CORS et intégration inter-services

| Variable | Défaut | Description |
|----------|--------|-------------|
| `FLOWRUNNER_ORIGIN` | `http://localhost:5173` | Origine autorisée par AgentCore (CORS). En prod : URL du frontend. |
| `AGENTCORE_ORIGIN` | `http://agentcore:8000` | URL qu'utilise FlowRunner pour appeler AgentCore. **En Docker :** `http://agentcore:8000`. **En local :** `http://localhost:8000` |

### Limites agents

| Variable | Défaut | Description |
|----------|--------|-------------|
| `DEFAULT_MAX_ITERATIONS` | `10` | Nombre max d'itérations par run agent |
| `DEFAULT_BUDGET_USD` | `0.10` | Plafond de coût en USD par run |
| `DEFAULT_MAX_TOKENS` | `4000` | Tokens max par appel LLM |

Ces valeurs sont des défauts ; chaque requête `POST /api/v1/agents/run` peut les surcharger.

---

## Développement local (sans Docker)

### AgentCore

```bash
cd agentcore

# Créer et activer un virtualenv
python -m venv .venv
source .venv/bin/activate

# Installer les dépendances (dev inclus)
pip install -r requirements-dev.txt

# Appliquer les migrations (PostgreSQL doit tourner)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agentcore \
  alembic upgrade head

# Lancer le serveur avec hot-reload
uvicorn agentcore.main:app --reload --port 8000
```

Démarrer le worker ARQ dans un second terminal :

```bash
cd agentcore
source .venv/bin/activate
arq agentcore.worker.WorkerSettings
```

### FlowRunner Server

```bash
cd flowrunner/server
npm install

# Appliquer les migrations (PostgreSQL doit tourner)
FLOWRUNNER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flowrunner \
  node --import tsx/esm scripts/migrate.ts

# Lancer avec hot-reload (tsx watch)
npm run dev
```

### FlowRunner Client

```bash
cd flowrunner/client
npm install

# Configurer les clés API côté client
cat > .env.local << EOF
VITE_FLOWRUNNER_API_KEY=<votre-FLOWRUNNER_API_KEY>
VITE_AGENTCORE_API_KEY=<votre-AGENTCORE_API_KEY>
EOF

npm run dev   # démarre sur http://localhost:5173
```

> `.env.local` est gitignored. Ne jamais le commiter.

---

## Migrations de base de données

### AgentCore (Alembic)

```bash
# Appliquer toutes les migrations
alembic upgrade head

# Voir l'état actuel
alembic current

# Créer une nouvelle migration
alembic revision --autogenerate -m "add_column_xyz"

# Revenir en arrière d'une migration
alembic downgrade -1
```

Les fichiers de migration se trouvent dans `agentcore/agentcore/db/migrations/versions/`.

### FlowRunner (SQL brut)

```bash
# Appliquer les migrations
node --import tsx/esm scripts/migrate.ts
```

Les fichiers SQL se trouvent dans `flowrunner/server/migrations/`. Chaque fichier est un script idempotent (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).

---

## CI/CD (GitHub Actions)

Trois workflows plus Dependabot :

### `ci.yml` — déclenché sur push `main`/`develop` et PR vers `main`

```
push / PR → main
          │
          ├── agentcore (Python)
          │     lint (ruff) → format check → type check (mypy) → migrations → pytest (≥80% coverage)
          │
          ├── flowrunner (Node.js)
          │     lint (ESLint) → type check (tsc) → vitest → build client
          │
          └── docker-build  (après agentcore + flowrunner)
                docker compose build
```

**Branch protection `main` :** merge bloqué si un job est rouge.

### `cd.yml` — déclenché sur push `main` uniquement

Build et push des images Docker vers GitHub Container Registry (GHCR) :

```
ghcr.io/<owner>/projet-1/agentcore:latest   (+ tag SHA)
ghcr.io/<owner>/projet-1/flowrunner:latest  (+ tag SHA)
```

Aucun secret à configurer — utilise `GITHUB_TOKEN` automatiquement.

Pour déployer la dernière version sur un serveur :

```bash
docker pull ghcr.io/<owner>/projet-1/agentcore:latest
docker pull ghcr.io/<owner>/projet-1/flowrunner:latest
docker compose up -d
```

### `security.yml` — déclenché sur push `main` + chaque lundi à 8h UTC

Scan Trivy des deux images (CRITICAL + HIGH). Les résultats sont visibles dans l'onglet **Security → Code scanning** du repo GitHub. Le pipeline ne bloque pas sur les CVE des images de base (incontournables), mais les signale.

### Dependabot

PRs de mise à jour automatiques chaque semaine pour `pip` (agentcore), `npm` (server + client), et les actions GitHub.

### Lancer la CI localement

```bash
# Installer les hooks pre-commit (lint + types avant chaque commit)
pre-commit install

# Simuler la CI manuellement
make lint
make typecheck
make test
```

---

## Build Docker en production

Les Dockerfiles sont optimisés pour la production :

**AgentCore** (`agentcore/Dockerfile`) — image unique `python:3.12-slim` :
- Installe les dépendances depuis `requirements.txt`
- Pas de `requirements-dev.txt` (pytest, ruff, mypy exclus)
- Taille finale : ~400 MB

**FlowRunner** (`flowrunner/server/Dockerfile`) — multi-stage :
- Stage `builder` : compile TypeScript → `dist/`
- Stage `production` : copie uniquement `dist/` + dépendances production
- Taille finale : ~180 MB

```bash
# Build toutes les images
docker compose build

# Build une image spécifique
docker compose build agentcore
docker compose build flowrunner

# Vérifier la taille des images
docker images | grep projet
```

---

## Commandes Makefile

```bash
make up           # docker compose up -d
make down         # docker compose down
make build        # docker compose build
make migrate      # migrations Alembic + FlowRunner SQL
make test         # pytest + vitest
make test-ac      # pytest (AgentCore uniquement)
make test-fr      # vitest (FlowRunner uniquement)
make lint         # ruff + ESLint
make typecheck    # mypy + tsc
make dev-ac       # AgentCore hot-reload (local)
make dev-fr       # FlowRunner server hot-reload (local)
make dev-client   # Vite dev server (local)
make logs         # docker compose logs -f
make clean        # docker compose down -v --remove-orphans
make install      # pip install -r requirements-dev.txt + npm install + pre-commit install
```

---

## Déploiement en production (VPS / VM)

### Checklist

- [ ] Générer des clés API fortes : `openssl rand -hex 32`
- [ ] Utiliser des mots de passe PostgreSQL forts
- [ ] `FLOWRUNNER_ORIGIN` = domaine réel du frontend (pas `localhost`)
- [ ] `AGENTCORE_ORIGIN` = `http://agentcore:8000` (interne Docker) ou URL interne
- [ ] Placer un reverse proxy (Nginx / Caddy) devant les ports 8000 et 3001
- [ ] Activer HTTPS sur le reverse proxy
- [ ] Ne jamais exposer PostgreSQL (5432) et Redis (6379) à l'extérieur
- [ ] Définir `DEFAULT_BUDGET_USD` selon votre budget OpenRouter mensuel
- [ ] Configurer des alertes sur `/metrics` (Prometheus + Grafana ou Datadog)

### Nginx (exemple minimal)

```nginx
server {
    listen 443 ssl;
    server_name api.monprojet.com;

    location /agentcore/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;   # pour WebSocket
        proxy_set_header Connection "upgrade";
    }

    location /flowrunner/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Variables d'environnement à changer pour la production

```bash
# .env (production)
DATABASE_URL=postgresql+asyncpg://user:STRONG_PASS@postgres:5432/agentcore
FLOWRUNNER_DATABASE_URL=postgresql://user:STRONG_PASS@postgres:5432/flowrunner
REDIS_URL=redis://:REDIS_PASS@redis:6379   # avec mot de passe Redis
AGENTCORE_API_KEY=<64-char-hex>
FLOWRUNNER_API_KEY=<64-char-hex>
FLOWRUNNER_ORIGIN=https://monapp.com       # domaine réel
AGENTCORE_ORIGIN=http://agentcore:8000     # inchangé (interne Docker)
DEFAULT_BUDGET_USD=1.00                    # ajuster selon budget
```

---

## Dépannage

### Le conteneur `agentcore` ne démarre pas

```bash
docker compose logs agentcore | tail -30
```

Causes fréquentes :
- Variable d'environnement manquante → message `ValidationError` au démarrage
- Migration Alembic échoue → vérifier que `DATABASE_URL` pointe vers le bon host

### `agentcore-worker` crash au démarrage

```bash
docker compose logs agentcore-worker
```

Cause typique : `'str' object has no attribute 'host'` → `REDIS_URL` mal formé ou ARQ reçoit une chaîne au lieu d'un objet `RedisSettings`.

### FlowRunner retourne 401

Vérifier que le header `X-API-Key` correspond exactement à `FLOWRUNNER_API_KEY` dans `.env`.

### Le nœud `ai-agent` échoue avec 401 AgentCore

Vérifier que `AGENTCORE_API_KEY` dans `.env` correspond à la clé configurée sur le service agentcore, et que `AGENTCORE_ORIGIN=http://agentcore:8000` (pas `localhost` en Docker).

### Recréer un conteneur après modification de `.env`

```bash
# `restart` ne relit pas env_file — il faut recréer
docker compose up -d --force-recreate <service>
```
