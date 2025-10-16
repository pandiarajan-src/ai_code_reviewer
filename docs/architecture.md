# Architecture

## Overview

The AI Code Reviewer follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│         Bitbucket Webhooks / Manual API     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            FastAPI Application Layer        │
│  - Health Check Routes                      │
│  - Webhook Handler Routes                   │
│  - Manual Review Routes                     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Core Business Logic Layer           │
│  - Review Engine (orchestration)            │
│  - Email Formatter (HTML conversion)        │
│  - Configuration Management                 │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          External Client Layer              │
│  - Bitbucket API Client                     │
│  - LLM Client (OpenAI/Ollama)              │
│  - Email Client (Azure Logic Apps)          │
└─────────────────────────────────────────────┘
```

## Directory Structure

```
src/ai_code_reviewer/
├── api/                    # FastAPI application layer
│   ├── app.py             # App initialization
│   ├── dependencies.py    # Dependency injection
│   └── routes/            # API route handlers
│       ├── health.py      # Health check endpoints
│       ├── webhook.py     # Webhook handlers
│       └── manual.py      # Manual review endpoints
├── core/                   # Core business logic
│   ├── config.py          # Configuration management
│   ├── review_engine.py   # Review processing orchestration
│   └── email_formatter.py # Email HTML formatting
├── clients/                # External API clients
│   ├── bitbucket_client.py
│   ├── llm_client.py
│   └── email_client.py
└── main.py                # Application entry point
```

## Component Details

### API Layer (`api/`)
- **Purpose**: Handle HTTP requests and responses
- **Responsibilities**:
  - Request validation and parsing
  - Route handling
  - Response formatting
  - Background task scheduling
- **Dependencies**: Core layer for business logic

### Core Layer (`core/`)
- **Purpose**: Business logic independent of web framework
- **Responsibilities**:
  - Review orchestration
  - Email formatting
  - Configuration management
  - Domain logic
- **Dependencies**: Client layer for external integrations

### Client Layer (`clients/`)
- **Purpose**: External service integrations
- **Responsibilities**:
  - Bitbucket API communication
  - LLM provider integration
  - Email sending via Logic Apps
  - API error handling
- **Dependencies**: Core configuration

## Data Flow

### Pull Request Review Flow

1. Bitbucket sends webhook → `webhook.py:webhook_handler()`
2. Handler validates payload and schedules background task
3. Background task calls `review_engine.py:process_pull_request_review()`
4. Review engine:
   - Fetches PR diff via `bitbucket_client`
   - Sends diff to LLM via `llm_client`
   - Formats review as HTML via `email_formatter`
   - Sends email via `email_client`

### Manual Review Flow

1. User calls `/manual-review` endpoint → `manual.py:manual_review()`
2. Endpoint fetches diff (PR or commit) via `bitbucket_client`
3. Sends diff to LLM via `llm_client`
4. Formats and sends review email
5. Returns review result to caller

## Design Principles

1. **Separation of Concerns**: Each layer has a single, well-defined responsibility
2. **Dependency Injection**: Clients are created once and shared via dependency injection
3. **Async/Await**: Non-blocking I/O for all external API calls
4. **Error Handling**: Graceful degradation with proper logging
5. **Testability**: Clear boundaries make unit and integration testing straightforward

## External Dependencies

- **Bitbucket Enterprise Server**: Source code repository and webhook source
- **LLM Providers**: OpenAI (cloud) or Ollama (local) for code analysis
- **Azure Logic Apps**: Email delivery service
- **FastAPI**: Web framework for API endpoints
- **httpx**: Async HTTP client library
