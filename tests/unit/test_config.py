import os
from unittest.mock import patch

import pytest

from ai_code_reviewer.api.core.config import Config


class TestConfig:
    """Test configuration management"""

    def test_default_values(self):
        """Test default configuration values"""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("ai_code_reviewer.api.core.config.load_dotenv"),
        ):
            # Reload config to pick up defaults
            import importlib

            from ai_code_reviewer.api.core import config

            importlib.reload(config)

            assert config.Config.HOST == "0.0.0.0"
            assert config.Config.BACKEND_PORT == 8000
            assert config.Config.LOG_LEVEL == "INFO"
            assert config.Config.LLM_PROVIDER == "openai"
            assert config.Config.LLM_MODEL == "gpt-4o"

    def test_environment_override(self):
        """Test environment variable override"""
        with patch.dict(os.environ, {"BACKEND_PORT": "9000", "LOG_LEVEL": "DEBUG"}):
            # Reload config to pick up new environment
            import importlib

            from ai_code_reviewer.api.core import config

            importlib.reload(config)

            assert config.Config.BACKEND_PORT == 9000
            assert config.Config.LOG_LEVEL == "DEBUG"

    def test_validate_config_success(self):
        """Test successful configuration validation"""
        with patch.dict(
            os.environ, {"BITBUCKET_TOKEN": "test_token", "LLM_API_KEY": "test_key", "LLM_PROVIDER": "openai"}
        ):
            import importlib

            from ai_code_reviewer.api.core import config

            importlib.reload(config)

            assert config.Config.validate_config() is True

    def test_validate_config_missing_bitbucket_token(self):
        """Test validation failure for missing Bitbucket token"""
        with patch.dict(os.environ, {"BITBUCKET_TOKEN": ""}, clear=True):
            import importlib

            from ai_code_reviewer.api.core import config

            importlib.reload(config)

            with pytest.raises(ValueError, match="BITBUCKET_TOKEN is required"):
                config.Config.validate_config()

    def test_validate_config_missing_openai_key(self):
        """Test validation failure for missing OpenAI key"""
        with patch.dict(
            os.environ, {"BITBUCKET_TOKEN": "test_token", "LLM_PROVIDER": "openai", "LLM_API_KEY": ""}, clear=True
        ):
            import importlib

            from ai_code_reviewer.api.core import config

            importlib.reload(config)

            with pytest.raises(ValueError, match="LLM_API_KEY is required"):
                config.Config.validate_config()

    def test_validate_config_local_ollama(self):
        """Test validation success for local Ollama provider"""
        with patch.dict(os.environ, {"BITBUCKET_TOKEN": "test_token", "LLM_PROVIDER": "local_ollama"}, clear=True):
            import importlib

            from ai_code_reviewer.api.core import config

            importlib.reload(config)

            assert config.Config.validate_config() is True

    def test_review_prompt_template(self):
        """Test review prompt template formatting"""
        diff_content = "test diff content"
        formatted_prompt = Config.REVIEW_PROMPT_TEMPLATE.format(diff_content=diff_content)

        assert "test diff content" in formatted_prompt
        assert "expert code reviewer" in formatted_prompt.lower()
        assert "bug detection" in formatted_prompt.lower()
