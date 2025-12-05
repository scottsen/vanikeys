"""
Tests for Pattern domain model.

Validates pattern creation, validation, properties, and serialization.
"""

import pytest
from vanikeys.domain.pattern import Pattern, MatchMode, FuzzyMode


class TestPatternCreation:
    """Test pattern creation and validation."""

    def test_create_simple_pattern(self):
        """Can create simple prefix pattern."""
        pattern = Pattern(substrings=["ALICE"])
        assert pattern.substrings == ["ALICE"]
        assert pattern.mode == MatchMode.PREFIX
        assert pattern.fuzzy == FuzzyMode.NONE
        assert pattern.case_sensitive is False

    def test_create_multi_substring_pattern(self):
        """Can create multi-substring pattern."""
        pattern = Pattern(
            substrings=["GO", "BE", "AWE", "SOME"],
            mode=MatchMode.MULTI_SUBSTRING
        )
        assert len(pattern.substrings) == 4
        assert pattern.mode == MatchMode.MULTI_SUBSTRING

    def test_create_fuzzy_pattern(self):
        """Can create fuzzy matching pattern."""
        pattern = Pattern(
            substrings=["B00M"],
            fuzzy=FuzzyMode.LEETSPEAK
        )
        assert pattern.fuzzy == FuzzyMode.LEETSPEAK
        assert pattern.has_fuzzy is True

    def test_empty_substrings_raises(self):
        """Empty substrings raises ValueError."""
        with pytest.raises(ValueError, match="at least one substring"):
            Pattern(substrings=[])

    def test_multi_substring_requires_two_substrings(self):
        """Multi-substring mode requires at least 2 substrings."""
        with pytest.raises(ValueError, match="at least 2 substrings"):
            Pattern(
                substrings=["ONLY_ONE"],
                mode=MatchMode.MULTI_SUBSTRING
            )

    def test_case_insensitive_normalization(self):
        """Case-insensitive patterns normalize to uppercase."""
        pattern = Pattern(substrings=["alice"], case_sensitive=False)
        assert pattern.substrings == ["ALICE"]

    def test_case_sensitive_no_normalization(self):
        """Case-sensitive patterns don't normalize."""
        pattern = Pattern(substrings=["Alice"], case_sensitive=True)
        assert pattern.substrings == ["Alice"]


class TestPatternProperties:
    """Test pattern property methods."""

    def test_pattern_string_simple(self):
        """Pattern string for simple pattern."""
        pattern = Pattern(substrings=["ALICE"])
        assert pattern.pattern_string == "ALICE"

    def test_pattern_string_multi_substring(self):
        """Pattern string for multi-substring pattern."""
        pattern = Pattern(
            substrings=["GO", "BE", "AWE", "SOME"],
            mode=MatchMode.MULTI_SUBSTRING
        )
        assert pattern.pattern_string == "GO BE AWE SOME"

    def test_is_multi_substring_true(self):
        """is_multi_substring returns True for multi mode."""
        pattern = Pattern(
            substrings=["GO", "BE"],
            mode=MatchMode.MULTI_SUBSTRING
        )
        assert pattern.is_multi_substring is True

    def test_is_multi_substring_false(self):
        """is_multi_substring returns False for other modes."""
        pattern = Pattern(substrings=["ALICE"])
        assert pattern.is_multi_substring is False

    def test_has_fuzzy_true(self):
        """has_fuzzy returns True when fuzzy enabled."""
        pattern = Pattern(
            substrings=["B00M"],
            fuzzy=FuzzyMode.LEETSPEAK
        )
        assert pattern.has_fuzzy is True

    def test_has_fuzzy_false(self):
        """has_fuzzy returns False when fuzzy disabled."""
        pattern = Pattern(substrings=["BOOM"])
        assert pattern.has_fuzzy is False


class TestPatternSerialization:
    """Test pattern serialization and deserialization."""

    def test_to_dict_basic(self):
        """to_dict() converts pattern to dictionary."""
        pattern = Pattern(substrings=["ALICE"])
        data = pattern.to_dict()

        assert data["substrings"] == ["ALICE"]
        assert data["mode"] == "prefix"
        assert data["fuzzy"] == "none"
        assert data["case_sensitive"] is False

    def test_to_dict_with_costs(self):
        """to_dict() includes computed costs."""
        pattern = Pattern(
            substrings=["ALICE"],
            difficulty=100000.0,
            odds="1 in 100K",
            cost_tokens=150,
            cost_guaranteed=5.00
        )
        data = pattern.to_dict()

        assert data["difficulty"] == 100000.0
        assert data["odds"] == "1 in 100K"
        assert data["cost_tokens"] == 150
        assert data["cost_guaranteed"] == 5.00

    def test_to_dict_with_metadata(self):
        """to_dict() includes metadata."""
        pattern = Pattern(
            substrings=["ALICE"],
            user_id="user_123",
            created_at="2025-12-03T10:00:00Z",
            id="pat_abc"
        )
        data = pattern.to_dict()

        assert data["user_id"] == "user_123"
        assert data["created_at"] == "2025-12-03T10:00:00Z"
        assert data["id"] == "pat_abc"

    def test_from_dict_basic(self):
        """from_dict() creates pattern from dictionary."""
        data = {
            "substrings": ["BOB"],
            "mode": "suffix",
            "fuzzy": "none",
            "case_sensitive": False
        }
        pattern = Pattern.from_dict(data)

        assert pattern.substrings == ["BOB"]
        assert pattern.mode == MatchMode.SUFFIX
        assert pattern.fuzzy == FuzzyMode.NONE

    def test_from_dict_with_costs(self):
        """from_dict() restores computed costs."""
        data = {
            "substrings": ["ALICE"],
            "mode": "prefix",
            "difficulty": 50000.0,
            "odds": "1 in 50K",
            "cost_tokens": 100,
            "cost_guaranteed": 3.50
        }
        pattern = Pattern.from_dict(data)

        assert pattern.difficulty == 50000.0
        assert pattern.odds == "1 in 50K"
        assert pattern.cost_tokens == 100
        assert pattern.cost_guaranteed == 3.50

    def test_roundtrip_serialization(self):
        """Pattern survives to_dict() -> from_dict() roundtrip."""
        original = Pattern(
            substrings=["GO", "BE", "AWE"],
            mode=MatchMode.MULTI_SUBSTRING,
            fuzzy=FuzzyMode.LEETSPEAK,
            case_sensitive=False,
            difficulty=1000000.0,
            odds="1 in 1M",
            cost_tokens=250,
            cost_guaranteed=10.00,
            user_id="user_456",
            created_at="2025-12-03T11:00:00Z",
            id="pat_xyz"
        )

        data = original.to_dict()
        restored = Pattern.from_dict(data)

        assert restored.substrings == original.substrings
        assert restored.mode == original.mode
        assert restored.fuzzy == original.fuzzy
        assert restored.case_sensitive == original.case_sensitive
        assert restored.difficulty == original.difficulty
        assert restored.odds == original.odds
        assert restored.cost_tokens == original.cost_tokens
        assert restored.cost_guaranteed == original.cost_guaranteed
        assert restored.user_id == original.user_id
        assert restored.created_at == original.created_at
        assert restored.id == original.id


class TestMatchModes:
    """Test all match modes."""

    def test_prefix_mode(self):
        """PREFIX mode creates valid pattern."""
        pattern = Pattern(substrings=["DEV"], mode=MatchMode.PREFIX)
        assert pattern.mode == MatchMode.PREFIX

    def test_suffix_mode(self):
        """SUFFIX mode creates valid pattern."""
        pattern = Pattern(substrings=["PROD"], mode=MatchMode.SUFFIX)
        assert pattern.mode == MatchMode.SUFFIX

    def test_contains_mode(self):
        """CONTAINS mode creates valid pattern."""
        pattern = Pattern(substrings=["TEST"], mode=MatchMode.CONTAINS)
        assert pattern.mode == MatchMode.CONTAINS

    def test_multi_substring_mode(self):
        """MULTI_SUBSTRING mode creates valid pattern."""
        pattern = Pattern(
            substrings=["A", "B", "C"],
            mode=MatchMode.MULTI_SUBSTRING
        )
        assert pattern.mode == MatchMode.MULTI_SUBSTRING

    def test_regex_mode(self):
        """REGEX mode creates valid pattern."""
        pattern = Pattern(substrings=["[0-9]+"], mode=MatchMode.REGEX)
        assert pattern.mode == MatchMode.REGEX


class TestFuzzyModes:
    """Test all fuzzy modes."""

    def test_no_fuzzy(self):
        """NONE fuzzy mode (exact match)."""
        pattern = Pattern(substrings=["EXACT"], fuzzy=FuzzyMode.NONE)
        assert pattern.fuzzy == FuzzyMode.NONE
        assert pattern.has_fuzzy is False

    def test_leetspeak_fuzzy(self):
        """LEETSPEAK fuzzy mode."""
        pattern = Pattern(substrings=["B00M"], fuzzy=FuzzyMode.LEETSPEAK)
        assert pattern.fuzzy == FuzzyMode.LEETSPEAK
        assert pattern.has_fuzzy is True

    def test_homoglyphs_fuzzy(self):
        """HOMOGLYPHS fuzzy mode."""
        pattern = Pattern(substrings=["O0O"], fuzzy=FuzzyMode.HOMOGLYPHS)
        assert pattern.fuzzy == FuzzyMode.HOMOGLYPHS
        assert pattern.has_fuzzy is True

    def test_phonetic_fuzzy(self):
        """PHONETIC fuzzy mode."""
        pattern = Pattern(substrings=["KOOL"], fuzzy=FuzzyMode.PHONETIC)
        assert pattern.fuzzy == FuzzyMode.PHONETIC
        assert pattern.has_fuzzy is True


class TestRealWorldPatterns:
    """Test realistic pattern configurations."""

    def test_devops_team_pattern(self):
        """DevOps team vanity key pattern."""
        pattern = Pattern(
            substrings=["ACME", "DEV"],
            mode=MatchMode.MULTI_SUBSTRING,
            user_id="team_devops"
        )
        assert pattern.pattern_string == "ACME DEV"
        assert pattern.is_multi_substring is True

    def test_personal_vanity_pattern(self):
        """Personal vanity key with fuzzy matching."""
        pattern = Pattern(
            substrings=["C00L"],
            fuzzy=FuzzyMode.LEETSPEAK
        )
        assert pattern.has_fuzzy is True
        assert pattern.substrings == ["C00L"]

    def test_environment_specific_pattern(self):
        """Environment-specific SSH key pattern."""
        pattern = Pattern(
            substrings=["PROD"],
            mode=MatchMode.PREFIX
        )
        assert pattern.mode == MatchMode.PREFIX
        assert pattern.pattern_string == "PROD"

    def test_security_versioned_pattern(self):
        """Versioned pattern for key rotation."""
        pattern = Pattern(
            substrings=["INFRA", "V2"],
            mode=MatchMode.MULTI_SUBSTRING
        )
        assert pattern.pattern_string == "INFRA V2"
