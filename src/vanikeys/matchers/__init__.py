"""
VaniKeys matchers - Pattern matching logic for vanity keys.

Core matching algorithms for different pattern types.
"""

from .multi_substring import MultiSubstringMatcher, FuzzyRules

__all__ = [
    "MultiSubstringMatcher",
    "FuzzyRules",
]
