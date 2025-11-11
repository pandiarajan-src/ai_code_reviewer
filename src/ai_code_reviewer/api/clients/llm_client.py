import logging
from typing import Any

import httpx

from ai_code_reviewer.api.core.config import Config
from ai_code_reviewer.api.core.guidelines_loader import GuidelinesLoader


logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with various LLM providers"""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.api_key = Config.LLM_API_KEY
        self.endpoint = Config.LLM_ENDPOINT
        self.model = Config.LLM_MODEL
        self.ollama_host = Config.OLLAMA_HOST

    async def test_connection(self) -> dict[str, Any]:
        """Test connection to the configured LLM provider"""
        try:
            if self.provider == "openai":
                return await self._test_openai_connection()
            elif self.provider == "local_ollama":
                return await self._test_ollama_connection()
            else:
                return {"status": "error", "error": f"Unknown provider: {self.provider}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _test_openai_connection(self) -> dict[str, Any]:
        """Test OpenAI API connection"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            payload = {"model": self.model, "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)

                if response.status_code == 200:
                    return {"status": "connected", "provider": "openai", "model": self.model}
                else:
                    return {"status": "failed", "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _test_ollama_connection(self) -> dict[str, Any]:
        """Test Ollama API connection"""
        try:
            # Test if Ollama is running
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")

                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model["name"] for model in models]

                    if self.model in model_names:
                        return {
                            "status": "connected",
                            "provider": "ollama",
                            "model": self.model,
                            "available_models": model_names,
                        }
                    else:
                        return {
                            "status": "model_not_found",
                            "error": f"Model {self.model} not found",
                            "available_models": model_names,
                        }
                else:
                    return {"status": "failed", "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_code_review(self, diff_content: str) -> str | None:
        """Get AI code review for the provided diff"""
        try:
            # Load coding guidelines if enabled
            guidelines_section = ""
            if Config.GUIDELINES_ENABLED:
                try:
                    guidelines_content = GuidelinesLoader.load_guidelines(Config.GUIDELINES_FILE)
                    # Detect programming language from diff to extract relevant guidelines
                    detected_language = self._detect_language_from_diff(diff_content)

                    if detected_language:
                        logger.info(f"Detected language: {detected_language}, extracting relevant guidelines")
                        guidelines_section = f"""### 📋 **Coding Guidelines**

The following coding guidelines MUST be followed. Pay special attention to "Rules (Must Comply)" sections:

{GuidelinesLoader.extract_language_guidelines(guidelines_content, detected_language)}"""
                    else:
                        logger.info("No specific language detected, including general principles only")
                        guidelines_section = f"""### 📋 **Coding Guidelines**

The following general coding principles MUST be followed:

{GuidelinesLoader.extract_language_guidelines(guidelines_content, None)}"""

                    logger.info(f"Guidelines section prepared ({len(guidelines_section)} chars)")
                except Exception as e:
                    logger.error(f"Error loading guidelines: {e}, proceeding without guidelines")
                    guidelines_section = ""
            else:
                logger.info("Coding guidelines are disabled (GUIDELINES_ENABLED=false)")

            # Prepare the prompt with guidelines
            prompt = Config.REVIEW_PROMPT_TEMPLATE.format(
                diff_content=diff_content, guidelines_section=guidelines_section
            )

            # Truncate if too long (to avoid token limits)
            max_chars = 80000  # Increased limit to accommodate guidelines (adjust based on your model's context window)
            if len(prompt) > max_chars:
                logger.warning(f"Prompt too long ({len(prompt)} chars), truncating to {max_chars}")
                # Calculate how much space we have for diff after guidelines
                available_chars = max_chars - len(guidelines_section) - 2000  # Reserve 2000 chars for template
                if available_chars < 5000:
                    # If guidelines are too large, truncate them too
                    logger.warning("Guidelines too large, truncating guidelines section")
                    guidelines_section = guidelines_section[:15000] + "\n\n[... guidelines truncated ...]"
                    available_chars = max_chars - len(guidelines_section) - 2000

                truncated_diff = diff_content[:available_chars] + "\n\n[... diff truncated ...]"
                prompt = Config.REVIEW_PROMPT_TEMPLATE.format(
                    diff_content=truncated_diff, guidelines_section=guidelines_section
                )

            if self.provider == "openai":
                return await self._get_openai_review(prompt)
            elif self.provider == "local_ollama":
                return await self._get_ollama_review(prompt)
            else:
                logger.error(f"Unknown LLM provider: {self.provider}")
                return None

        except Exception as e:
            logger.error(f"Error getting code review: {str(e)}")
            return None

    async def _get_openai_review(self, prompt: str) -> str | None:
        """Get code review from OpenAI API"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer. Provide constructive, specific feedback on code changes.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.1,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    review = result["choices"][0]["message"]["content"].strip()
                    logger.info(f"Received OpenAI review ({len(review)} characters)")
                    return str(review)
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return None

    async def _get_ollama_review(self, prompt: str) -> str | None:
        """Get code review from Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9, "num_predict": 2000},
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.ollama_host}/api/generate", json=payload)

                if response.status_code == 200:
                    result = response.json()
                    review = result.get("response", "").strip()
                    logger.info(f"Received Ollama review ({len(review)} characters)")
                    return str(review)
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return None

    def _clean_diff_for_review(self, diff_content: str) -> str:
        """Clean and prepare diff content for review"""
        lines = diff_content.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip binary file indicators
            if line.startswith("Binary files") or "differ" in line:
                continue

            # Skip very long lines that might be minified code
            if len(line) > 500:
                cleaned_lines.append(line[:500] + "... [line truncated]")
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    async def get_summary_review(self, diff_content: str, file_count: int) -> str | None:
        """Get a summary review for large changesets"""
        try:
            summary_prompt = f"""You are an expert code reviewer. This is a large changeset with {file_count} files modified.
Please provide a high-level summary review focusing on:
1. Overall architecture and design patterns
2. Major security concerns
3. Performance implications
4. Breaking changes or compatibility issues

Here's a sample of the changes:
```
{diff_content[:5000]}
```

Provide a concise summary review:"""

            if self.provider == "openai":
                return await self._get_openai_review(summary_prompt)
            elif self.provider == "local_ollama":
                return await self._get_ollama_review(summary_prompt)
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting summary review: {str(e)}")
            return None

    def _detect_language_from_diff(self, diff_content: str) -> str | None:
        """
        Detect the primary programming language from the diff content.

        Analyzes file extensions in the diff to determine the dominant language.

        Args:
            diff_content: The git diff content

        Returns:
            The detected language name (e.g., "Python", "C#", "JavaScript/TypeScript")
            or None if no clear language is detected
        """
        import re
        from collections import Counter

        # Extract file paths from diff headers (diff --git a/path b/path or +++ b/path)
        file_pattern = r"(?:diff --git a/.*? b/|^\+\+\+ b/)(.+?)(?:\s|$)"
        files = re.findall(file_pattern, diff_content, re.MULTILINE)

        if not files:
            logger.debug("No files found in diff")
            return None

        # Map file extensions to language names
        extension_map = {
            ".py": "Python",
            ".cs": "C#",
            ".csproj": "C#",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".h": "C++",
            ".hpp": "C++",
            ".swift": "Swift",
            ".m": "Objective-C",
            ".mm": "Objective-C",
            ".js": "JavaScript/TypeScript",
            ".jsx": "JavaScript/TypeScript",
            ".ts": "JavaScript/TypeScript",
            ".tsx": "JavaScript/TypeScript",
            ".xaml": "XAML/WPF",
        }

        # Count occurrences of each language
        language_counter: Counter[str] = Counter()
        for file_path in files:
            # Get file extension
            if "." in file_path:
                ext = "." + file_path.rsplit(".", 1)[1].lower()
                if ext in extension_map:
                    language_counter[extension_map[ext]] += 1

        if not language_counter:
            logger.debug("No recognized file extensions found in diff")
            return None

        # Return the most common language
        most_common = language_counter.most_common(1)[0]
        detected_language = most_common[0]
        count = most_common[1]

        logger.info(f"Detected primary language: {detected_language} ({count} files)")
        return detected_language
