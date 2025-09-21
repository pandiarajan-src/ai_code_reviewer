import os

class Config:
    BITBUCKET_URL = os.getenv("BITBUCKET_URL", "https://your-bitbucket-server.com")
    BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")  # This should be set as an environment variable

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # 'openai', 'local_ollama'
    LLM_API_KEY = os.getenv("LLM_API_KEY")  # Required for OpenAI
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")  # For OpenAI or local Ollama
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")  # 'gpt-4o', 'llama3', 'qwen-coder'

    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Secret for Bitbucket webhooks

    # Paths for local LLM (if using Ollama)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Review instructions for the AI
    REVIEW_PROMPT_TEMPLATE = """You are an expert code reviewer AI. Review the following code changes provided in the diff format.

Focus on the following:
- Bug detection (logic errors, null pointers, race conditions).
- Performance issues (inefficient loops, unnecessary database queries).
- Security vulnerabilities (SQL injection, cross-site scripting).
- Adherence to best practices and code readability.

Do not comment on code style (formatting, line length) as that is handled by a linter.
Provide your feedback in a concise, constructive, and clear manner. If there are no issues, simply respond with "No issues found."

Here is the diff:
```
{diff_content}
```

Please provide your review:"""

    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        errors = []
        
        if not cls.BITBUCKET_TOKEN:
            errors.append("BITBUCKET_TOKEN is required")
            
        if cls.LLM_PROVIDER == "openai" and not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is required when using OpenAI provider")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True

