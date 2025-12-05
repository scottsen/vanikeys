"""
Tests for multi-substring matcher.

Tests the core VaniKeys innovation: sequential substring matching.
"""

import pytest
from vanikeys.matchers import MultiSubstringMatcher, FuzzyRules


class TestFuzzyRules:
    """Test fuzzy matching rules."""

    def test_to_regex_pattern_simple(self):
        """Test simple pattern conversion."""
        pattern = FuzzyRules.to_regex_pattern("GO")
        # Should allow both G/g and O/0
        assert "G" in pattern or "g" in pattern
        assert "O" in pattern or "0" in pattern

    def test_to_regex_pattern_leetspeak(self):
        """Test leetspeak pattern conversion."""
        pattern = FuzzyRules.to_regex_pattern("B00M")
        # B/8, 0/O, 0/O, M/m
        assert pattern  # Basic check

    def test_normalize(self):
        """Test text normalization."""
        assert FuzzyRules.normalize("B00M") == "BOOM"
        assert FuzzyRules.normalize("G0") == "GO"
        assert FuzzyRules.normalize("1337") == "IEET"  # 1→I, 3→E, 3→E, 7→T


class TestMultiSubstringMatcher:
    """Test multi-substring matcher."""

    def test_simple_match(self):
        """Test simple two-substring match."""
        matcher = MultiSubstringMatcher(["GO", "BE"])
        assert matcher.match("GOxxxBE")
        assert matcher.match("did:key:z6MkGOxxxBExxx")
        assert not matcher.match("BExxxGO")  # Wrong order

    def test_multi_substring_match(self):
        """Test multi-substring (VaniKeys innovation!)."""
        matcher = MultiSubstringMatcher(["GO", "BE", "AWE", "SOME"])
        assert matcher.match("GOxxxBExxxAWExxxSOME")
        assert matcher.match("did:key:z6MkGOxBExAWExSOME")
        assert not matcher.match("GOxxxAWExxxBExxxSOME")  # Wrong order

    def test_fuzzy_matching(self):
        """Test fuzzy matching (leetspeak)."""
        matcher = MultiSubstringMatcher(["B00M"], fuzzy=True)
        assert matcher.match("BOOM")  # 0→O
        assert matcher.match("B00M")  # Exact
        assert matcher.match("B0OM")  # Mix
        assert matcher.match("8OOM")  # 8→B

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        matcher = MultiSubstringMatcher(["ALICE"], case_sensitive=False)
        assert matcher.match("alice")
        assert matcher.match("Alice")
        assert matcher.match("ALICE")

    def test_case_sensitive(self):
        """Test case-sensitive matching."""
        matcher = MultiSubstringMatcher(["ALICE"], case_sensitive=True)
        assert matcher.match("ALICE")
        assert not matcher.match("alice")

    def test_match_positions(self):
        """Test finding match positions."""
        matcher = MultiSubstringMatcher(["GO", "BE"])
        positions = matcher.match_positions("xxGOxxxBExx")
        assert positions == [(2, 4), (7, 9)]

    def test_match_positions_multi(self):
        """Test finding positions for multi-substring."""
        matcher = MultiSubstringMatcher(["GO", "BE", "AWE"])
        text = "did:key:z6MkGOxBExAWE"
        positions = matcher.match_positions(text)
        assert positions is not None
        assert len(positions) == 3

    def test_extract_matched_text(self):
        """Test extracting matched portion."""
        matcher = MultiSubstringMatcher(["GO", "BE"])
        matched = matcher.extract_matched_text("xxGOxxxBExx")
        assert matched == "GOxxxBE"

    def test_no_match(self):
        """Test when pattern doesn't match."""
        matcher = MultiSubstringMatcher(["GO", "BE"])
        assert not matcher.match("ALICE")
        assert matcher.match_positions("ALICE") is None
        assert matcher.extract_matched_text("ALICE") is None

    def test_explain_match(self):
        """Test match explanation."""
        matcher = MultiSubstringMatcher(["GO", "BE"])
        explanation = matcher.explain_match("xxGOxxxBExx")
        assert "GO" in explanation
        assert "BE" in explanation
        assert "position" in explanation

    def test_empty_substrings_raises(self):
        """Test that empty substrings raises error."""
        with pytest.raises(ValueError):
            MultiSubstringMatcher([])

    def test_pattern_string(self):
        """Test human-readable pattern string."""
        matcher = MultiSubstringMatcher(["GO", "BE", "AWE"])
        assert matcher.pattern_string == "GO BE AWE"

    def test_regex_pattern_property(self):
        """Test regex pattern property."""
        matcher = MultiSubstringMatcher(["GO", "BE"])
        assert matcher.regex_pattern  # Should be non-empty

    def test_repr(self):
        """Test string representation."""
        matcher = MultiSubstringMatcher(["GO", "BE"], fuzzy=True)
        repr_str = repr(matcher)
        assert "MultiSubstringMatcher" in repr_str
        assert "fuzzy" in repr_str


class TestRealWorldPatterns:
    """Test with real-world DID key patterns."""

    def test_did_key_prefix_match(self):
        """Test matching in real DID keys."""
        matcher = MultiSubstringMatcher(["ALICE"])
        assert matcher.match("did:key:z6MkALICExyz123")
        assert not matcher.match("did:key:z6MkBOBxyz123")

    def test_did_key_multi_substring(self):
        """Test multi-substring in real DID keys."""
        matcher = MultiSubstringMatcher(["GO", "BE", "GREAT"])
        assert matcher.match("did:key:z6MkGOxBExGREATxyz")
        assert not matcher.match("did:key:z6MkGOxGREATxBExyz")  # Wrong order

    def test_did_key_fuzzy_match(self):
        """Test fuzzy matching in real DID keys."""
        matcher = MultiSubstringMatcher(["C00L"], fuzzy=True)
        assert matcher.match("did:key:z6MkCOOLxyz")  # 0→O
        assert matcher.match("did:key:z6MkC00Lxyz")  # Exact

    def test_vanikeys_example(self):
        """Test the canonical VaniKeys example: 'GO BE AWE SOME'."""
        matcher = MultiSubstringMatcher(["GO", "BE", "AWE", "SOME"])
        # This is what VaniKeys generates!
        assert matcher.match("did:key:z6MkGOaaBExxxAWEyySOMEzzz")
        assert not matcher.match("did:key:z6MkGOaaSOMExxxAWEyyBEzzz")  # Wrong order
