# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
AI-powered code review agent for Bitbucket Enterprise Server that automatically reviews pull requests and commits using LLMs (OpenAI GPT-4, local Ollama). The agent sends intelligent code review feedback via email notifications to commit/PR authors using Azure Logic Apps integration.

## Repository Structure

```
src/ai_code_reviewer/        # Main application package
├── api/                     # Backend application
│   ├── main.py             # Application entry point
│   ├── app.py              # FastAPI app initialization
│   ├── dependencies.py     # Dependency injection
│   ├── routes/             # API route handlers
│   │   ├── health.py       # Health check endpoints
│   │   ├── webhook.py      # Webhook handlers
│   │   ├── manual.py       # Manual review endpoints (diff upload, manual trigger)
│   │   ├── reviews.py      # Review retrieval endpoints
│   │   └── failures.py     # Failure log endpoints
│   ├── core/               # Core business logic
│   │   ├── config.py       # Configuration management
│   │   ├── review_engine.py # Review processing orchestration
│   │   └── email_formatter.py # Email HTML formatting
│   ├── clients/            # External API clients
│   │   ├── bitbucket_client.py # Bitbucket API integration
│   │   ├── llm_client.py   # LLM provider abstraction
│   │   └── email_client.py # Email sending via Logic Apps
│   ├── db/                 # Database layer
│   │   ├── models.py       # SQLAlchemy models for review records
│   │   ├── database.py     # Database configuration and session management
│   │   └── repository.py   # Data access layer for review operations
│   └── frontend/           # React frontend application
│       ├── src/
│       │   ├── components/ # React components
│       │   │   ├── Layout/ # Header, Tabs, Layout
│       │   │   ├── DiffUpload/ # Tab 1: Diff file upload
│       │   │   ├── ManualReview/ # Tab 2: Manual review trigger
│       │   │   ├── ReviewsTable/ # Tab 3: Successful reviews
│       │   │   ├── FailuresTable/ # Tab 4: Failed reviews
│       │   │   └── SystemInfo/ # Tab 5: System configuration
│       │   ├── services/   # API client
│       │   ├── theme/      # Material-UI theme
│       │   ├── types/      # TypeScript types
│       │   ├── App.tsx     # Main app component
│       │   └── main.tsx    # Entry point
│       ├── package.json    # Frontend dependencies
│       └── vite.config.ts  # Vite configuration

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
# Install production dependencies AND package (recommended - using uv)
make install
# Or manually:
uv sync --no-dev && uv pip install -e .

# Or install with pip
pip install -e .

# Install development dependencies (includes testing, linting, security tools)
make install-dev
# Or manually:
uv pip install -e ".[dev]"
# Or: pip install -e ".[dev]"

# Install specific dependency groups
pip install -e ".[test]"  # Testing only
pip install -e ".[lint]"  # Linting only

# IMPORTANT: The -e flag installs the package in "editable" mode
# This allows the module to be imported (import ai_code_reviewer)
# Without -e or uv pip install, only dependencies are installed
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
make lint                  # Backend Python linting
make frontend-lint         # Frontend TypeScript/React linting
make ci                    # Full CI pipeline (lint + test)

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

#### Backend Only
```bash
# Run the FastAPI server locally (recommended - uses module syntax)
python -m ai_code_reviewer.api.main

# Or using Makefile
make dev

# With environment variables
export BITBUCKET_URL=https://your-bitbucket.com
export BITBUCKET_TOKEN=your_token
export LLM_API_KEY=your_api_key
python -m ai_code_reviewer.api.main
```

#### Frontend Only
```bash
# Navigate to frontend directory
cd src/ai_code_reviewer/api/frontend

# Install dependencies (first time only)
npm install

# Run development server (with hot reload)
npm run dev

# Frontend will be available at http://localhost:3000
# API proxy configured in vite.config.ts to forward /api/* to http://localhost:8000
```

#### Full Stack Development
```bash
# Terminal 1: Run backend
python -m ai_code_reviewer.api.main

# Terminal 2: Run frontend
cd src/ai_code_reviewer/api/frontend && npm run dev

# Access the application:
# - Frontend UI: http://localhost:3000
# - Backend API: http://localhost:8000
# - API docs: http://localhost:8000/docs
```

### Docker

#### Quick Start
```bash
# 1. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 2. Build and run (production mode)
make docker-build
make docker-run

# 3. Access the application
# - Frontend UI: http://localhost:3000
# - Backend API: http://localhost:8000
# - API docs: http://localhost:8000/docs
```

#### Development vs Production

**Production Mode** (recommended):
```bash
make docker-run
# Database: Docker named volume (docker_db_data)
# Logging: Docker logs (stdout/stderr with auto-rotation)
# Access logs: docker logs -f <container-id>
```

**Development Mode** (easy database access):
```bash
make docker-run-dev
# Database: ./data/ai_code_reviewer_dev.db (accessible from workspace)
# Logging: Docker logs (same as production)
# Useful for: Debugging, inspecting DB with SQLite Browser
```

#### Database Management

```bash
# Backup database from running container
make docker-backup
# Saves to: ./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db

# Restore database from backup (interactive)
make docker-restore
# Shows list of available backups to choose from

# Restore specific backup (non-interactive)
bash scripts/docker-restore.sh --file backups/ai_code_reviewer_20251110_164931.db --yes

# Safe upgrade with automatic backup
make docker-upgrade
# Automatically: backup → rebuild → migrate → restart

# Export logs to file
make docker-logs-export
# Saves to: ./logs/docker_logs_YYYYMMDD_HHMMSS.log
```

#### Other Commands

```bash
# View real-time logs
make docker-logs

# Run with local Ollama LLM
make docker-run-local

# Stop containers (keeps database)
make docker-stop

# Clean everything (⚠️ DELETES DATABASE)
make docker-clean
```

#### Architecture Notes

- **Single Container**: nginx (frontend) + uvicorn (backend) managed by supervisord
- **Database**: SQLite with persistent Docker volume or bind mount (dev mode)
- **Migrations**: Alembic runs automatically on container startup
- **Logging**: Docker-native logging with automatic rotation (10MB max, 3 files)
- **Cross-Platform**: Works identically on Mac/Linux/Windows (LF line endings enforced)

#### Advanced

See detailed guides:
- **Quick Start**: [docker/README.md](docker/README.md)
- **Comprehensive Guide**: [docs/DOCKER.md](docs/DOCKER.md)
- **Database Management**: [docs/DATABASE.md](docs/DATABASE.md)

## Architecture

### Layered Architecture
The application follows a clean layered architecture with separated frontend and backend:

**Backend (`src/ai_code_reviewer/api/`):**
1. **API Layer** (`routes/`): FastAPI routes, request/response handling
2. **Core Layer** (`core/`): Business logic, review orchestration, configuration
3. **Client Layer** (`clients/`): External service integrations (Bitbucket, LLM, Email)
4. **Database Layer** (`db/`): SQLAlchemy models, database operations, review record persistence

**Frontend (`src/ai_code_reviewer/api/frontend/`):**
1. **Components** (`src/components/`): React UI components organized by feature
   - Layout: Header, navigation tabs
   - DiffUpload: Tab 1 - File upload and review
   - ManualReview: Tab 2 - Manual review trigger
   - ReviewsTable: Tab 3 - Successful reviews with pagination
   - FailuresTable: Tab 4 - Failed reviews with pagination
   - SystemInfo: Tab 5 - System health and status
2. **Services** (`src/services/`): API client using Axios
3. **Theme** (`src/theme/`): Material-UI theme with Intel blue colors
4. **Types** (`src/types/`): TypeScript type definitions

### Core Components

**Backend:**
- **src/ai_code_reviewer/api/main.py**: Application entry point
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
- Type checking: MyPy with gradual typing (includes type stubs for external libraries)
- Security scanning: Bandit (code) and Safety (dependencies)
- Pre-commit hooks: Available for automated quality checks
- Async/await for non-blocking operations
- Structured logging with appropriate log levels
- Environment configuration: python-dotenv for .env file loading
- Frontend: TypeScript 5.9+, ESLint 8.x with @typescript-eslint v8.x, React 18+

## Security Considerations

**Current Security Posture**: Several security features are intentionally disabled for development convenience but **MUST** be enabled before production deployment:

- **Webhook signature verification**: Commented out in `webhook.py:53-56`
- **SSL certificate verification**: Disabled for Bitbucket in `bitbucket_client.py:31,53`
- **CORS policy**: Allows all origins in `app.py:68-74` (permissive)
- **Rate limiting**: Not implemented on any endpoints
- **API authentication**: No authentication required

**When making changes:**
- Do not introduce additional security vulnerabilities
- Document any new security trade-offs in code comments
- Follow OWASP Top 10 best practices
- Validate all user inputs at system boundaries (API endpoints, webhook handlers)
- Use parameterized queries exclusively (never raw SQL)
- Sanitize HTML output in frontend (use `rehype-sanitize` for ReactMarkdown)
- Avoid storing sensitive data in logs (redact tokens, passwords, PII)
- Test security fixes thoroughly before committing

**See**: README.md Security Warning section and security audit documentation for detailed remediation steps.

## Recent Fixes and Improvements

### Module Structure Refactoring (2025-01)
- **Relocated core modules**: Moved from `ai_code_reviewer.core.*` to `ai_code_reviewer.api.core.*`
- **Updated all imports**: Fixed import paths in test files and source code
- **Added app instance**: Created `app` instance in `app.py` for proper FastAPI initialization
- All tests now passing with correct import structure

### Type Checking Enhancements
- **Added type stubs**: Installed `types-requests>=2.31.0` for proper MyPy type checking
- **Fixed TypeScript types**: Created `vite-env.d.ts` for Vite environment variable types
- **Upgraded TypeScript ESLint**: Updated to `@typescript-eslint` v8.x for TypeScript 5.9 compatibility
- Zero type errors across Python and TypeScript codebases

### Docker Build Fixes
- **Fixed .dockerignore**: Updated to allow `nginx.conf` and `supervisord.conf` while excluding logs
- **Resolved npm dependencies**: Changed from `npm ci --only=production` to `npm ci` to include optional dependencies needed for Rollup on Alpine Linux (ARM64)
- **Multi-stage build optimized**: Frontend builds successfully in Docker with all required dependencies
- Docker build now passes consistently

### Frontend Linting Setup
- **Created ESLint config**: Added `.eslintrc.cjs` with TypeScript + React configuration
- **Fixed linting errors**: Corrected code quality issues (prefer-const, unused variables)
- **Version compatibility**: Resolved TypeScript/ESLint version mismatch warnings
- Frontend linting now fully functional with zero warnings

### Test Suite Status
All 6 test categories passing (100% success rate):
- ✅ Dependency Installation
- ✅ Configuration Validation
- ✅ Client Modules
- ✅ Unit Tests (78 tests)
- ✅ Code Linting (Python + Frontend)
- ✅ Docker Build

## Troubleshooting

### Common Issues and Solutions

**Issue: `make dev` fails with "ModuleNotFoundError: No module named 'ai_code_reviewer'"**
- **Root Cause**: The package hasn't been installed in the Python environment yet
- **Common Mistake**: Running only `uv sync` installs dependencies but NOT the package itself
- **Solution**: Run one of these commands to install the package:
  ```bash
  make setup           # Complete first-time setup (recommended)
  make install-dev     # Install development dependencies + package
  make install         # Install production dependencies + package
  pip install -e .     # Install package in editable mode
  uv pip install -e .  # Install with uv (faster)
  ```
- **Why `-e` is needed**: Editable mode creates a link so Python can import the module without copying files
- **Quick Test**: After installation, verify with `python -c "import ai_code_reviewer"`
- **Note**: The Makefile now checks for this automatically and provides a helpful error message

**Issue: `make test` fails with import errors**
- **Solution**: Import paths were updated to use `ai_code_reviewer.api.core.*` instead of `ai_code_reviewer.core.*`. Ensure all imports follow the new structure.

**Issue: MyPy complains about missing type stubs**
- **Solution**: Install type stubs with `uv pip install types-requests` or run `uv pip install -e ".[dev]"` to get all dev dependencies including type stubs.

**Issue: Docker build fails with "Cannot find module @rollup/rollup-linux-arm64-musl"**
- **Solution**: Use `npm ci` instead of `npm ci --only=production` to include optional dependencies needed for platform-specific builds.

**Issue: Frontend lint shows TypeScript version warning**
- **Solution**: Upgrade `@typescript-eslint` packages to v8.x which supports TypeScript 5.9+. This is now included in package.json.

**Issue: ESLint can't find configuration file**
- **Solution**: Ensure `.eslintrc.cjs` exists in the frontend directory. The file is now included in the repository.

**Issue: Docker container starts but environment variables are not loaded**
- **Root Cause**: The `.env` file is missing or not being loaded by docker-compose
- **Solution (Linux/Mac)**:
  ```bash
  # Create .env file from example
  cp .env.example .env

  # Edit with your configuration
  vim .env  # or nano, code, etc.

  # Rebuild and restart
  make docker-stop
  make docker-build
  make docker-run
  ```
- **Verification**: Check container logs for your configuration values
  ```bash
  make docker-logs | grep "BITBUCKET_URL\|LLM_PROVIDER"
  ```
- **Note**: Line endings are automatically enforced as LF by `.gitattributes` (works on all platforms)

**Issue: Webhook received but review not triggered**
- **Root Cause**: Webhook payload format may not match expected structure
- **Solution**: Check webhook event type and payload structure
  - PR events: `pr:opened`, `pr:from_ref_updated`
  - Commit events: `repo:refs_changed`
  - Payload structures differ significantly between event types
  - See [Webhook Payload Documentation](../docs/webhook-payloads.md) for detailed payload formats and field mappings
- **Debug**: Check application logs for `"Unsupported event key"` or `"Missing required fields"` errors
- **Verification**: Test webhook delivery in Bitbucket settings and verify payload matches expected format
