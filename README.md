# AI Code Reviewer Agent

A comprehensive AI-powered code review agent for Bitbucket Enterprise Server that automatically reviews code changes in pull requests and commits using advanced language models and sends intelligent feedback via email notifications.

## Overview

This agent integrates seamlessly with your Bitbucket Enterprise Server to provide intelligent, automated code reviews. It supports both cloud-based LLMs (like OpenAI GPT-4) and local LLMs (like Ollama with Llama/Qwen-Coder models) for maximum flexibility and privacy control.

### Key Features

- **Automated Code Review**: Automatically reviews pull requests and commits when triggered by Bitbucket webhooks
- **Email Notifications**: Sends HTML-formatted review results directly to commit/PR authors via Azure Logic Apps
- **Review History Database**: Stores all review records with metadata for tracking and auditing
- **Multi-LLM Support**: Works with OpenAI GPT models, local Ollama instances, and other LLM providers
- **Comprehensive Analysis**: Focuses on bug detection, security vulnerabilities, performance issues, and best practices
- **Intelligent Routing**: Automatically extracts author email from commits/PRs for targeted notifications
- **Flexible Deployment**: Can run independently or alongside existing CI/CD infrastructure
- **Docker Ready**: Fully containerized with frontend + backend for easy deployment and scaling
- **Web UI**: React-based frontend for diff uploads, manual reviews, and viewing review history
- **Webhook Security**: Supports webhook signature verification for secure communication
- **Manual Triggers**: Provides API endpoints and web interface for manual code review requests
- **Review Retrieval APIs**: Query review history by project, author, commit, or PR
- **Health Monitoring**: Built-in health checks and monitoring endpoints
- **Type-Safe**: Full TypeScript frontend and Python type hints with MyPy validation

### Project Structure

The project follows a clean, modular architecture:

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
│       │   ├── main.tsx    # Entry point
│       │   └── vite-env.d.ts # Vite type definitions
│       ├── package.json    # Frontend dependencies
│       ├── vite.config.ts  # Vite configuration
│       └── .eslintrc.cjs   # ESLint configuration

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
├── Dockerfile             # Multi-stage container (frontend + backend)
├── docker-compose.yml     # Multi-container orchestration
├── nginx.conf             # Nginx configuration for frontend
└── supervisord.conf       # Supervisor configuration

docs/                       # Documentation
├── architecture.md        # System architecture
├── development.md         # Development guide
├── deployment.md          # Deployment instructions
└── project-summary.md     # Project overview
```

### Architecture

The agent follows a clean layered architecture with webhook-driven workflow:

1. **API Layer**: FastAPI routes for webhooks, health checks, and manual triggers
2. **Core Layer**: Business logic for review orchestration and email formatting
3. **Client Layer**: External service integrations (Bitbucket, LLM, Email)

**Workflow**:
1. Bitbucket sends webhook → API receives and validates
2. Review engine fetches code diff → Sends to LLM for analysis
3. LLM returns feedback → Format as HTML email
4. Send email to commit/PR author via Azure Logic Apps

## Quick Start

### Prerequisites

- Docker and Docker Compose (recommended for production)
- Python 3.12+ (for local development)
- uv package manager (recommended) or pip
- Bitbucket Enterprise Server with admin access
- OpenAI API key OR local Ollama installation
- Azure Logic App configured for email sending (or similar email service)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd ai_code_reviewer

# Copy and edit environment configuration
cp .env.example .env
# Edit .env with your actual configuration
```

### 2. Configure Environment Variables

Edit the `.env` file with your settings:

```bash
# Bitbucket Configuration
BITBUCKET_URL=https://your-bitbucket-server.com
BITBUCKET_TOKEN=your_bitbucket_access_token

# LLM Configuration (OpenAI)
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4o

# OR Local LLM Configuration (Ollama)
# LLM_PROVIDER=local_ollama
# OLLAMA_HOST=http://localhost:11434
# LLM_MODEL=qwen-coder

# Security
WEBHOOK_SECRET=your_webhook_secret

# Email Configuration (Azure Logic App)
LOGIC_APP_EMAIL_URL=https://your-logic-app-url
LOGIC_APP_FROM_EMAIL=noreply@yourcompany.com
EMAIL_OPTOUT=false
```

### 3. Deploy with Docker

```bash
# For OpenAI/Cloud LLM
docker-compose -f docker/docker-compose.yml up -d

# For local LLM with Ollama
docker-compose -f docker/docker-compose.yml --profile local-llm up -d

# Or use Makefile (recommended)
make docker-build
make docker-run
```

### 4. Configure Bitbucket Webhooks

1. Navigate to your repository settings in Bitbucket
2. Go to **Webhooks** and create a new webhook
3. Set URL to: `http://your-server:8000/webhook/code-review`
4. Select events: **Pull Request > Opened**, **Pull Request > Source updated**, **Repository > Push**
5. Add your webhook secret if configured
6. Save and enable the webhook

## Configuration Guide

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BITBUCKET_URL` | Your Bitbucket Enterprise Server URL | Yes | - |
| `BITBUCKET_TOKEN` | Bitbucket access token | Yes | - |
| `LLM_PROVIDER` | LLM provider (`openai` or `local_ollama`) | No | `openai` |
| `LLM_API_KEY` | OpenAI API key (if using OpenAI) | Conditional | - |
| `LLM_ENDPOINT` | LLM API endpoint | No | OpenAI default |
| `LLM_MODEL` | Model name | No | `gpt-4o` |
| `OLLAMA_HOST` | Ollama server URL (if using local LLM) | No | `http://localhost:11434` |
| `WEBHOOK_SECRET` | Secret for webhook verification | No | - |
| `LOGIC_APP_EMAIL_URL` | Azure Logic App HTTP trigger URL | Yes | - |
| `LOGIC_APP_FROM_EMAIL` | From email address for notifications | No | `pandiarajans@test.com` |
| `EMAIL_OPTOUT` | Disable email sending for testing | No | `true` |
| `HOST` | Server bind address | No | `0.0.0.0` |
| `BACKEND_PORT` | Backend API server port | No | `8000` |
| `FRONTEND_PORT` | Frontend UI server port | No | `3000` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `DATABASE_URL` | Database connection URL | No | `sqlite+aiosqlite:///./ai_code_reviewer.db` |
| `DATABASE_ECHO` | Enable SQL query logging | No | `false` |

### Bitbucket Token Setup

1. Log into Bitbucket as a service account user
2. Go to **Personal Settings > HTTP access tokens**
3. Create a new token with permissions:
   - **Repositories: Read**
   - **Pull requests: Write** (to post comments)
4. Copy the token to your `.env` file

### LLM Provider Configuration

#### OpenAI Configuration

```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4o  # or gpt-4, gpt-3.5-turbo
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
```

#### Local Ollama Configuration

```bash
LLM_PROVIDER=local_ollama
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=qwen-coder  # or llama3, codellama
```

For Ollama setup:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull your preferred model
ollama pull qwen-coder
ollama pull llama3
```

### Email Configuration

The agent uses Azure Logic Apps for email notifications. Configure your Logic App to:

#### Azure Logic App Setup
1. Create a new Logic App in Azure Portal
2. Configure HTTP trigger with POST method
3. Add Office 365 Outlook or SMTP connector
4. Configure email template to use request body parameters:
   - `to`: Recipient email address
   - `cc`: CC email address (optional)
   - `subject`: Email subject
   - `mailbody`: HTML email body

#### Environment Configuration
```bash
LOGIC_APP_EMAIL_URL=https://your-logic-app-url.azurewebsites.net/api/triggers/manual/invoke?code=your-code
LOGIC_APP_FROM_EMAIL=noreply@yourcompany.com
EMAIL_OPTOUT=false  # Set to true to disable emails for testing
```

## API Endpoints

### Health Check
- **GET** `/health` - Comprehensive health check including LLM and Bitbucket connectivity

### Webhook Handler
- **POST** `/webhook/code-review` - Handles Bitbucket webhook events

### Manual Review
- **POST** `/manual-review` - Manually trigger code review
  - Parameters: `project_key`, `repo_slug`, `pr_id` OR `commit_id`
  - Returns: Review result and database record ID

### Review History Retrieval

All review records are automatically saved to the database with complete metadata including:
- Date/time of review
- Review type (auto/manual)
- Trigger type (commit/pull_request)
- Project and repository information
- Commit ID or PR ID
- Author name and email
- Code diff content
- Review feedback
- Email recipients and delivery status
- LLM provider and model used

#### Available Endpoints:

- **GET** `/reviews/latest?limit=10` - Get last N review records
  - Query param: `limit` (1-100, default: 10)

- **GET** `/reviews?offset=0&limit=10` - Get paginated reviews
  - Query params: `offset` (starting record, default: 0), `limit` (1-100, default: 10)
  - Returns: Total count, offset, limit, and records

- **GET** `/reviews/{review_id}` - Get specific review by ID

- **GET** `/reviews/project/{project_key}?repo_slug=repo&limit=10` - Get reviews by project/repo
  - Query params: `repo_slug` (optional), `limit` (default: 10)

- **GET** `/reviews/author/{author_email}?limit=10` - Get reviews by author email
  - Query param: `limit` (default: 10)

- **GET** `/reviews/commit/{commit_id}` - Get all reviews for a specific commit

- **GET** `/reviews/pr/{pr_id}` - Get all reviews for a specific pull request

#### Example API Calls:

```bash
# Get last 5 reviews
curl http://localhost:8000/reviews/latest?limit=5

# Get reviews with pagination (records 10-19)
curl http://localhost:8000/reviews?offset=10&limit=10

# Get specific review by ID
curl http://localhost:8000/reviews/42

# Get reviews for a project
curl http://localhost:8000/reviews/project/PROJ?repo_slug=my-repo&limit=20

# Get reviews by author
curl http://localhost:8000/reviews/author/developer@company.com?limit=15

# Get reviews for a commit
curl http://localhost:8000/reviews/commit/abc123def456

# Get reviews for a PR
curl http://localhost:8000/reviews/pr/123
```

### Database Configuration

By default, the application uses SQLite for simplicity. You can configure a different database using the `DATABASE_URL` environment variable:

```bash
# SQLite (default)
DATABASE_URL=sqlite+aiosqlite:///./ai_code_reviewer.db

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost/ai_code_reviewer

# MySQL
DATABASE_URL=mysql+aiomysql://user:password@localhost/ai_code_reviewer
```

The database is automatically initialized on application startup. No manual migration is required for the initial setup.

### Database Management Script

A comprehensive database helper script is provided for development and testing:

```bash
# Create/initialize database
python scripts/db_helper.py create

# Reset database (drop and recreate all tables)
python scripts/db_helper.py reset

# Clean all records (keep schema)
python scripts/db_helper.py clean

# Show database statistics
python scripts/db_helper.py stats

# Seed test data for development
python scripts/db_helper.py seed

# List recent reviews
python scripts/db_helper.py list --limit 20

# Backup database (SQLite only)
python scripts/db_helper.py backup
python scripts/db_helper.py backup --file my_backup.db

# Restore from backup (SQLite only)
python scripts/db_helper.py restore --file my_backup.db
```

This script is particularly useful for:
- Setting up test data for API testing
- Resetting database between test runs
- Development and debugging
- Creating backups before major changes

### Docker Database Persistence

When running with Docker, the database is stored in a persistent volume:

```bash
# Start with Docker Compose (database persists across restarts)
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer

# Stop (data persists)
docker-compose -f docker/docker-compose.yml down

# Remove including database volume (CAUTION: deletes all data)
docker-compose -f docker/docker-compose.yml down -v
```

The database volume `db_data` persists the SQLite database file at `/app/data/ai_code_reviewer.db` inside the container. This ensures review history is retained across container restarts.

## Development

### Local Setup

```bash
# Install development dependencies (recommended - using uv)
uv pip install -e ".[dev]"

# Or using Makefile
make install-dev

# Or with pip
pip install -e ".[dev]"

# Install production dependencies only
uv sync --no-dev
# Or: pip install -r requirements.txt

# Install specific dependency groups
pip install -e ".[test]"  # Testing tools only
pip install -e ".[lint]"  # Linting tools only
```

### Testing

Run the comprehensive test suite:

```bash
# Run all tests
make test
# Or: python scripts/run_tests.py

# Run specific test categories
make test-unit        # Unit tests only
make test-integration # Integration tests only

# Run specific test modules
pytest tests/unit/test_config.py -v
pytest tests/unit/test_bitbucket_client.py -v
pytest tests/integration/test_main.py -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=html
```

### Code Quality & Linting

The project includes comprehensive linting and security tools for both backend and frontend code:

```bash
# Backend Python linting (ruff, black, mypy) with auto-fix
make lint
# Or: ./scripts/lint.sh

# Frontend TypeScript/React linting (ESLint)
make frontend-lint

# Full CI pipeline (lint + test)
make ci

# Check code quality without making changes
./scripts/lint.sh --check-only

# Run linting without auto-fix
./scripts/lint.sh --no-fix

# Type checking
make type-check

# Security scanning
make security-check       # Run Bandit security scan on code
make security-deps        # Check dependencies for vulnerabilities with Safety

# Pre-commit hooks (optional but recommended)
pre-commit install              # Install git hooks
pre-commit run --all-files      # Run all pre-commit checks manually
```

### Running Locally

#### Backend Only
```bash
# Start development server
make dev-backend
# Or: python -m ai_code_reviewer.api.main

# Backend API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

#### Frontend Only
```bash
# Navigate to frontend directory
cd src/ai_code_reviewer/api/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
# API proxy configured to forward /api/* to http://localhost:8000
```

#### Full Stack Development
```bash
# Terminal 1: Run backend
python -m ai_code_reviewer.api.main

# Terminal 2: Run frontend
cd src/ai_code_reviewer/api/frontend && npm run dev

# Or use Makefile to run both
make dev

# Access the application:
# - Frontend UI: http://localhost:3000
# - Backend API: http://localhost:8000
# - API docs: http://localhost:8000/docs
```

The development tools include:

**Backend:**
- **Ruff**: Fast Python linter and formatter (replaces flake8, isort)
- **Black**: Code formatter for consistent style (120 char line length)
- **MyPy**: Static type checking with gradual typing and type stubs
- **Bandit**: Security vulnerability scanner for Python code
- **Safety**: Dependency vulnerability checker
- **Pre-commit**: Git hooks for automated quality checks
- **pytest**: Testing framework with async support
- **pytest-cov**: Code coverage reporting (80%+ target)

**Frontend:**
- **TypeScript 5.9+**: Type-safe JavaScript with latest features
- **ESLint 8.x**: Linting with @typescript-eslint v8.x for TypeScript support
- **React 18+**: Modern React with hooks and concurrent features
- **Vite**: Fast build tool with hot module replacement
- **Material-UI**: Component library with Intel blue theme
- **Axios**: HTTP client for API communication

All tool configurations are centralized in `pyproject.toml` (backend) and `package.json` (frontend).

## Deployment Options

### Docker Deployment (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f ai-code-reviewer

# Update deployment
docker-compose pull && docker-compose up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-code-reviewer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-code-reviewer
  template:
    metadata:
      labels:
        app: ai-code-reviewer
    spec:
      containers:
      - name: ai-code-reviewer
        image: ai-code-reviewer:latest
        ports:
        - containerPort: 8000
        env:
        - name: BITBUCKET_URL
          value: "https://your-bitbucket-server.com"
        - name: BITBUCKET_TOKEN
          valueFrom:
            secretKeyRef:
              name: ai-code-reviewer-secrets
              key: bitbucket-token
        # Add other environment variables
```

### Standalone Deployment

```bash
# Install the package
pip install -e .

# Run directly using module syntax (recommended)
python -m ai_code_reviewer.main

# Or with environment file
cp .env.example .env
# Edit .env with your configuration
python -m ai_code_reviewer.main

# Production with gunicorn (installed via docker extras)
pip install -e ".[docker]"
gunicorn ai_code_reviewer.main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Monitoring and Troubleshooting

### Health Monitoring

The agent provides comprehensive health checks at `/health`:

```json
{
  "status": "healthy",
  "bitbucket": {"status": "connected", "version": "7.0.0"},
  "llm": {"status": "connected", "provider": "openai"},
  "config": {
    "bitbucket_url": "https://your-bitbucket-server.com",
    "llm_provider": "openai",
    "llm_model": "gpt-4o"
  }
}
```

### Common Issues

#### Webhook Not Triggering
- Verify webhook URL is accessible from Bitbucket server
- Check webhook configuration in Bitbucket repository settings
- Verify webhook secret matches configuration
- Check agent logs for incoming webhook requests

#### LLM Connection Issues
- For OpenAI: Verify API key and check rate limits
- For Ollama: Ensure Ollama service is running and model is pulled
- Check network connectivity between agent and LLM service

#### Bitbucket API Issues
- Verify Bitbucket token has correct permissions
- Check if token has expired
- Ensure agent can reach Bitbucket server URL

### Logging

The agent provides structured logging at multiple levels:

```bash
# View real-time logs
docker-compose logs -f ai-code-reviewer

# Filter by log level
docker-compose logs ai-code-reviewer | grep ERROR
docker-compose logs ai-code-reviewer | grep WARNING
```

## Security Considerations

### Webhook Security
- Always configure `WEBHOOK_SECRET` for production deployments
- Use HTTPS for webhook endpoints
- Implement network-level access controls

### Token Security
- Use dedicated service accounts with minimal required permissions
- Rotate tokens regularly
- Store tokens securely (environment variables, secrets management)

### Network Security
- Deploy agent in secure network segments
- Use TLS/SSL for all external communications
- Implement proper firewall rules

## Customization

### Review Prompt Customization

Edit `config.py` to customize the AI review prompt:

```python
REVIEW_PROMPT_TEMPLATE = """Your custom review instructions here...

Focus on:
- Your specific requirements
- Company coding standards
- Security policies

Here is the diff:
```
{diff_content}
```

Please provide your review:"""
```

### Adding New LLM Providers

Extend `llm_client.py` to support additional LLM providers:

```python
async def _get_custom_llm_review(self, prompt: str) -> Optional[str]:
    # Implement your custom LLM integration
    pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `uv pip install -e ".[dev]"` or `pip install -e ".[dev]"`
4. Make your changes
5. Run the test suite: `make test` or `python scripts/run_tests.py`
6. Run linting and security checks: `make lint && make security-check`
7. (Optional) Install pre-commit hooks: `pre-commit install`
8. Submit a pull request

### Development Standards

- Follow PEP 8 style guide (enforced by Ruff and Black)
- Add type hints to all functions (checked by MyPy)
- Write tests for new functionality (maintain 80%+ coverage)
- Document security exceptions with `#nosec` comments
- Update documentation for user-facing changes
- Use async/await for I/O operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Recent Updates

### January 2025

**Module Structure Refactoring**
- Reorganized core modules from `ai_code_reviewer.core.*` to `ai_code_reviewer.api.core.*`
- Updated all import paths across tests and source code
- Added proper `app` instance export in `app.py`
- All 78 unit and integration tests passing

**Type Safety Enhancements**
- Added `types-requests` for MyPy type checking of requests library
- Created `vite-env.d.ts` for Vite environment variable types
- Upgraded `@typescript-eslint` to v8.x for TypeScript 5.9 compatibility
- Zero type errors across Python and TypeScript codebases

**Docker Build Improvements**
- Fixed `.dockerignore` to properly include nginx and supervisor config files
- Resolved npm dependency issues for ARM64 Alpine Linux builds
- Multi-stage Docker build now fully functional
- Frontend and backend successfully containerized together

**Frontend Linting Setup**
- Created `.eslintrc.cjs` with TypeScript + React configuration
- Fixed all code quality issues (prefer-const, unused variables)
- Resolved TypeScript/ESLint version compatibility warnings
- Frontend linting now integrated into CI pipeline

**Test Suite Status**
- ✅ All 6 test categories passing (100% success rate)
- ✅ 78 unit and integration tests
- ✅ Backend linting (Ruff, Black, MyPy)
- ✅ Frontend linting (ESLint, TypeScript)
- ✅ Docker build and deployment
- ✅ Full CI pipeline operational

## Additional Documentation

For more detailed information:

- **[Architecture Guide](docs/architecture.md)** - System architecture and component design
- **[Development Guide](docs/development.md)** - Development setup and guidelines
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions
- **[Webhook Payloads](docs/webhook-payloads.md)** - Bitbucket webhook payload structures and examples
- **[Project Summary](docs/project-summary.md)** - High-level project overview
- **[CLAUDE.md](CLAUDE.md)** - AI coding assistant guidance and troubleshooting

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Consult the documentation in the `docs/` directory
4. Check **[CLAUDE.md](CLAUDE.md)** for common issues and solutions
5. Open an issue on the project repository
6. Contact your system administrator for deployment-specific issues
