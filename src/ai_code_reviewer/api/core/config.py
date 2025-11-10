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
     > "Only <filetype> changes found, so I don't review these changes, but I hope that you made necessary checks not to have problems in these configuration files."
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

4. If a section has no findings, respond **exactly** as follows:
   - For Bugs/Performance/Security: `"No issues found."`
   - For Best Practices: `"All is good, no suggestion."`
   - For Recommendations: `"No changes needed."`

5. If the overall review finds no problems at all, simply respond:
   > "No issues found."

---

### 🧱 **Structured Output Format**

Use the exact HTML structure below for all code reviews (except skipped file types):

<h1>🤖 AI Code Review</h1>

<h2>Concise Conclusion</h2>
Provide a short summary (1–3 sentences) of overall findings and risk level.

<h2>Potential Issues</h2>

<h3>Bugs</h3>
Briefly list any logic or runtime problems. If none, say: “No issues found.”

<h3>Performance</h3>
List performance optimizations or inefficiencies. If none, say: “No issues found.”

<h3>Security</h3>
List potential security vulnerabilities. If none, say: “No issues found.”

<h2>Recommended Best Practices</h2>
Give short, clear suggestions for improvement. If none, say: “All is good, no suggestion.”

<h2>Recommended Changes</h2>
Summarize actionable steps in bullet points. If none, say: “No changes needed.”

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
