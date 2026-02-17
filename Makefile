.PHONY: help dev dev-backend dev-frontend test test-unit test-integration test-all test-e2e \
	infra-up infra-down docker-build docker-run clean version version-patch version-minor version-major \
	lint format migrate

.DEFAULT_GOAL := help

# ──────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ──────────────────────────────────────────────
# Infrastructure
# ──────────────────────────────────────────────

infra-up: ## Start infrastructure services (PostgreSQL)
	docker compose up -d
	@echo "Waiting for database to be ready..."
	@$(MAKE) --no-print-directory wait-for-db
	@echo "Infrastructure is ready."

infra-down: ## Stop infrastructure services
	docker compose down

wait-for-db:
	@timeout=30; \
	while ! docker compose exec -T db pg_isready -U $${POSTGRES_USER:-pulse} -d $${POSTGRES_DB:-pulse_board} > /dev/null 2>&1; do \
		timeout=$$((timeout - 1)); \
		if [ $$timeout -le 0 ]; then \
			echo "Error: Database did not become ready in time"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

# ──────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────

dev: ## Start backend, frontend, and infrastructure
	@$(MAKE) --no-print-directory infra-up
	@trap 'kill 0; $(MAKE) --no-print-directory infra-down' EXIT; \
	$(MAKE) --no-print-directory dev-backend & \
	$(MAKE) --no-print-directory dev-frontend & \
	wait

dev-backend: ## Start backend with hot reload
	@$(MAKE) --no-print-directory infra-up
	uv run uvicorn pulse_board.presentation.api.app:create_app --host 0.0.0.0 --port 8000 --reload --factory

dev-frontend: ## Start frontend with HMR
	cd frontend && source $$HOME/.nvm/nvm.sh && nvm use 22 && npm run dev

migrate: ## Run database migrations
	@$(MAKE) --no-print-directory infra-up
	uv run alembic upgrade head

# ──────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────

test: test-unit ## Run unit tests (alias)

test-unit: ## Run unit tests
	uv run pytest tests/unit -v

test-integration: ## Run integration tests
	@$(MAKE) --no-print-directory infra-up
	uv run pytest tests/integration -v

test-all: ## Run all tests (unit + integration)
	@$(MAKE) --no-print-directory infra-up
	uv run pytest tests/ -v

test-e2e: ## Run end-to-end tests (placeholder)
	@echo "E2E tests not yet configured"

# ──────────────────────────────────────────────
# Code Quality
# ──────────────────────────────────────────────

lint: ## Run linters (ruff + pyright)
	uv run ruff check .
	uv run ruff format . --check
	uv run pyright

format: ## Auto-format code
	uv run ruff check . --fix
	uv run ruff format .

# ──────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────

docker-build: ## Build Docker image
	docker build -t pulse-board:$$($(MAKE) --no-print-directory version) \
		-t pulse-board:latest .

docker-run: ## Run application in Docker
	docker run --rm --network host --env-file .env pulse-board:latest

# ──────────────────────────────────────────────
# Cleanup
# ──────────────────────────────────────────────

clean: ## Remove all build artifacts and infrastructure
	docker compose down -v 2>/dev/null || true
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache .mypy_cache
	rm -rf frontend/node_modules frontend/dist frontend/.vite
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete."

# ──────────────────────────────────────────────
# Versioning
# ──────────────────────────────────────────────

version: ## Show current version
	@uv run python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"

version-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@uv run python3 -c "\
	import re, pathlib; \
	p = pathlib.Path('pyproject.toml'); \
	t = p.read_text(); \
	m = re.search(r'version\s*=\s*\"(\d+)\.(\d+)\.(\d+)\"', t); \
	v = f'{m.group(1)}.{m.group(2)}.{int(m.group(3))+1}'; \
	p.write_text(re.sub(r'(version\s*=\s*\")[\d.]+\"', f'\g<1>{v}\"', t)); \
	print(f'Version bumped to {v}')"

version-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@uv run python3 -c "\
	import re, pathlib; \
	p = pathlib.Path('pyproject.toml'); \
	t = p.read_text(); \
	m = re.search(r'version\s*=\s*\"(\d+)\.(\d+)\.(\d+)\"', t); \
	v = f'{m.group(1)}.{int(m.group(2))+1}.0'; \
	p.write_text(re.sub(r'(version\s*=\s*\")[\d.]+\"', f'\g<1>{v}\"', t)); \
	print(f'Version bumped to {v}')"

version-major: ## Bump major version (0.1.0 -> 1.0.0)
	@uv run python3 -c "\
	import re, pathlib; \
	p = pathlib.Path('pyproject.toml'); \
	t = p.read_text(); \
	m = re.search(r'version\s*=\s*\"(\d+)\.(\d+)\.(\d+)\"', t); \
	v = f'{int(m.group(1))+1}.0.0'; \
	p.write_text(re.sub(r'(version\s*=\s*\")[\d.]+\"', f'\g<1>{v}\"', t)); \
	print(f'Version bumped to {v}')"
