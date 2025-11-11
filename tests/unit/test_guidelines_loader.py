"""Tests for the GuidelinesLoader utility."""

import tempfile
from pathlib import Path

import pytest

from ai_code_reviewer.api.core.guidelines_loader import GuidelinesLoader


@pytest.fixture
def sample_guidelines_file():
    """Create a temporary guidelines file for testing."""
    content = """# Sample Coding Guidelines

## General Principles

### Universal Rules (Apply to All Languages)

1. **Security First**: Never expose secrets
2. **Error Handling**: Catch specific exceptions

---

## Python

### Rules (Must Comply)

1. **Type Hints**
   Use type annotations for all function parameters.

### Guidelines (Recommended)

- Follow PEP 8 style guidelines

---

## C#

### Rules (Must Comply)

1. **Async-First Pattern**
   Use async/await for all I/O-bound operations.

---

## JavaScript/TypeScript

### Rules (Must Comply)

1. **TypeScript Over JavaScript**
   Always prefer TypeScript.

---
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)
    GuidelinesLoader.clear_cache()


def test_load_guidelines_success(sample_guidelines_file):
    """Test loading guidelines from a file."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)

    assert content is not None
    assert len(content) > 0
    assert "General Principles" in content
    assert "Python" in content


def test_load_guidelines_caching(sample_guidelines_file):
    """Test that guidelines are cached properly."""
    # First load
    content1 = GuidelinesLoader.load_guidelines(sample_guidelines_file)

    # Second load should use cache
    content2 = GuidelinesLoader.load_guidelines(sample_guidelines_file)

    assert content1 == content2
    assert GuidelinesLoader._cached_guidelines is not None


def test_load_guidelines_file_not_found():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        GuidelinesLoader.load_guidelines("/nonexistent/path/to/guidelines.md")


def test_clear_cache(sample_guidelines_file):
    """Test clearing the cache."""
    # Load guidelines
    GuidelinesLoader.load_guidelines(sample_guidelines_file)
    assert GuidelinesLoader._cached_guidelines is not None

    # Clear cache
    GuidelinesLoader.clear_cache()
    assert GuidelinesLoader._cached_guidelines is None
    assert GuidelinesLoader._cached_file_path is None


def test_extract_general_principles(sample_guidelines_file):
    """Test extracting general principles."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)
    extracted = GuidelinesLoader.extract_language_guidelines(content, None)

    assert "General Principles" in extracted
    assert "Security First" in extracted
    # General principles extraction includes everything from General Principles to the first language section
    # This is acceptable behavior as it provides comprehensive guidance


def test_extract_python_guidelines(sample_guidelines_file):
    """Test extracting Python-specific guidelines."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)
    extracted = GuidelinesLoader.extract_language_guidelines(content, "Python")

    assert "## Python" in extracted
    assert "Type Hints" in extracted
    assert "PEP 8" in extracted


def test_extract_csharp_guidelines(sample_guidelines_file):
    """Test extracting C#-specific guidelines."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)
    extracted = GuidelinesLoader.extract_language_guidelines(content, "C#")

    assert "## C#" in extracted
    assert "Async-First Pattern" in extracted


def test_extract_javascript_guidelines(sample_guidelines_file):
    """Test extracting JavaScript/TypeScript guidelines."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)
    extracted = GuidelinesLoader.extract_language_guidelines(content, "JavaScript/TypeScript")

    assert "## JavaScript/TypeScript" in extracted
    assert "TypeScript Over JavaScript" in extracted


def test_extract_unknown_language_fallback(sample_guidelines_file):
    """Test that unknown languages fall back to general principles."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)
    extracted = GuidelinesLoader.extract_language_guidelines(content, "Rust")

    # Should fall back to general principles
    assert "General Principles" in extracted


def test_extract_language_case_insensitive(sample_guidelines_file):
    """Test that language extraction is case-insensitive."""
    content = GuidelinesLoader.load_guidelines(sample_guidelines_file)

    # Test different cases
    extracted1 = GuidelinesLoader.extract_language_guidelines(content, "python")
    extracted2 = GuidelinesLoader.extract_language_guidelines(content, "PYTHON")
    extracted3 = GuidelinesLoader.extract_language_guidelines(content, "Python")

    assert extracted1 == extracted2 == extracted3
    assert "Type Hints" in extracted1
