# Development Guide

## Getting Started

### Prerequisites

- Python 3.12+
- uv (Python package manager) or pip
- Git
- Docker and Docker Compose (optional, for containerized development)

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai_code_reviewer
   ```

2. **Install dependencies**:
   ```bash
   # Using Makefile (recommended)
   make install-dev

   # Or manually with uv
   uv sync
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run tests to verify setup**:
   ```bash
   make test
   ```

## Project Structure

See [architecture.md](architecture.md) for detailed information about the codebase organization.

## Development Workflow

### Running the Development Server

```bash
# Using Makefile
make dev

# Or directly
python -m ai_code_reviewer.main
```

The server will start at `http://localhost:8000` with auto-reload disabled by default.

### Running Tests

```bash
# All tests with coverage
make test

# Specific test modules
pytest tests/unit/test_config.py -v
pytest tests/integration/test_api.py -v

# Fast tests without coverage
make test-fast

# With coverage report
make test-coverage
```

### Code Quality

```bash
# Run all linting with auto-fix
make lint
./scripts/lint.sh

# Check without modifications
./scripts/lint.sh --check-only

# Individual tools
ruff check .           # Linting
black .                # Formatting
mypy src/              # Type checking
```

### Docker Development

```bash
# Build and run
make docker-build
make docker-run

# With local LLM
make docker-run-local

# View logs
make docker-logs

# Stop containers
make docker-stop
```

## Making Changes

### Adding New API Endpoints

1. Create route handler in `src/ai_code_reviewer/api/routes/`
2. Register router in `src/ai_code_reviewer/api/app.py`
3. Add tests in `tests/integration/`

Example:
```python
# src/ai_code_reviewer/api/routes/new_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint():
    return {"status": "ok"}
```

```python
# src/ai_code_reviewer/api/app.py
from ai_code_reviewer.api.routes import new_feature

def create_app():
    app = FastAPI(...)
    app.include_router(new_feature.router, tags=["new"])
    return app
```

### Adding New LLM Providers

1. Extend `src/ai_code_reviewer/clients/llm_client.py`
2. Add configuration in `src/ai_code_reviewer/core/config.py`
3. Update tests in `tests/unit/test_llm_client.py`

### Modifying Review Logic

Business logic lives in `src/ai_code_reviewer/core/`:
- `review_engine.py` - Review orchestration
- `email_formatter.py` - Email formatting
- `config.py` - Configuration and prompts

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution

### Integration Tests (`tests/integration/`)
- Test API endpoints end-to-end
- Use test fixtures for data
- May involve external service mocks

### Test Fixtures (`tests/fixtures/`)
- Shared test data
- Mock responses
- Reusable test utilities

### Running Specific Tests

```bash
# By category
pytest -m unit
pytest -m integration

# By file
pytest tests/unit/test_config.py

# By test name
pytest tests/unit/test_config.py::test_validate_config -v
```

## Common Development Tasks

### Updating Dependencies

```bash
# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

### Database Migrations (Future)

If database support is added:
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### Environment Variables

Required for local development:
```bash
BITBUCKET_URL=https://your-bitbucket-server.com
BITBUCKET_TOKEN=your_token
LLM_PROVIDER=openai
LLM_API_KEY=your_key
LOGIC_APP_EMAIL_URL=your_logic_app_url
EMAIL_OPTOUT=true  # Disable emails during development
```

### Debugging

1. **Enable debug logging**:
   ```bash
   LOG_LEVEL=DEBUG python -m ai_code_reviewer.main
   ```

2. **Use Python debugger**:
   ```python
   import pdb; pdb.set_trace()
   ```

3. **Check health endpoints**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/health/detailed
   ```

## Code Style Guidelines

1. **Follow PEP 8** - Enforced by ruff and black
2. **Type hints** - Use type annotations for all functions
3. **Docstrings** - Document public functions and classes
4. **Line length** - 120 characters maximum
5. **Imports** - Organized automatically by ruff
6. **Async/await** - Use for all I/O operations

## Git Workflow

1. Create feature branch from `main`
2. Make changes with atomic commits
3. Run tests and linting: `make ci`
4. Create pull request
5. Address review feedback
6. Merge when approved

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running from the project root:
```bash
python -m ai_code_reviewer.main
```

Not:
```bash
cd src && python main.py  # ❌ Wrong
```

### Test Failures

1. Check environment variables are set
2. Verify dependencies are installed: `uv sync`
3. Clear pytest cache: `rm -rf .pytest_cache`
4. Check for conflicting ports (8000)

### Linting Failures

1. Run auto-fix: `./scripts/lint.sh`
2. Check specific issues: `ruff check . --show-fixes`
3. Format code: `black .`

## Contributing

See [Contributing Guidelines](../CONTRIBUTING.md) for information about:
- Code review process
- Commit message conventions
- Pull request templates
- Issue reporting
