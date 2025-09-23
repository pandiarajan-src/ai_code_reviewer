# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
AI-powered code review agent for Bitbucket Enterprise Server that automatically reviews pull requests and commits using LLMs (OpenAI GPT-4, local Ollama).

## Key Commands

### Testing
```bash
# Run all tests with coverage
python run_tests.py

# Run specific test modules
pytest tests/test_config.py -v
pytest tests/test_bitbucket_client.py -v
pytest tests/test_llm_client.py -v
pytest tests/test_main.py -v

# Run tests with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
```

### Code Quality
```bash
# Run comprehensive linting (ruff, black, mypy) with auto-fix
./lint.sh

# Check code without modifications
./lint.sh --check-only

# Run linting without auto-fix
./lint.sh --no-fix
```

### Development Server
```bash
# Run the FastAPI server locally
python main.py

# With environment variables
export BITBUCKET_URL=https://your-bitbucket.com
export BITBUCKET_TOKEN=your_token
export LLM_API_KEY=your_api_key
python main.py
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose up -d

# For local LLM with Ollama
docker-compose --profile local-llm up -d

# View logs
docker-compose logs -f ai-code-reviewer
```

## Architecture

### Core Components
- **main.py**: FastAPI application entry point, webhook handlers, API endpoints
- **bitbucket_client.py**: Bitbucket Enterprise API integration for fetching diffs and posting comments
- **llm_client.py**: LLM provider abstraction supporting OpenAI and Ollama
- **config.py**: Configuration management and validation, contains review prompt templates

### Key Integrations
1. **Webhook Processing**: Receives Bitbucket webhooks (PR opened/updated, commits pushed), validates signatures, triggers async review
2. **Review Pipeline**: Fetches diff from Bitbucket → Sends to LLM with structured prompt → Parses response → Posts as PR comment
3. **LLM Providers**: Supports OpenAI (cloud) and Ollama (local) with provider abstraction in LLMClient

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

## Testing Strategy
- Unit tests in `tests/` directory with pytest fixtures in `conftest.py`
- Comprehensive test runner in `run_tests.py` that validates all functionality
- Mock-based testing for external API calls (Bitbucket, LLM providers)
- Coverage reporting with HTML output in `htmlcov/`

## Code Standards
- Python 3.12+ with type hints
- Formatting: Black (120 char line length)
- Linting: Ruff with comprehensive rules (configured in pyproject.toml)
- Type checking: MyPy with gradual typing
- Async/await for non-blocking operations
- Structured logging with appropriate log levels