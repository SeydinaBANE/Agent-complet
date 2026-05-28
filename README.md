# Portfolio Agentic

[![CI](https://github.com/SeydinaBANE/projet-1/actions/workflows/ci.yml/badge.svg)](https://github.com/SeydinaBANE/projet-1/actions/workflows/ci.yml)
[![CD](https://github.com/SeydinaBANE/projet-1/actions/workflows/cd.yml/badge.svg)](https://github.com/SeydinaBANE/projet-1/actions/workflows/cd.yml)
[![Security](https://github.com/SeydinaBANE/projet-1/actions/workflows/security.yml/badge.svg)](https://github.com/SeydinaBANE/projet-1/actions/workflows/security.yml)

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
# Fill in OPENROUTER_API_KEY then generate API keys:
# openssl rand -hex 32  (run twice — once for AGENTCORE_API_KEY, once for FLOWRUNNER_API_KEY)

# 2. Install local dev dependencies (Python, Node, pre-commit hooks)
make install

# 3. Start all services — migrations run automatically on startup
make up

# 4. Open
# AgentCore API docs → http://localhost:8000/docs
# FlowRunner API    → http://localhost:3001/documentation
# React editor      → http://localhost:5173
```

> **Note:** `AGENTCORE_ORIGIN` in `.env` must be `http://agentcore:8000` when running via Docker Compose, or `http://localhost:8000` for local dev (without Docker).

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

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architecture technique détaillée — LangGraph graph, schémas DB, types de nœuds, sécurité, observabilité |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Guide de déploiement — Docker Compose, variables d'environnement, CI/CD (lint → test → push GHCR → Trivy), production |
| [`agentcore/README.md`](agentcore/README.md) | API AgentCore complète — endpoints, outils, guardrails, tests |
| [`flowrunner/README.md`](flowrunner/README.md) | API FlowRunner complète — types de nœuds, contexte, tests, frontend |

## Architecture

```
Browser (React + React Flow)
    │  REST
    ▼
FlowRunner Server (Fastify · Node.js 20 · BullMQ)
    │  POST /api/v1/agents/run
    ▼
AgentCore (FastAPI · Python 3.12 · LangGraph · ARQ)
    │
    ├── PostgreSQL  (runs, actions, workflows, run_steps)
    └── Redis       (ARQ queue, BullMQ queue, pub/sub stream, agent memory)
```
