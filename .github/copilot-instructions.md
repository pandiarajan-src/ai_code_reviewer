# AI Code Reviewer - Copilot Instructions

This is a webhook-driven FastAPI application that provides AI-powered code reviews for Bitbucket Enterprise Server. The agent automatically analyzes pull requests and commits, posting intelligent feedback using configurable LLM providers.

## Architecture Overview

The application follows a 3-tier webhook architecture:
- **FastAPI Web Server** (`main.py`) - Handles webhooks and provides API endpoints
- **Bitbucket Client** (`bitbucket_client.py`) - Fetches diffs and posts comments via REST API
- **LLM Client** (`llm_client.py`) - Integrates with OpenAI or local Ollama for code analysis

Key data flow: Bitbucket webhook → fetch diff → send to LLM → post review comment.

## Code Patterns & Conventions

### Configuration Management
All config is centralized in `config.py` using environment variables with defaults:
```python
BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")  # Required
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # 'openai' or 'local_ollama'
```
- Use `Config.validate_config()` to ensure required vars are set
- Templates like `REVIEW_PROMPT_TEMPLATE` are configurable in config.py

### Async HTTP Client Pattern
Both `bitbucket_client.py` and `llm_client.py` follow the same pattern:
```python
async def _make_request(self, method: str, endpoint: str, **kwargs):
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        response = await client.request(method, url, headers=self.headers, **kwargs)
```
- Always use async/await for HTTP calls
- Include proper timeout values (30s for Bitbucket, 60-120s for LLM)
- Handle both JSON and text responses with separate methods

### Webhook Event Processing
Main webhook handler processes events via background tasks:
```python
@app.post("/webhook/code-review")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    if event_key in ["pr:opened", "pr:modified", "pr:from_ref_updated"]:
        background_tasks.add_task(process_pull_request_review, payload)
```
- Use FastAPI `BackgroundTasks` for async processing
- Verify webhook signatures with `verify_webhook_signature()`
- Log all webhook events for debugging

### Error Handling & Logging
Consistent error handling across all modules:
```python
try:
    # Operation
    logger.info(f"Success message with {details}")
except Exception as e:
    logger.error(f"Error context: {str(e)}")
    return None  # or appropriate fallback
```
- Use structured logging with context (PR ID, commit hash, etc.)
- Return `None` for failures, check for `None` before proceeding
- Never raise exceptions from background tasks

## Development Workflows

### Testing
Run comprehensive test suite with `python run_tests.py`:
- **Unit Tests**: `pytest tests/ -v --cov=.` for coverage reporting
- **Integration Tests**: Mocked FastAPI TestClient in `tests/test_main.py`
- **Docker Build**: Validates containerization
- **Configuration**: Tests env var validation and defaults

### Code Quality
Use `./lint.sh` for comprehensive code linting:
- **Ruff**: Fast linting and import sorting with auto-fix
- **Black**: Code formatting for consistent style
- **MyPy**: Static type checking
- **Config**: Centralized in `pyproject.toml`

Test fixtures in `conftest.py` provide mocked clients and sample payloads.

### Local Development
```bash
# Set up environment
cp .env.example .env  # Edit with test values
pip install -r requirements.txt -r test_requirements.txt

# Run locally
python main.py  # Starts on localhost:8000

# Test endpoints
curl http://localhost:8000/health
```

### Docker Development
```bash
# Standard deployment
docker-compose up -d

# With local Ollama
docker-compose --profile local-llm up -d
```

## LLM Provider Integration

### Adding New Providers
Extend `LLMClient` class with provider-specific methods:
```python
async def _test_provider_connection(self) -> Dict[str, Any]:
    # Test connectivity and return status

async def _get_provider_review(self, prompt: str) -> Optional[str]:
    # Send prompt and return review text
```
Update `get_code_review()` and `test_connection()` to handle new provider.

### Prompt Engineering
Modify `REVIEW_PROMPT_TEMPLATE` in `config.py`:
- Focus on specific review criteria (bugs, security, performance)
- Include context about diff format and expected output
- Use `{diff_content}` placeholder for dynamic content

## Deployment Considerations

### Environment-Specific Config
- **Development**: Use `.env` file with test credentials
- **Production**: Set environment variables in container/k8s
- **Security**: Never commit real tokens; use secrets management

### Health Monitoring
The `/health` endpoint validates:
- Configuration completeness via `Config.validate_config()`
- Bitbucket connectivity via `bitbucket_client.test_connection()`
- LLM provider connectivity via `llm_client.test_connection()`

### Bitbucket Webhook Setup
Webhook must be configured for these events:
- `pr:opened`, `pr:modified`, `pr:from_ref_updated` (pull requests)
- `repo:refs_changed` (commits/pushes)

Point to: `http://your-server:8000/webhook/code-review`

## Common Integration Points

### Manual Review API
```bash
POST /manual-review
{
  "project_key": "PROJ",
  "repo_slug": "repository",
  "pr_id": 123  # OR "commit_id": "abc123"
}
```

### Extending Functionality
- **Custom Review Logic**: Modify prompt templates or add preprocessing in `llm_client.py`
- **Additional Webhooks**: Add new event handlers in `main.py` webhook processor
- **Different Comment Formats**: Customize comment formatting in `process_*_review()` functions

## File Organization
- `main.py` - FastAPI app, webhook handlers, API endpoints
- `config.py` - Environment-based configuration management
- `bitbucket_client.py` - Bitbucket Enterprise Server API client
- `llm_client.py` - Multi-provider LLM integration
- `tests/` - Comprehensive test suite with mocks and fixtures
- `docker-compose.yml` - Multi-service deployment config
- `run_tests.py` - Custom test runner with dependency validation

Focus on webhook reliability, async processing, and proper error handling when making changes.
