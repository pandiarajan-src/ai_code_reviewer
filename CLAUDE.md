# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
AI-powered code review agent for Bitbucket Enterprise Server that automatically reviews pull requests and commits using LLMs (OpenAI GPT-4, local Ollama). The agent sends intelligent code review feedback via email notifications to commit/PR authors using Azure Logic Apps integration.

## Repository Structure

```
src/ai_code_reviewer/        # Main application package
├── api/                     # FastAPI application layer
│   ├── app.py              # App initialization
│   ├── dependencies.py     # Dependency injection
│   └── routes/             # API route handlers
│       ├── health.py       # Health check endpoints
│       ├── webhook.py      # Webhook handlers
│       ├── manual.py       # Manual review endpoints
│       └── reviews.py      # Review retrieval endpoints
├── core/                    # Core business logic
│   ├── config.py           # Configuration management
│   ├── review_engine.py    # Review processing orchestration
│   └── email_formatter.py  # Email HTML formatting
├── clients/                 # External API clients
│   ├── bitbucket_client.py # Bitbucket API integration
│   ├── llm_client.py       # LLM provider abstraction
│   └── email_client.py     # Email sending via Logic Apps
├── db/                      # Database layer
│   ├── models.py           # SQLAlchemy models for review records
│   ├── database.py         # Database configuration and session management
│   └── repository.py       # Data access layer for review operations
└── main.py                 # Application entry point

tests/                       # Test suite
├── unit/                   # Unit tests
├── integration/            # Integration tests
├── fixtures/               # Test fixtures
└── conftest.py             # Shared test configuration

scripts/                    # Development tools
├── lint.sh                # Linting automation
├── run_tests.py           # Test runner
└── db_helper.py           # Database management utility

docker/                     # Docker configuration
├── Dockerfile             # Container definition
└── docker-compose.yml     # Multi-container orchestration

docs/                       # Documentation
├── architecture.md        # System architecture
├── development.md         # Development guide
├── deployment.md          # Deployment instructions
└── project-summary.md     # Project overview
```

## Key Commands

### Installation
```bash
# Install production dependencies (recommended - using uv)
uv sync --no-dev

# Or install with pip
pip install -r requirements.txt

# Install development dependencies (includes testing, linting, security tools)
uv pip install -e ".[dev]"
# Or: pip install -e ".[dev]"

# Install specific dependency groups
pip install -e ".[test]"  # Testing only
pip install -e ".[lint]"  # Linting only
```

### Testing
```bash
# Run all tests with coverage
python scripts/run_tests.py

# Or using Makefile
make test

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run specific test modules
pytest tests/unit/test_config.py -v
pytest tests/unit/test_bitbucket_client.py -v

# Run tests with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

### Code Quality
```bash
# Run comprehensive linting (ruff, black, mypy) with auto-fix
./scripts/lint.sh

# Or using Makefile
make lint

# Check code without modifications
./scripts/lint.sh --check-only

# Run linting without auto-fix
./scripts/lint.sh --no-fix

# Security scanning (Bandit for code, Safety for dependencies)
make security-check       # Run Bandit security scan
make security-deps        # Check dependencies for vulnerabilities

# Pre-commit hooks (optional but recommended)
pre-commit install        # Install git hooks
pre-commit run --all-files  # Run all pre-commit checks
```

### Database Management
```bash
# Database helper script for development and testing
python scripts/db_helper.py create    # Create/initialize database
python scripts/db_helper.py reset     # Drop and recreate tables
python scripts/db_helper.py clean     # Remove all records
python scripts/db_helper.py stats     # Show statistics
python scripts/db_helper.py seed      # Seed test data
python scripts/db_helper.py list      # List recent reviews
python scripts/db_helper.py backup    # Backup database (SQLite)
python scripts/db_helper.py restore --file backup.db  # Restore backup

# Useful for:
# - Setting up test data for API/integration testing
# - Resetting database between test runs
# - Development and debugging
# - Creating backups before major changes
```

### Development Server
```bash
# Run the FastAPI server locally (recommended - uses module syntax)
python -m ai_code_reviewer.main

# Or using Makefile
make dev

# With environment variables
export BITBUCKET_URL=https://your-bitbucket.com
export BITBUCKET_TOKEN=your_token
export LLM_API_KEY=your_api_key
python -m ai_code_reviewer.main
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# For local LLM with Ollama
docker-compose -f docker/docker-compose.yml --profile local-llm up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer

# Stop (database persists)
docker-compose -f docker/docker-compose.yml down

# Remove including volumes (CAUTION: deletes database)
docker-compose -f docker/docker-compose.yml down -v

# Using Makefile (recommended)
make docker-build
make docker-run
make docker-logs

# Note: Database is stored in persistent volume 'db_data' at /app/data/ai_code_reviewer.db
```

## Architecture

### Layered Architecture
The application follows a clean layered architecture:

1. **API Layer** (`src/ai_code_reviewer/api/`): FastAPI routes, request/response handling
2. **Core Layer** (`src/ai_code_reviewer/core/`): Business logic, review orchestration, configuration
3. **Client Layer** (`src/ai_code_reviewer/clients/`): External service integrations
4. **Database Layer** (`src/ai_code_reviewer/db/`): SQLAlchemy models, database operations, review record persistence

### Core Components
- **src/ai_code_reviewer/main.py**: Application entry point
- **src/ai_code_reviewer/api/app.py**: FastAPI app initialization with database lifecycle management
- **src/ai_code_reviewer/api/routes/**: HTTP endpoint handlers (health, webhook, manual review, review retrieval)
- **src/ai_code_reviewer/core/review_engine.py**: Review processing orchestration with database persistence
- **src/ai_code_reviewer/core/config.py**: Configuration management and validation
- **src/ai_code_reviewer/core/email_formatter.py**: HTML email formatting
- **src/ai_code_reviewer/clients/bitbucket_client.py**: Bitbucket API integration
- **src/ai_code_reviewer/clients/llm_client.py**: LLM provider abstraction (OpenAI/Ollama)
- **src/ai_code_reviewer/clients/email_client.py**: Email sending via Azure Logic Apps
- **src/ai_code_reviewer/db/models.py**: SQLAlchemy models for review records
- **src/ai_code_reviewer/db/database.py**: Database configuration and session management
- **src/ai_code_reviewer/db/repository.py**: Data access layer for review record operations

### Key Integrations
1. **Webhook Processing**: Receives Bitbucket webhooks (PR opened/updated, commits pushed), validates signatures, triggers async review
2. **Review Pipeline**: Fetches diff from Bitbucket → Sends to LLM with structured prompt → Parses response → Saves to database → Sends HTML email to author
3. **Email Notifications**: Uses Azure Logic Apps to send formatted HTML email notifications to commit/PR authors
4. **LLM Providers**: Supports OpenAI (cloud) and Ollama (local) with provider abstraction in LLMClient
5. **Database Persistence**: All reviews are automatically saved with complete metadata (diff, feedback, author, timestamps, email status)

### API Endpoints
- `/health`: Comprehensive health check (Bitbucket connectivity, LLM status)
- `/webhook/code-review`: Webhook receiver for Bitbucket events
- `/manual-review`: Manual review trigger endpoint
- `/reviews/*`: Review retrieval endpoints (latest, paginated, by ID/project/author/commit/PR)

## Environment Configuration
Required environment variables are defined in config.py with validation. Key variables:
- `BITBUCKET_URL`, `BITBUCKET_TOKEN`: Bitbucket Enterprise connection
- `LLM_PROVIDER`: "openai" or "local_ollama"
- `LLM_API_KEY`: For OpenAI provider
- `OLLAMA_HOST`: For local Ollama provider
- `WEBHOOK_SECRET`: Optional webhook signature verification
- `LOGIC_APP_EMAIL_URL`: Azure Logic App HTTP trigger URL for email notifications
- `LOGIC_APP_FROM_EMAIL`: From email address for notifications (default: pandiarajans@test.com)
- `EMAIL_OPTOUT`: Set to "true" to disable email sending for testing (default: true)
- `DATABASE_URL`: Database connection string (default: sqlite+aiosqlite:///./ai_code_reviewer.db)
- `DATABASE_ECHO`: Enable SQL query logging for debugging (default: false)

## Testing Strategy
- Unit tests in `tests/unit/` directory for isolated component testing
- Integration tests in `tests/integration/` for end-to-end API testing
- Shared pytest fixtures in `tests/conftest.py`
- Comprehensive test runner in `scripts/run_tests.py` that validates all functionality
- Mock-based testing for external API calls (Bitbucket, LLM providers)
- Coverage reporting with HTML output in `htmlcov/`
- Target coverage: 80%+ (enforced in pytest configuration)
- Async test support via pytest-asyncio

## Code Standards
- Python 3.12+ with type hints
- Package management: pyproject.toml with setuptools (PEP 517/518)
- Dependency management: uv (recommended) or pip
- Formatting: Black (120 char line length)
- Linting: Ruff with comprehensive rules (configured in pyproject.toml)
- Type checking: MyPy with gradual typing
- Security scanning: Bandit (code) and Safety (dependencies)
- Pre-commit hooks: Available for automated quality checks
- Async/await for non-blocking operations
- Structured logging with appropriate log levels
- Environment configuration: python-dotenv for .env file loading
