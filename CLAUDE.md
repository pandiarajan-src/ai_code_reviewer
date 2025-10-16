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
│       └── manual.py       # Manual review endpoints
├── core/                    # Core business logic
│   ├── config.py           # Configuration management
│   ├── review_engine.py    # Review processing orchestration
│   └── email_formatter.py  # Email HTML formatting
├── clients/                 # External API clients
│   ├── bitbucket_client.py # Bitbucket API integration
│   ├── llm_client.py       # LLM provider abstraction
│   └── email_client.py     # Email sending via Logic Apps
└── main.py                 # Application entry point

tests/                       # Test suite
├── unit/                   # Unit tests
├── integration/            # Integration tests
├── fixtures/               # Test fixtures
└── conftest.py             # Shared test configuration

scripts/                    # Development tools
├── lint.sh                # Linting automation
└── run_tests.py           # Test runner

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

# Using Makefile (recommended)
make docker-build
make docker-run
make docker-logs
```

## Architecture

### Layered Architecture
The application follows a clean layered architecture:

1. **API Layer** (`src/ai_code_reviewer/api/`): FastAPI routes, request/response handling
2. **Core Layer** (`src/ai_code_reviewer/core/`): Business logic, review orchestration, configuration
3. **Client Layer** (`src/ai_code_reviewer/clients/`): External service integrations

### Core Components
- **src/ai_code_reviewer/main.py**: Application entry point
- **src/ai_code_reviewer/api/app.py**: FastAPI app initialization
- **src/ai_code_reviewer/api/routes/**: HTTP endpoint handlers (health, webhook, manual review)
- **src/ai_code_reviewer/core/review_engine.py**: Review processing orchestration
- **src/ai_code_reviewer/core/config.py**: Configuration management and validation
- **src/ai_code_reviewer/core/email_formatter.py**: HTML email formatting
- **src/ai_code_reviewer/clients/bitbucket_client.py**: Bitbucket API integration
- **src/ai_code_reviewer/clients/llm_client.py**: LLM provider abstraction (OpenAI/Ollama)
- **src/ai_code_reviewer/clients/email_client.py**: Email sending via Azure Logic Apps

### Key Integrations
1. **Webhook Processing**: Receives Bitbucket webhooks (PR opened/updated, commits pushed), validates signatures, triggers async review
2. **Review Pipeline**: Fetches diff from Bitbucket → Sends to LLM with structured prompt → Parses response → Sends HTML email to author
3. **Email Notifications**: Uses Azure Logic Apps to send formatted HTML email notifications to commit/PR authors
4. **LLM Providers**: Supports OpenAI (cloud) and Ollama (local) with provider abstraction in LLMClient

### API Endpoints
- `/health`: Comprehensive health check (Bitbucket connectivity, LLM status)
- `/webhook/code-review`: Webhook receiver for Bitbucket events
- `/manual-review`: Manual review trigger endpoint

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

## Testing Strategy
- Unit tests in `tests/unit/` directory for isolated component testing
- Integration tests in `tests/integration/` for end-to-end API testing
- Shared pytest fixtures in `tests/conftest.py`
- Comprehensive test runner in `scripts/run_tests.py` that validates all functionality
- Mock-based testing for external API calls (Bitbucket, LLM providers)
- Coverage reporting with HTML output in `htmlcov/`
- Target coverage: 80%+

## Code Standards
- Python 3.12+ with type hints
- Formatting: Black (120 char line length)
- Linting: Ruff with comprehensive rules (configured in pyproject.toml)
- Type checking: MyPy with gradual typing
- Async/await for non-blocking operations
- Structured logging with appropriate log levels