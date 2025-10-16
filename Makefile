# AI Code Reviewer - Makefile
# Comprehensive development and deployment commands

.PHONY: help install install-dev test test-coverage test-unit test-integration lint lint-check format type-check security-check security-deps clean dev server stop docker-build docker-run docker-stop docker-logs docker-clean health

# Configuration
PYTHON := python3
PIP := pip
PYTEST := pytest
COVERAGE_MIN := 80
SERVER_HOST := 0.0.0.0
SERVER_PORT := $(shell echo $${PORT:-8000})

# Load .env file if it exists (for environment variables)
ifneq (,$(wildcard .env))
	include .env
	export
endif

# Help target - default when running 'make'
help: ## Show this help message
	@echo "AI Code Reviewer - Available Commands"
	@echo "====================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment Variables:"
	@echo "  BITBUCKET_URL      - Bitbucket server URL"
	@echo "  BITBUCKET_TOKEN    - Bitbucket access token"
	@echo "  LLM_PROVIDER       - openai or local_ollama"
	@echo "  LLM_API_KEY        - API key for LLM provider"
	@echo "  WEBHOOK_SECRET     - Optional webhook signature verification"

# Installation targets
install: ## Install production dependencies
	@echo "📦 Installing production dependencies..."
	uv sync --no-dev

install-dev: ## Install all dependencies including development tools
	@echo "📦 Installing development dependencies..."
	uv pip install -e ".[dev]"
	@echo "✅ Development environment ready!"

# Testing targets
test: ## Run all tests with coverage
	@echo "🧪 Running all tests with coverage..."
	$(PYTHON) scripts/run_tests.py

test-coverage: ## Run tests and generate detailed coverage report
	@echo "📊 Running tests with detailed coverage report..."
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=$(COVERAGE_MIN)
	@echo "📄 Coverage report generated in htmlcov/"

test-unit: ## Run only unit tests
	@echo "🔬 Running unit tests..."
	$(PYTEST) tests/unit/ -v --cov=src --cov-report=term-missing

test-integration: ## Run only integration tests
	@echo "🔗 Running integration tests..."
	$(PYTEST) tests/integration/ -v --cov=src --cov-report=term-missing

test-fast: ## Run tests without coverage (faster)
	@echo "⚡ Running fast tests..."
	$(PYTEST) tests/ -v --no-cov

# Code Quality targets
lint: ## Run comprehensive linting with auto-fix
	@echo "🔧 Running comprehensive linting with auto-fix..."
	./scripts/lint.sh

lint-check: ## Check code quality without making changes
	@echo "🔍 Checking code quality..."
	./scripts/lint.sh --check-only

format: ## Format code with black and ruff
	@echo "🎨 Formatting code..."
	ruff format .
	black .
	@echo "✅ Code formatting completed!"

type-check: ## Run type checking with mypy
	@echo "🔍 Running type checking..."
	mypy src/ --ignore-missing-imports
	mypy tests/ --ignore-missing-imports
	mypy scripts/ --ignore-missing-imports

security-check: ## Run security checks with bandit
	@echo "🔒 Running security checks with Bandit..."
	@echo "Note: Known acceptable risks (self-signed certs, Docker binding) are documented in pyproject.toml"
	@bandit -r src/ -f txt --severity-level medium || true
	@echo ""
	@echo "ℹ️  To suppress documented exceptions, use #nosec comments in code"
	@echo "ℹ️  See pyproject.toml [tool.bandit] for configuration"

security-deps: ## Check dependencies for security vulnerabilities
	@echo "🔍 Checking dependencies for vulnerabilities with Safety..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run safety check 2>&1 | grep -v "DEPRECATED" || echo "⚠️  Vulnerabilities found - review and update dependencies"; \
	elif command -v safety >/dev/null 2>&1; then \
		safety check 2>&1 | grep -v "DEPRECATED" || echo "⚠️  Vulnerabilities found - review and update dependencies"; \
	else \
		echo "⚠️  Safety not installed. Install with: uv pip install -e \".[dev]\""; \
		echo "   Or: pip install safety"; \
	fi

# Development server targets
dev: ## Start development server with auto-reload
	@echo "🚀 Starting development server..."
	@echo "Server will be available at http://$(SERVER_HOST):$(SERVER_PORT)"
	@echo "Press Ctrl+C to stop"
	$(PYTHON) -m ai_code_reviewer.main

server: dev ## Alias for dev command

stop: ## Stop any running Python processes (development server)
	@echo "🛑 Stopping development server..."
	@pkill -f "python.*main.py" || echo "No running server found"

# Docker targets
docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -f docker/Dockerfile -t ai-code-reviewer .
	@echo "✅ Docker image built successfully!"

docker-run: ## Run application in Docker container
	@echo "🐳 Starting Docker container..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "✅ Container started! Check status with 'make docker-logs'"

docker-run-local: ## Run with local Ollama LLM
	@echo "🐳 Starting with local Ollama LLM..."
	docker-compose -f docker/docker-compose.yml --profile local-llm up -d
	@echo "✅ Container with local LLM started!"

docker-stop: ## Stop Docker containers
	@echo "🛑 Stopping Docker containers..."
	docker-compose -f docker/docker-compose.yml down

docker-logs: ## View Docker container logs
	@echo "📋 Viewing container logs (Ctrl+C to exit)..."
	docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer

docker-logs-ollama: ## View Ollama container logs
	@echo "📋 Viewing Ollama logs (Ctrl+C to exit)..."
	docker-compose -f docker/docker-compose.yml logs -f ollama

docker-clean: ## Clean Docker containers and images
	@echo "🧹 Cleaning Docker containers and images..."
	docker-compose -f docker/docker-compose.yml down --volumes --remove-orphans
	docker image prune -f
	@echo "✅ Docker cleanup completed!"

# Health and monitoring targets
health: ## Check application health
	@echo "🏥 Checking application health..."
	@curl -f http://localhost:$(SERVER_PORT)/health || echo "❌ Health check failed - is the server running?"

health-detailed: ## Detailed health check with external API validation
	@echo "🔍 Detailed health check (includes external API calls)..."
	@curl -s http://localhost:$(SERVER_PORT)/health/detailed | python -m json.tool || echo "❌ Health check failed or invalid JSON"

# Utility targets
clean: ## Clean temporary files and caches
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	@echo "✅ Cleanup completed!"

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "✅ Full cleanup completed!"

# Pre-commit setup
pre-commit-install: ## Install pre-commit hooks
	@echo "🔗 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

pre-commit-run: ## Run pre-commit on all files
	@echo "🔍 Running pre-commit on all files..."
	pre-commit run --all-files

# Quick development workflow
check: lint-check test-fast ## Quick check - lint and fast tests

ci: lint test ## Full CI pipeline - lint and test with coverage

# One-command setup for new developers
setup: install-dev env-example ## Complete setup for new developers
	@echo ""
	@echo "🎉 Setup completed!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and configure your settings"
	@echo "2. Run 'make dev' to start the development server"
	@echo "3. Run 'make test' to verify everything works"
	@echo ""

# Release preparation
release-check: clean ci ## Prepare for release - clean, lint, and test
	@echo "🚀 Release checks completed successfully!"

# Database/migration targets (if needed in future)
# migrate: ## Run database migrations
# migrate-create: ## Create new migration

# Monitoring targets
logs: ## View application logs
	@echo "📋 Viewing application logs..."
	@tail -f logs/*.log 2>/dev/null || echo "No log files found in logs/ directory"

# Documentation targets
docs-serve: ## Serve documentation locally (if docs exist)
	@echo "📚 Checking for documentation..."
	@if [ -f "README.md" ]; then echo "README.md found"; else echo "No documentation found"; fi

# Version information
version: ## Show version information
	@echo "AI Code Reviewer Version Information"
	@echo "==================================="
	@grep -E "^version" pyproject.toml || echo "Version not found in pyproject.toml"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Dependencies:"
	@uv --version 2>/dev/null || echo "uv not installed"

# Default target
.DEFAULT_GOAL := help
