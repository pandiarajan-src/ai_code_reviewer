# AI Code Reviewer Agent

A comprehensive AI-powered code review agent for Bitbucket Enterprise Server that automatically reviews code changes in pull requests and commits using advanced language models.

## Overview

This agent integrates seamlessly with your Bitbucket Enterprise Server to provide intelligent, automated code reviews. It supports both cloud-based LLMs (like OpenAI GPT-4) and local LLMs (like Ollama with Llama/Qwen-Coder models) for maximum flexibility and privacy control.

### Key Features

- **Automated Code Review**: Automatically reviews pull requests and commits when triggered by Bitbucket webhooks
- **Multi-LLM Support**: Works with OpenAI GPT models, local Ollama instances, and other LLM providers
- **Comprehensive Analysis**: Focuses on bug detection, security vulnerabilities, performance issues, and best practices
- **Flexible Deployment**: Can run independently or alongside existing CI/CD infrastructure
- **Docker Ready**: Fully containerized for easy deployment and scaling
- **Webhook Security**: Supports webhook signature verification for secure communication
- **Manual Triggers**: Provides API endpoints for manual code review requests
- **Health Monitoring**: Built-in health checks and monitoring endpoints

### Architecture

The agent follows a webhook-driven architecture:

1. **Webhook Listener**: Receives events from Bitbucket when code changes occur
2. **Bitbucket API Client**: Fetches code diffs and posts review comments
3. **LLM Integration**: Sends code to AI models for analysis and receives feedback
4. **Review Engine**: Processes AI responses and formats them for Bitbucket

## Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.12+ (for local development)
- Bitbucket Enterprise Server with admin access
- OpenAI API key OR local Ollama installation

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
```

### 3. Deploy with Docker

```bash
# For OpenAI/Cloud LLM
docker-compose up -d

# For local LLM with Ollama
docker-compose --profile local-llm up -d
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
| `HOST` | Server bind address | No | `0.0.0.0` |
| `PORT` | Server port | No | `8000` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

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

## API Endpoints

### Health Check
- **GET** `/health` - Comprehensive health check including LLM and Bitbucket connectivity

### Webhook Handler
- **POST** `/webhook/code-review` - Handles Bitbucket webhook events

### Manual Review
- **POST** `/manual-review` - Manually trigger code review
  - Parameters: `project_key`, `repo_slug`, `pr_id` OR `commit_id`

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all tests
python run_tests.py

# Run specific test categories
pytest tests/test_config.py -v
pytest tests/test_bitbucket_client.py -v
pytest tests/test_llm_client.py -v
pytest tests/test_main.py -v
```

### Code Quality & Linting

The project includes comprehensive linting tools for code quality:

```bash
# Install linting dependencies
pip install -r dev_requirements.txt

# Run comprehensive linting (ruff, black, mypy) with auto-fix
./lint.sh

# Check code quality without making changes
./lint.sh --check-only

# Run linting without auto-fix
./lint.sh --no-fix
```

The linting script uses:
- **Ruff**: Fast Python linter and formatter (replaces flake8, isort)
- **Black**: Code formatter for consistent style
- **MyPy**: Static type checking

Configuration is centralized in `pyproject.toml`.

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
# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Or with gunicorn for production
pip install gunicorn
gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4
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
3. Make your changes
4. Run the test suite: `python run_tests.py`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Open an issue on the project repository
4. Contact your system administrator for deployment-specific issues

