import os
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from .env file
# Look for .env in the project root (4 levels up from this file)
# Path: src/ai_code_reviewer/api/core/config.py -> project root
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    BITBUCKET_URL = os.getenv("BITBUCKET_URL", "https://your-bitbucket-server.com")
    BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")  # This should be set as an environment variable

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # 'openai', 'local_ollama'
    LLM_API_KEY = os.getenv("LLM_API_KEY")  # Required for OpenAI
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")  # For OpenAI or local Ollama
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")  # 'gpt-4o', 'llama3', 'qwen-coder'

    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Secret for Bitbucket webhooks

    # Email configuration
    LOGIC_APP_EMAIL_URL = os.getenv("LOGIC_APP_EMAIL_URL")  # Required for email notifications
    LOGIC_APP_FROM_EMAIL = os.getenv("LOGIC_APP_FROM_EMAIL", "pandiarajans@test.com")
    EMAIL_OPTOUT = os.getenv("EMAIL_OPTOUT", "true").lower() == "true"  # Default to true for testing

    # Paths for local LLM (if using Ollama)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Review instructions for the AI
    REVIEW_PROMPT_TEMPLATE = """You are an expert AI code reviewer specializing in software design, performance, and security.
You will receive a "git diff" containing changes that may span one or more files.

Your task is to perform a precise, focused, and concise code review.
Avoid verbosity — your responses should be short, clear, and directly actionable.

---

### 🔍 Review Instructions

1. **File Type Skip Logic:**
   - If all modified files are of non-source or configuration types such as:
     `.ini`, `.xml`, `.json`, `.res`, `.resx`, `.xcf`, `.pdf`, `.docx`, `.exe`, `.dll`, `.xlsx`
     → then skip the review.
   - Respond **only** with:
     > "Only changes in <filetypes> files were detected. As a result, these modifications are not subject to code review; however, but please ensure they are error-free and adhere to your project's standards."
   - Do **not** use the structured format in this case.

2. **For Source Code Files (.cs, .py, .js, .java, .cpp, etc.):**
   - Review all related file changes **together** as one logical change.
   - You may consider the **entire file context** (not just modified lines) to detect dependencies or side effects.

3. **Focus Areas:**
   - **Functional bugs:** Logic errors, null handling, race conditions, runtime risks.
   - **Performance:** Inefficient loops, redundant computations, unnecessary I/O or DB calls.
   - **Security:** Injection risks, unsafe logging, exposure of sensitive data, thread-safety issues.
   - **Best practices:** Error handling, maintainability, DRY, modularity, and clarity.
   - Do **not** comment on style, naming, or formatting.

4. **Coding Guidelines Compliance (CRITICAL):**
   - If coding guidelines are provided below, you MUST check the code against them.
   - Pay special attention to items marked as "Rules (Must Comply)" or "Must Comply".
   - Flag ANY violations of mandatory guidelines explicitly in the review.
   - Mention specific guideline rules that are violated (e.g., "Violates C# Rule #1: Async-First Pattern").
   - Guidelines marked as "Guidelines (Recommended)" or "Things to Avoid" should be mentioned but are not critical violations.

5. If a section has no findings, respond **exactly** as follows:
   - For Bugs/Performance/Security: `"No issues found."`
   - For Best Practices: `"All is good, no suggestion."`
   - For Recommendations: `"No changes needed."`
   - For Coding Guidelines: `"No guideline violations found."`

6. If the overall review finds no problems at all, simply respond:
   > "No issues found."

---

### 🧱 **Structured Output Format**

Use the exact markdown (.md) file structure below for all code reviews (except skipped file types):

# 🤖 AI Code Review

## Concise Conclusion
Provide a short summary (1–3 sentences) of overall findings and risk level.

## Recommended Changes
Summarize actionable steps in bullet points. If none, say: "No changes needed."

## Potential Issues Found:
**Bugs**
Briefly list any logic or runtime problems. If none, say: "No issues found."

**Performance**
List performance optimizations or inefficiencies. If none, say: "No issues found."

**Security**
List potential security vulnerabilities. If none, say: "No issues found."

**Coding Guidelines Violations**
List any violations of the mandatory coding guidelines (if provided). Reference specific guideline rules by name/number. If none, say: "No guideline violations found."

## Recommended Best Practices
Give short, clear suggestions for improvement (including recommended guidelines). If none, say: "All is good, no suggestion."

Here is the coding guidelines to follow:
---
{guidelines_section}
---

Here is the diff for your analysis:
```
{diff_content}
```

Please provide your complete review following the rules and structure above."""

    # Server configuration
    # nosec B104: Binding to 0.0.0.0 is required for Docker containers to accept external connections
    # This is standard practice for containerized applications
    HOST = os.getenv("HOST", "0.0.0.0")  # nosec B104
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))  # Backend API port
    FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))  # Frontend UI port

    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_code_reviewer.db")
    DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"  # Enable SQL query logging

    # Coding guidelines configuration
    GUIDELINES_FILE = os.getenv(
        "GUIDELINES_FILE",
        str(
            Path(__file__).parent.parent.parent.parent.parent
            / "Guidelines"
            / "Universal_Engineering_Coding_Guidelines.md"
        ),
    )
    GUIDELINES_ENABLED = os.getenv("GUIDELINES_ENABLED", "true").lower() == "true"

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        errors = []

        if not cls.BITBUCKET_TOKEN:
            errors.append("BITBUCKET_TOKEN is required")

        if cls.LLM_PROVIDER == "openai" and not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is required when using OpenAI provider")

        if not cls.EMAIL_OPTOUT and not cls.LOGIC_APP_EMAIL_URL:
            errors.append("LOGIC_APP_EMAIL_URL is required when EMAIL_OPTOUT is false")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True
