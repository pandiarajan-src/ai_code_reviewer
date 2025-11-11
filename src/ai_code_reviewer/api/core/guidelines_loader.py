"""Guidelines loader utility for loading coding guidelines from markdown files."""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class GuidelinesLoader:
    """Loads and caches coding guidelines from markdown files."""

    _cached_guidelines: str | None = None
    _cached_file_path: Path | None = None

    @classmethod
    def load_guidelines(cls, file_path: str | Path) -> str:
        """
        Load coding guidelines from a markdown file.

        Args:
            file_path: Path to the guidelines markdown file

        Returns:
            The content of the guidelines file as a string

        Raises:
            FileNotFoundError: If the guidelines file doesn't exist
            IOError: If there's an error reading the file
        """
        file_path = Path(file_path)

        # Return cached content if file path hasn't changed
        if cls._cached_guidelines is not None and cls._cached_file_path == file_path:
            logger.debug(f"Using cached guidelines from {file_path}")
            return cls._cached_guidelines

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Guidelines file not found: {file_path}")

        if not file_path.is_file():
            raise OSError(f"Guidelines path is not a file: {file_path}")

        # Read the file
        try:
            logger.info(f"Loading coding guidelines from {file_path}")
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Cache the content
            cls._cached_guidelines = content
            cls._cached_file_path = file_path

            logger.info(f"Successfully loaded {len(content)} characters of guidelines")
            return content

        except Exception as e:
            logger.error(f"Error reading guidelines file {file_path}: {e}")
            raise OSError(f"Failed to read guidelines file: {e}") from e

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the cached guidelines (useful for testing or reloading)."""
        cls._cached_guidelines = None
        cls._cached_file_path = None
        logger.debug("Cleared guidelines cache")

    @classmethod
    def extract_language_guidelines(cls, guidelines: str, language: str | None = None) -> str:
        """
        Extract language-specific guidelines from the full guidelines document.

        Args:
            guidelines: Full guidelines content
            language: Programming language to extract (e.g., "Python", "C#", "JavaScript/TypeScript")
                     If None, returns general principles only

        Returns:
            Extracted guidelines section
        """
        if language is None:
            # Extract only general principles
            start_marker = "## General Principles"
            end_marker = "## C# (.NET/WPF)"
        else:
            # Map common language names to section headers
            language_sections = {
                "python": "## Python",
                "csharp": "## C# (.NET/WPF)",
                "c#": "## C# (.NET/WPF)",
                ".net": "## C# (.NET/WPF)",
                "c++": "## C++",
                "cpp": "## C++",
                "swift": "## Swift & SwiftUI",
                "swiftui": "## Swift & SwiftUI",
                "objective-c": "## Objective-C",
                "objc": "## Objective-C",
                "javascript": "## JavaScript/TypeScript",
                "typescript": "## JavaScript/TypeScript",
                "js": "## JavaScript/TypeScript",
                "ts": "## JavaScript/TypeScript",
                "xaml": "## XAML/WPF",
                "wpf": "## XAML/WPF",
            }

            # Normalize language name
            lang_key = language.lower().replace(" ", "").replace("/", "")
            start_marker_found = language_sections.get(lang_key)

            if start_marker_found is None:
                logger.warning(f"Unknown language '{language}', using general principles only")
                return cls.extract_language_guidelines(guidelines, None)

            # Use the found marker
            start_marker = start_marker_found
            # Find the next section marker
            end_marker = "---"  # Section separator

        # Extract the section
        try:
            start_idx = guidelines.find(start_marker)
            if start_idx == -1:
                logger.warning(f"Could not find section '{start_marker}' in guidelines")
                return guidelines  # Return full guidelines as fallback

            # Find the end of the section (next section or end of document)
            end_idx = guidelines.find(end_marker, start_idx + len(start_marker))
            extracted = guidelines[start_idx:] if end_idx == -1 else guidelines[start_idx:end_idx]

            logger.debug(f"Extracted {len(extracted)} characters for language '{language}'")
            return extracted.strip()

        except Exception as e:
            logger.error(f"Error extracting language guidelines: {e}")
            return guidelines  # Return full guidelines as fallback
