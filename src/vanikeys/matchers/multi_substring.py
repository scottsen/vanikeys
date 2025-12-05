"""
Multi-substring matcher with fuzzy matching support.

This is the core innovation of VaniKeys: matching multiple substrings
in sequential order (e.g., "GO BE AWE SOME") with optional fuzzy rules.

Examples:
    # Exact match
    matcher = MultiSubstringMatcher(["GO", "BE", "AWE", "SOME"])
    matcher.match("did:key:z6MkGOxxxBExxxAWExxxSOMExxx")  # True

    # Fuzzy match (0→O, 1→I, 3→E)
    matcher = MultiSubstringMatcher(["B00M"], fuzzy=True)
    matcher.match("did:key:z6MkB00Mxxx")  # True (exact)
    matcher.match("did:key:z6MkBOOMxxx")  # True (fuzzy: 0→O)
"""

from typing import List, Tuple, Optional
import re


class FuzzyRules:
    """
    Fuzzy matching rules for leetspeak-style substitutions.

    Rules:
        0 → O (and vice versa)
        1 → I (and vice versa)
        3 → E (and vice versa)
        4 → A (and vice versa)
        5 → S (and vice versa)
        7 → T (and vice versa)
        8 → B (and vice versa)
    """

    # Character equivalence mapping (bidirectional)
    # First element is canonical form (letters preferred for readability)
    EQUIVALENTS = {
        "0": ["O", "0"],
        "O": ["O", "0"],
        "1": ["I", "1"],
        "I": ["I", "1"],
        "3": ["E", "3"],
        "E": ["E", "3"],
        "4": ["A", "4"],
        "A": ["A", "4"],
        "5": ["S", "5"],
        "S": ["S", "5"],
        "7": ["T", "7"],
        "T": ["T", "7"],
        "8": ["B", "8"],
        "B": ["B", "8"],
    }

    @classmethod
    def to_regex_pattern(cls, substring: str) -> str:
        """
        Convert a substring to a regex pattern with fuzzy matching.

        Example:
            "B00M" → "[B8][0O][0O][Mm]"
            "GO" → "[Gg][0O]"

        Args:
            substring: The substring to convert (case-insensitive)

        Returns:
            Regex pattern string with character classes for fuzzy matching
        """
        pattern_parts = []
        for char in substring.upper():
            if char in cls.EQUIVALENTS:
                # Create character class with all equivalents
                equiv_chars = cls.EQUIVALENTS[char]
                # Include both upper and lower case
                char_class = []
                for c in equiv_chars:
                    char_class.append(c)
                    char_class.append(c.lower())
                # Remove duplicates and create character class
                unique_chars = "".join(sorted(set(char_class)))
                pattern_parts.append(f"[{unique_chars}]")
            else:
                # No fuzzy match, just case-insensitive
                pattern_parts.append(f"[{char}{char.lower()}]")

        return "".join(pattern_parts)

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalize text by converting fuzzy equivalents to canonical form.

        Example:
            "B00M" → "BOOM"
            "G0" → "GO"

        This is useful for probability calculations.
        """
        normalized = []
        for char in text.upper():
            if char in cls.EQUIVALENTS:
                # Use the first (canonical) equivalent
                normalized.append(cls.EQUIVALENTS[char][0])
            else:
                normalized.append(char)
        return "".join(normalized)


class MultiSubstringMatcher:
    """
    Matches multiple substrings in sequential order.

    The substrings must appear in the given order, but can have any
    characters between them.

    Examples:
        # Simple case
        matcher = MultiSubstringMatcher(["GO", "BE"])
        matcher.match("GOxxxBE")  # True
        matcher.match("BExxxGO")  # False (wrong order)

        # Multi-substring (VaniKeys innovation!)
        matcher = MultiSubstringMatcher(["GO", "BE", "AWE", "SOME"])
        matcher.match("GOxxxBExxxAWExxxSOME")  # True
        matcher.match_positions("GOxxxBExxxAWExxxSOME")
        # → [(0, 2), (5, 7), (10, 13), (16, 20)]

        # Fuzzy matching
        matcher = MultiSubstringMatcher(["B00M"], fuzzy=True)
        matcher.match("BOOM")  # True (0→O)
        matcher.match("B00M")  # True (exact)
    """

    def __init__(
        self,
        substrings: List[str],
        fuzzy: bool = False,
        case_sensitive: bool = False,
    ):
        """
        Initialize matcher.

        Args:
            substrings: List of substrings to match in order
            fuzzy: Enable fuzzy matching (leetspeak rules)
            case_sensitive: Enforce case-sensitive matching
        """
        if not substrings:
            raise ValueError("Must provide at least one substring")

        self.substrings = substrings
        self.fuzzy = fuzzy
        self.case_sensitive = case_sensitive

        # Build regex pattern
        self._pattern = self._build_pattern()
        self._regex = re.compile(self._pattern)

    def _build_pattern(self) -> str:
        """
        Build regex pattern for matching.

        Returns:
            Regex pattern string
        """
        pattern_parts = []

        for substring in self.substrings:
            if self.fuzzy:
                # Use fuzzy character classes
                sub_pattern = FuzzyRules.to_regex_pattern(substring)
            else:
                # Exact match (case-insensitive if needed)
                if self.case_sensitive:
                    sub_pattern = re.escape(substring)
                else:
                    # Case-insensitive character classes
                    sub_pattern = "".join(
                        f"[{c.upper()}{c.lower()}]" if c.isalpha() else re.escape(c)
                        for c in substring
                    )

            pattern_parts.append(sub_pattern)

        # Join with .*? (non-greedy any characters)
        # This ensures substrings appear in order
        return ".*?".join(pattern_parts)

    def match(self, text: str) -> bool:
        """
        Check if text matches the pattern.

        Args:
            text: Text to check (typically a DID key)

        Returns:
            True if pattern matches, False otherwise
        """
        return self._regex.search(text) is not None

    def match_positions(self, text: str) -> Optional[List[Tuple[int, int]]]:
        """
        Find match positions for each substring.

        Args:
            text: Text to check

        Returns:
            List of (start, end) positions for each substring, or None if no match
        """
        # Try to match the full pattern
        match_obj = self._regex.search(text)
        if not match_obj:
            return None

        # Now find individual substring positions
        positions = []
        search_start = match_obj.start()

        for substring in self.substrings:
            # Build individual regex for this substring
            if self.fuzzy:
                sub_pattern = FuzzyRules.to_regex_pattern(substring)
            else:
                if self.case_sensitive:
                    sub_pattern = re.escape(substring)
                else:
                    sub_pattern = "".join(
                        f"[{c.upper()}{c.lower()}]" if c.isalpha() else re.escape(c)
                        for c in substring
                    )

            # Search from current position
            sub_match = re.search(sub_pattern, text[search_start:])
            if sub_match:
                actual_start = search_start + sub_match.start()
                actual_end = search_start + sub_match.end()
                positions.append((actual_start, actual_end))
                # Next substring must come after this one
                search_start = actual_end
            else:
                # This shouldn't happen if the full pattern matched
                return None

        return positions

    def extract_matched_text(self, text: str) -> Optional[str]:
        """
        Extract the full matched text (from first substring to last).

        Args:
            text: Text to check

        Returns:
            Matched portion of text, or None if no match
        """
        positions = self.match_positions(text)
        if not positions:
            return None

        # Return from start of first match to end of last match
        first_start = positions[0][0]
        last_end = positions[-1][1]
        return text[first_start:last_end]

    def explain_match(self, text: str) -> str:
        """
        Generate human-readable explanation of match.

        Args:
            text: Text to check

        Returns:
            Explanation string
        """
        positions = self.match_positions(text)
        if not positions:
            return f"No match found for pattern: {' '.join(self.substrings)}"

        # Build explanation showing each substring position
        lines = [f"Matched pattern: {' '.join(self.substrings)}"]
        lines.append(f"In text: {text}")
        lines.append("")

        for i, (start, end) in enumerate(positions):
            matched_text = text[start:end]
            lines.append(
                f"  {self.substrings[i]:15} → position {start:3}-{end:3}: "
                f"{matched_text}"
            )

        return "\n".join(lines)

    @property
    def pattern_string(self) -> str:
        """Human-readable pattern string."""
        return " ".join(self.substrings)

    @property
    def regex_pattern(self) -> str:
        """The compiled regex pattern."""
        return self._pattern

    def __repr__(self) -> str:
        """String representation."""
        fuzzy_str = " (fuzzy)" if self.fuzzy else ""
        return f"MultiSubstringMatcher({self.substrings}{fuzzy_str})"
