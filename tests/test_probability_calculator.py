"""
Tests for probability calculator.

Tests difficulty estimation, odds calculation, and cost calculation.
"""

import pytest
from vanikeys.core import ProbabilityCalculator
from vanikeys.domain import Pattern, MatchMode, FuzzyMode


class TestProbabilityCalculator:
    """Test probability calculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calc = ProbabilityCalculator()

    def test_simple_prefix_pattern(self):
        """Test simple prefix pattern probability."""
        pattern = Pattern(substrings=["GO"], mode=MatchMode.PREFIX)
        result = self.calc.calculate(pattern)

        # Should have reasonable probability
        assert result["probability"] > 0
        assert result["expected_attempts"] > 1

        # Should have odds display
        assert "1 in" in result["odds_display"]

        # Should have cost
        assert result["cost_tokens"] >= 50
        assert result["cost_guaranteed_usd"] >= 5.0

    def test_longer_prefix_harder(self):
        """Test that longer patterns are harder."""
        short_pattern = Pattern(substrings=["GO"], mode=MatchMode.PREFIX)
        long_pattern = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)

        short_result = self.calc.calculate(short_pattern)
        long_result = self.calc.calculate(long_pattern)

        # Longer pattern should be harder
        assert long_result["expected_attempts"] > short_result["expected_attempts"]
        assert long_result["cost_tokens"] > short_result["cost_tokens"]

    def test_multi_substring_harder(self):
        """Test that multi-substring is harder than single."""
        single = Pattern(substrings=["GO"], mode=MatchMode.PREFIX)
        multi = Pattern(
            substrings=["GO", "BE", "AWE"],
            mode=MatchMode.MULTI_SUBSTRING,
        )

        single_result = self.calc.calculate(single)
        multi_result = self.calc.calculate(multi)

        # Multi-substring should be harder
        assert multi_result["expected_attempts"] > single_result["expected_attempts"]
        assert multi_result["cost_tokens"] > single_result["cost_tokens"]

    def test_fuzzy_matching_easier(self):
        """Test that fuzzy matching is easier."""
        exact = Pattern(
            substrings=["B00M"],
            mode=MatchMode.PREFIX,
            fuzzy=FuzzyMode.NONE,
        )
        fuzzy = Pattern(
            substrings=["B00M"],
            mode=MatchMode.PREFIX,
            fuzzy=FuzzyMode.LEETSPEAK,
        )

        exact_result = self.calc.calculate(exact)
        fuzzy_result = self.calc.calculate(fuzzy)

        # Fuzzy should be easier (more valid chars per position)
        assert fuzzy_result["expected_attempts"] < exact_result["expected_attempts"]

    def test_difficulty_score(self):
        """Test difficulty score calculation."""
        pattern = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)
        result = self.calc.calculate(pattern)

        # Difficulty score is log10 of expected attempts
        assert result["difficulty_score"] >= 0

    def test_odds_display_formatting(self):
        """Test human-readable odds formatting."""
        # Test various scales
        assert "1 in 1.0K" in self.calc._format_odds(1000)
        assert "1 in 1.0M" in self.calc._format_odds(1_000_000)
        assert "1 in 4.2B" in self.calc._format_odds(4_200_000_000)

    def test_token_cost_scaling(self):
        """Test token cost scales with difficulty."""
        easy = Pattern(substrings=["A"], mode=MatchMode.PREFIX)
        medium = Pattern(substrings=["ABC"], mode=MatchMode.PREFIX)
        hard = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)

        easy_cost = self.calc.calculate(easy)["cost_tokens"]
        medium_cost = self.calc.calculate(medium)["cost_tokens"]
        hard_cost = self.calc.calculate(hard)["cost_tokens"]

        # Costs should increase with difficulty
        assert easy_cost <= medium_cost <= hard_cost

    def test_guaranteed_cost_minimum(self):
        """Test guaranteed mode has minimum cost."""
        pattern = Pattern(substrings=["A"], mode=MatchMode.PREFIX)
        result = self.calc.calculate(pattern)

        # Minimum guaranteed cost is $5.00
        assert result["cost_guaranteed_usd"] >= 5.0

    def test_guaranteed_cost_scales(self):
        """Test guaranteed cost scales with difficulty."""
        easy = Pattern(substrings=["GO"], mode=MatchMode.PREFIX)
        hard = Pattern(substrings=["GOBEAWESOME"], mode=MatchMode.PREFIX)

        easy_cost = self.calc.calculate(easy)["cost_guaranteed_usd"]
        hard_cost = self.calc.calculate(hard)["cost_guaranteed_usd"]

        # Harder pattern should cost more
        assert hard_cost > easy_cost

    def test_explain_calculation(self):
        """Test calculation explanation."""
        pattern = Pattern(
            substrings=["GO", "BE"],
            mode=MatchMode.MULTI_SUBSTRING,
        )
        explanation = self.calc.explain_calculation(pattern)

        # Should contain key information
        assert "GO BE" in explanation
        assert "Multi-substring" in explanation.lower() or "multi" in explanation.lower()
        assert "probability" in explanation.lower() or "odds" in explanation.lower()
        assert "cost" in explanation.lower() or "tokens" in explanation.lower()

    def test_contains_mode(self):
        """Test 'contains' mode probability."""
        pattern = Pattern(substrings=["ALICE"], mode=MatchMode.CONTAINS)
        result = self.calc.calculate(pattern)

        # Should be easier than prefix (more positions to match)
        prefix_pattern = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)
        prefix_result = self.calc.calculate(prefix_pattern)

        # Contains should have higher probability
        assert result["probability"] >= prefix_result["probability"]

    def test_suffix_mode(self):
        """Test suffix mode probability."""
        pattern = Pattern(substrings=["ALICE"], mode=MatchMode.SUFFIX)
        result = self.calc.calculate(pattern)

        # Should be same as prefix (just position-specific)
        prefix_pattern = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)
        prefix_result = self.calc.calculate(prefix_pattern)

        # Probabilities should be similar
        assert abs(result["probability"] - prefix_result["probability"]) < 0.0001


class TestRealWorldPatterns:
    """Test with real-world pattern examples."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calc = ProbabilityCalculator()

    def test_canonical_vanikeys_example(self):
        """Test the canonical VaniKeys example: 'GO BE AWE SOME'."""
        pattern = Pattern(
            substrings=["GO", "BE", "AWE", "SOME"],
            mode=MatchMode.MULTI_SUBSTRING,
        )
        result = self.calc.calculate(pattern)

        # This should be quite difficult
        assert result["difficulty_score"] > 5.0  # At least 100K attempts
        assert result["cost_tokens"] >= 100

        # Should have human-readable odds
        assert "1 in" in result["odds_display"]

    def test_simple_business_did(self):
        """Test simple business DID (e.g., 'ACME')."""
        pattern = Pattern(substrings=["ACME"], mode=MatchMode.PREFIX)
        result = self.calc.calculate(pattern)

        # Should be moderately difficult
        assert result["cost_tokens"] >= 50
        assert result["cost_guaranteed_usd"] >= 5.0

    def test_personal_name(self):
        """Test personal name (e.g., 'ALICE')."""
        pattern = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)
        result = self.calc.calculate(pattern)

        # Should be difficult (5 characters)
        assert result["difficulty_score"] > 4.0
        assert result["cost_tokens"] >= 80

    def test_fuzzy_cool_pattern(self):
        """Test fuzzy 'C00L' pattern."""
        pattern = Pattern(
            substrings=["C00L"],
            mode=MatchMode.PREFIX,
            fuzzy=FuzzyMode.LEETSPEAK,
        )
        result = self.calc.calculate(pattern)

        # Should be easier than exact "C00L"
        assert result["cost_tokens"] >= 50

    def test_whale_pattern(self):
        """Test very difficult whale pattern."""
        pattern = Pattern(
            substrings=["GO", "BE", "AWE", "SOME", "COOL"],
            mode=MatchMode.MULTI_SUBSTRING,
        )
        result = self.calc.calculate(pattern)

        # This should be extremely difficult
        assert result["difficulty_score"] > 8.0
        assert result["cost_tokens"] >= 150
        assert result["cost_guaranteed_usd"] >= 50.0
