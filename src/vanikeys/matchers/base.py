"""Base pattern matcher interface."""

from abc import ABC, abstractmethod


class PatternMatcher(ABC):
    """Abstract base class for pattern matching strategies."""

    def __init__(self, pattern: str, case_sensitive: bool = True):
        """
        Initialize pattern matcher.

        Args:
            pattern: The pattern to search for
            case_sensitive: Whether matching is case-sensitive
        """
        self.pattern = pattern
        self.case_sensitive = case_sensitive

        # Normalize pattern if case-insensitive
        if not case_sensitive:
            self.pattern = self.pattern.upper()

    @abstractmethod
    def matches(self, candidate: str) -> bool:
        """
        Check if candidate string matches the pattern.

        Args:
            candidate: String to check for pattern match

        Returns:
            True if candidate matches pattern, False otherwise
        """
        pass

    def _normalize(self, text: str) -> str:
        """Normalize text for case-insensitive matching."""
        if not self.case_sensitive:
            return text.upper()
        return text

    def __repr__(self) -> str:
        """String representation of matcher."""
        return (
            f"{self.__class__.__name__}("
            f"pattern='{self.pattern}', "
            f"case_sensitive={self.case_sensitive})"
        )
