.PHONY: help up down logs migrate test test-ac test-fr lint typecheck build clean install dev-ac dev-fr

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Stream logs from all services
	docker compose logs -f

migrate: ## Run all database migrations
	docker compose run --rm agentcore alembic upgrade head
	cd flowrunner/server && npm run db:migrate

test: ## Run all tests (set env vars or use a .env file)
	cd agentcore && pytest --cov=agentcore --cov-report=term-missing
	cd flowrunner/server && npm test

test-ac: ## Run AgentCore tests only
	cd agentcore && pytest -v

test-fr: ## Run FlowRunner tests only
	cd flowrunner/server && npm test

lint: ## Lint both projects
	cd agentcore && ruff check .
	cd flowrunner/server && npm run lint

typecheck: ## Type-check both projects
	cd agentcore && mypy agentcore/
	cd flowrunner/server && npm run typecheck

build: ## Build Docker images
	docker compose build

clean: ## Remove containers, volumes, and caches
	docker compose down -v --remove-orphans
	find agentcore -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find agentcore -name "*.pyc" -delete 2>/dev/null || true

install: ## Install all local dependencies
	cd agentcore && pip install -r requirements-dev.txt
	pre-commit install
	cd flowrunner/server && npm install
	cd flowrunner/client && npm install

dev-ac: ## Start AgentCore in dev mode (hot-reload)
	cd agentcore && uvicorn agentcore.main:app --reload --port 8000

dev-fr: ## Start FlowRunner server in dev mode
	cd flowrunner/server && npm run dev

dev-client: ## Start React dev server
	cd flowrunner/client && npm run dev
