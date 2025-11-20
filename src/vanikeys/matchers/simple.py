"""Simple pattern matchers (prefix, suffix, contains, regex)."""

import re
from vanikeys.matchers.base import PatternMatcher


class PrefixMatcher(PatternMatcher):
    """Match pattern at the start of the string."""

    def matches(self, candidate: str) -> bool:
        """Check if candidate starts with pattern."""
        normalized = self._normalize(candidate)
        return normalized.startswith(self.pattern)


class SuffixMatcher(PatternMatcher):
    """Match pattern at the end of the string."""

    def matches(self, candidate: str) -> bool:
        """Check if candidate ends with pattern."""
        normalized = self._normalize(candidate)
        return normalized.endswith(self.pattern)


class ContainsMatcher(PatternMatcher):
    """Match pattern anywhere in the string."""

    def matches(self, candidate: str) -> bool:
        """Check if pattern appears anywhere in candidate."""
        normalized = self._normalize(candidate)
        return self.pattern in normalized


class RegexMatcher(PatternMatcher):
    """Match using regular expression."""

    def __init__(self, pattern: str, case_sensitive: bool = True):
        """
        Initialize regex matcher.

        Args:
            pattern: Regular expression pattern
            case_sensitive: Whether matching is case-sensitive
        """
        super().__init__(pattern, case_sensitive)

        # Compile regex with appropriate flags
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            self.regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def matches(self, candidate: str) -> bool:
        """Check if candidate matches regex pattern."""
        return self.regex.search(candidate) is not None
