# Development Guide

## Getting Started

### Prerequisites

- Python 3.12+
- uv (Python package manager, recommended) or pip
- Git
- Docker and Docker Compose (optional, for containerized development)
- Pre-commit (optional, for automated code quality checks)

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
   uv pip install -e ".[dev]"

   # Or with pip
   pip install -e ".[dev]"

   # Install specific dependency groups
   pip install -e ".[test]"   # Testing tools only
   pip install -e ".[lint]"   # Linting tools only
   pip install -e ".[docker]" # Docker/production extras
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

# Security scanning
make security-check    # Bandit code security scan
make security-deps     # Safety dependency vulnerability check

# Pre-commit hooks (optional but recommended)
pre-commit install              # Install git hooks
pre-commit run --all-files      # Run all checks manually
make pre-commit-run             # Alternative using Makefile
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

Dependencies are managed via `pyproject.toml` with optional groups (dev, test, lint, docker).

```bash
# Edit pyproject.toml to add dependencies, then:
uv sync                # Sync all dependencies

# Or with pip (after editing pyproject.toml)
pip install -e ".[dev]"

# Update all dependencies
uv sync --upgrade

# Update specific package
pip install --upgrade package-name
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
2. **Type hints** - Use type annotations for all functions (checked by MyPy)
3. **Docstrings** - Document public functions and classes
4. **Line length** - 120 characters maximum
5. **Imports** - Organized automatically by ruff
6. **Async/await** - Use for all I/O operations
7. **Security** - Document exceptions with `#nosec` comments
8. **Testing** - Maintain 80%+ code coverage
9. **Configuration** - Use pyproject.toml for all tool configurations

## Git Workflow

1. Create feature branch from `main`
2. Make changes with atomic commits
3. Run tests and linting: `make ci`
4. Create pull request
5. Address review feedback
6. Merge when approved

## Recent Updates (January 2025)

### Module Restructuring
- Core modules moved from `ai_code_reviewer.core.*` to `ai_code_reviewer.api.core.*`
- Entry point now at `src/ai_code_reviewer/api/main.py`
- Run server with: `python -m ai_code_reviewer.api.main`
- All import paths updated in tests and source code

### Frontend Integration
- React frontend now integrated at `src/ai_code_reviewer/api/frontend/`
- Frontend linting with ESLint + TypeScript support
- Run frontend: `cd src/ai_code_reviewer/api/frontend && npm run dev`
- Full stack dev: `make dev` (runs both backend and frontend)

### Type Safety Improvements
- Added `types-requests` for MyPy type checking
- Created `vite-env.d.ts` for Vite environment types
- Upgraded `@typescript-eslint` to v8.x for TypeScript 5.9+
- Zero type errors across Python and TypeScript

### Docker Improvements
- Multi-stage build with frontend + backend
- Fixed `.dockerignore` for proper config file inclusion
- Resolved ARM64 Alpine npm dependency issues
- Full Docker build now passing

## Troubleshooting

### Import Errors

**Updated module structure**: Use the new import paths:
```bash
# Correct - new structure
python -m ai_code_reviewer.api.main
from ai_code_reviewer.api.core.config import Config

# Wrong - old structure
python -m ai_code_reviewer.main  # ❌ Outdated
from ai_code_reviewer.core.config import Config  # ❌ Outdated
```

Ensure you're running from the project root with the new module path.

### Test Failures

1. Check environment variables are set (copy `.env.example` to `.env`)
2. Verify dependencies are installed: `uv pip install -e ".[dev]"` or `pip install -e ".[dev]"`
3. Ensure type stubs installed: Type stubs like `types-requests` are included in dev dependencies
4. Clear pytest cache: `rm -rf .pytest_cache`
5. Check for conflicting ports (8000 for backend, 3000 for frontend)
6. Ensure you're running from project root: `python -m ai_code_reviewer.api.main`

### Linting Failures

**Backend (Python)**
1. Run auto-fix: `./scripts/lint.sh` or `make lint`
2. Check specific issues: `ruff check . --show-fixes`
3. Format code: `black .`
4. Type check: `mypy src/ --ignore-missing-imports`

**Frontend (TypeScript)**
1. Run linting: `make frontend-lint`
2. Fix issues: `cd src/ai_code_reviewer/api/frontend && npm run lint`
3. ESLint config at: `src/ai_code_reviewer/api/frontend/.eslintrc.cjs`

### Docker Build Failures

1. Ensure config files exist: `docker/nginx.conf` and `docker/supervisord.conf`
2. Check `.dockerignore` allows config files but excludes logs
3. For ARM64 platforms: Use `npm ci` (not `npm ci --only=production`)
4. Frontend requires all dev dependencies for build: TypeScript, Vite, ESLint

## Contributing

See [Contributing Guidelines](../CONTRIBUTING.md) for information about:
- Code review process
- Commit message conventions
- Pull request templates
- Issue reporting
