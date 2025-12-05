"""
Tests for Pattern Matching and Difficulty Estimation
"""

import pytest
from vanikeys.crypto.matching import (
    create_pattern_matcher,
    estimate_pattern_difficulty,
    validate_pattern,
)


class TestPatternMatcher:
    """Test pattern matching functions."""

    def test_simple_substring_match(self):
        """Simple substring matching."""
        matcher = create_pattern_matcher("lab", case_sensitive=False)

        assert matcher("SHA256:lab123xxxxxxxxxxxx")
        assert matcher("SHA256:xxxlab123xxxxxxxxx")
        assert not matcher("SHA256:xyz999xxxxxxxxxxxx")

    def test_case_insensitive_matching(self):
        """Case-insensitive matching works."""
        matcher = create_pattern_matcher("lab", case_sensitive=False)

        assert matcher("SHA256:LAB123")
        assert matcher("SHA256:Lab123")
        assert matcher("SHA256:lab123")

    def test_case_sensitive_matching(self):
        """Case-sensitive matching works."""
        matcher = create_pattern_matcher("lab", case_sensitive=True)

        assert matcher("SHA256:lab123")
        assert not matcher("SHA256:LAB123")
        assert not matcher("SHA256:Lab123")

    def test_regex_pattern_matching(self):
        """Regex patterns work."""
        matcher = create_pattern_matcher("lab[0-9]{3}", case_sensitive=False)

        assert matcher("SHA256:lab123")
        assert matcher("SHA256:lab999")
        assert not matcher("SHA256:lababc")


class TestDifficultyEstimation:
    """Test pattern difficulty estimation."""

    def test_estimate_easy_pattern(self):
        """Short patterns are easy."""
        est = estimate_pattern_difficulty("a", case_sensitive=False)

        assert est["difficulty_class"] == "easy"
        assert est["expected_attempts"] < 100

    def test_estimate_medium_pattern(self):
        """Medium patterns take longer."""
        est = estimate_pattern_difficulty("lab", case_sensitive=False)

        assert est["difficulty_class"] in ["easy", "medium"]

    def test_estimate_hard_pattern(self):
        """Long patterns are hard."""
        est = estimate_pattern_difficulty("lab1234", case_sensitive=False)

        assert est["difficulty_class"] in ["hard", "extreme"]
        assert est["expected_attempts"] > 1_000_000_000

    def test_difficulty_fields_present(self):
        """All expected fields present."""
        est = estimate_pattern_difficulty("test", case_sensitive=False)

        assert "pattern" in est
        assert "pattern_length" in est
        assert "expected_attempts" in est
        assert "difficulty_class" in est
        assert "cost_estimate_usd" in est


class TestPatternValidation:
    """Test pattern validation."""

    def test_valid_pattern(self):
        """Valid patterns pass."""
        result = validate_pattern("lab123")

        assert result["valid"]
        assert len(result["errors"]) == 0

    def test_empty_pattern_invalid(self):
        """Empty patterns are invalid."""
        result = validate_pattern("")

        assert not result["valid"]
        assert len(result["errors"]) > 0

    def test_too_long_pattern_invalid(self):
        """Very long patterns are invalid."""
        result = validate_pattern("a" * 30)

        assert not result["valid"]
