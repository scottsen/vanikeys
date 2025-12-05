"""
Domain model for vanity key patterns.

Pure Python models representing patterns users want to match.
No I/O, no external dependencies - just domain logic.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class MatchMode(Enum):
    """How the pattern should be matched."""
    PREFIX = "prefix"           # Match at start: "ALICE..."
    SUFFIX = "suffix"           # Match at end: "...ALICE"
    CONTAINS = "contains"       # Match anywhere: "...ALICE..."
    MULTI_SUBSTRING = "multi"   # Multiple substrings in order: "GO BE AWE SOME"
    REGEX = "regex"             # Full regex support


class FuzzyMode(Enum):
    """Fuzzy matching rules."""
    NONE = "none"               # Exact match only
    LEETSPEAK = "leetspeak"     # 0→O, 1→I, 3→E, 4→A, 5→S, 7→T, 8→B
    HOMOGLYPHS = "homoglyphs"   # Visually similar: O→0, I→1, etc.
    PHONETIC = "phonetic"       # Sound-alike: C→K, PH→F


@dataclass
class Pattern:
    """
    A vanity key pattern specification.

    Examples:
        - Simple prefix: Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)
        - Multi-substring: Pattern(substrings=["GO", "BE", "AWE", "SOME"],
                                   mode=MatchMode.MULTI_SUBSTRING)
        - Fuzzy: Pattern(substrings=["B00M"], mode=MatchMode.PREFIX,
                        fuzzy=FuzzyMode.LEETSPEAK)
    """

    # Core pattern specification
    substrings: List[str]  # List of substrings to match
    mode: MatchMode = MatchMode.PREFIX
    fuzzy: FuzzyMode = FuzzyMode.NONE
    case_sensitive: bool = False

    # Computed properties (set after creation)
    difficulty: Optional[float] = None  # Estimated keys to generate
    odds: Optional[str] = None          # Human-readable odds (e.g., "1 in 4.2B")
    cost_tokens: Optional[int] = None   # VaniTokens cost for gacha pull
    cost_guaranteed: Optional[float] = None  # USD cost for guaranteed mode

    # Metadata
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    id: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        """Validate pattern after creation."""
        if not self.substrings:
            raise ValueError("Pattern must have at least one substring")

        # Normalize case if needed
        if not self.case_sensitive:
            self.substrings = [s.upper() for s in self.substrings]

        # Validate multi-substring mode
        if self.mode == MatchMode.MULTI_SUBSTRING and len(self.substrings) < 2:
            raise ValueError("Multi-substring mode requires at least 2 substrings")

    @property
    def pattern_string(self) -> str:
        """Human-readable pattern string."""
        if self.mode == MatchMode.MULTI_SUBSTRING:
            return " ".join(self.substrings)
        return self.substrings[0]

    @property
    def is_multi_substring(self) -> bool:
        """Is this a multi-substring pattern?"""
        return self.mode == MatchMode.MULTI_SUBSTRING

    @property
    def has_fuzzy(self) -> bool:
        """Does this pattern use fuzzy matching?"""
        return self.fuzzy != FuzzyMode.NONE

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "substrings": self.substrings,
            "mode": self.mode.value,
            "fuzzy": self.fuzzy.value,
            "case_sensitive": self.case_sensitive,
            "difficulty": self.difficulty,
            "odds": self.odds,
            "cost_tokens": self.cost_tokens,
            "cost_guaranteed": self.cost_guaranteed,
            "user_id": self.user_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        """Create from dictionary."""
        return cls(
            substrings=data["substrings"],
            mode=MatchMode(data["mode"]),
            fuzzy=FuzzyMode(data.get("fuzzy", "none")),
            case_sensitive=data.get("case_sensitive", False),
            difficulty=data.get("difficulty"),
            odds=data.get("odds"),
            cost_tokens=data.get("cost_tokens"),
            cost_guaranteed=data.get("cost_guaranteed"),
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
            id=data.get("id"),
        )
