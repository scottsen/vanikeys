"""Difficulty calculation for vanity key generation."""

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from vanikeys.core.types import PatternConfig, PatternMatchType


@dataclass
class DifficultyEstimate:
    """Represents difficulty estimate for finding a vanity pattern."""

    pattern: str
    match_type: PatternMatchType
    average_attempts: int
    min_attempts: int
    max_attempts: int  # 99.9% confidence
    keyspace_size: int

    def estimated_time(self, keys_per_second: float) -> timedelta:
        """Calculate estimated time to find pattern."""
        seconds = self.average_attempts / keys_per_second
        return timedelta(seconds=seconds)

    def time_range(
        self,
        keys_per_second: float
    ) -> tuple[timedelta, timedelta]:
        """Calculate time range (min to 99.9% confidence)."""
        min_time = timedelta(seconds=self.min_attempts / keys_per_second)
        max_time = timedelta(seconds=self.max_attempts / keys_per_second)
        return min_time, max_time

    @property
    def difficulty_rating(self) -> Literal["trivial", "easy", "moderate", "hard", "extreme"]:
        """Human-readable difficulty rating."""
        if self.average_attempts < 10_000:
            return "trivial"
        elif self.average_attempts < 1_000_000:
            return "easy"
        elif self.average_attempts < 100_000_000:
            return "moderate"
        elif self.average_attempts < 10_000_000_000:
            return "hard"
        else:
            return "extreme"

    def __str__(self) -> str:
        """Human-readable difficulty description."""
        return (
            f"Pattern: '{self.pattern}' ({self.match_type.value})\n"
            f"Average attempts: {self.average_attempts:,}\n"
            f"Difficulty: {self.difficulty_rating}\n"
            f"Keyspace size: {self.keyspace_size:,}"
        )


class DifficultyCalculator:
    """Calculate difficulty for vanity patterns."""

    # Common encoding alphabet sizes
    ALPHABET_SIZES = {
        "base58": 58,     # Bitcoin/Base58 (excludes 0, O, I, l)
        "base64": 64,     # Standard base64
        "hex": 16,        # Hexadecimal
        "base32": 32,     # Base32
        "decimal": 10,    # 0-9
    }

    def __init__(self, alphabet: str = "base58"):
        """
        Initialize calculator with alphabet size.

        Args:
            alphabet: Either a known alphabet name or "custom:N" where N is size
        """
        if alphabet in self.ALPHABET_SIZES:
            self.alphabet_size = self.ALPHABET_SIZES[alphabet]
        elif alphabet.startswith("custom:"):
            self.alphabet_size = int(alphabet.split(":")[1])
        else:
            raise ValueError(
                f"Unknown alphabet: {alphabet}. "
                f"Use one of {list(self.ALPHABET_SIZES.keys())} or 'custom:N'"
            )

    def calculate(self, config: PatternConfig) -> DifficultyEstimate:
        """
        Calculate difficulty for a pattern configuration.

        Args:
            config: Pattern configuration

        Returns:
            Difficulty estimate with attempt counts and keyspace size
        """
        pattern_length = len(config.pattern)

        if config.match_type == PatternMatchType.PREFIX:
            return self._calculate_prefix(config.pattern, pattern_length)
        elif config.match_type == PatternMatchType.SUFFIX:
            return self._calculate_suffix(config.pattern, pattern_length)
        elif config.match_type == PatternMatchType.CONTAINS:
            return self._calculate_contains(config.pattern, pattern_length)
        else:  # REGEX
            return self._calculate_regex(config.pattern)

    def _calculate_prefix(self, pattern: str, length: int) -> DifficultyEstimate:
        """Calculate difficulty for prefix matching."""
        # For prefix: need to match exactly at position 0
        # Probability = 1 / (alphabet_size ** pattern_length)
        keyspace = self.alphabet_size ** length
        average = keyspace

        # Min: Could get lucky on first try
        min_attempts = 1

        # Max: 99.9% confidence interval
        # P(not found after N tries) = (1 - 1/keyspace)^N < 0.001
        # N > ln(0.001) / ln(1 - 1/keyspace) ≈ -ln(0.001) * keyspace
        max_attempts = int(math.ceil(-math.log(0.001) * keyspace))

        return DifficultyEstimate(
            pattern=pattern,
            match_type=PatternMatchType.PREFIX,
            average_attempts=average,
            min_attempts=min_attempts,
            max_attempts=max_attempts,
            keyspace_size=keyspace,
        )

    def _calculate_suffix(self, pattern: str, length: int) -> DifficultyEstimate:
        """Calculate difficulty for suffix matching."""
        # Same as prefix - position doesn't matter for difficulty
        return self._calculate_prefix(pattern, length)

    def _calculate_contains(
        self,
        pattern: str,
        length: int,
        target_string_length: int = 50  # Typical address length
    ) -> DifficultyEstimate:
        """Calculate difficulty for substring matching."""
        # Contains is easier than prefix because pattern can appear anywhere
        # Approximate: probability ≈ (string_length - pattern_length + 1) / keyspace
        # So attempts ≈ keyspace / (string_length - pattern_length + 1)

        keyspace = self.alphabet_size ** length
        num_positions = max(1, target_string_length - length + 1)
        average = keyspace // num_positions

        min_attempts = 1
        max_attempts = int(math.ceil(-math.log(0.001) * average))

        return DifficultyEstimate(
            pattern=pattern,
            match_type=PatternMatchType.CONTAINS,
            average_attempts=average,
            min_attempts=min_attempts,
            max_attempts=max_attempts,
            keyspace_size=keyspace,
        )

    def _calculate_regex(self, pattern: str) -> DifficultyEstimate:
        """Calculate difficulty for regex matching (approximation)."""
        # Regex difficulty is hard to calculate precisely
        # Use heuristic: treat as "contains" with length = pattern length
        # This is conservative (underestimates difficulty)

        # Remove regex special chars for length estimate
        import re
        clean_pattern = re.sub(r'[^a-zA-Z0-9]', '', pattern)
        length = max(1, len(clean_pattern))

        keyspace = self.alphabet_size ** length
        average = keyspace // 10  # Very rough approximation

        min_attempts = 1
        max_attempts = int(math.ceil(-math.log(0.001) * average))

        return DifficultyEstimate(
            pattern=pattern,
            match_type=PatternMatchType.REGEX,
            average_attempts=average,
            min_attempts=min_attempts,
            max_attempts=max_attempts,
            keyspace_size=keyspace,
        )


def format_difficulty_table() -> str:
    """Generate a reference table of difficulties for different pattern lengths."""
    calc = DifficultyCalculator("base58")

    lines = [
        "Vanity Pattern Difficulty (Base58 Prefix)",
        "=" * 70,
        f"{'Length':<8} {'Attempts':<15} {'@ 300K/s':<15} {'@ 50M/s (GPU)':<15}",
        "-" * 70,
    ]

    for length in range(1, 9):
        pattern = "X" * length
        config = PatternConfig(pattern=pattern, match_type=PatternMatchType.PREFIX)
        difficulty = calc.calculate(config)

        time_cpu = difficulty.estimated_time(300_000)
        time_gpu = difficulty.estimated_time(50_000_000)

        lines.append(
            f"{length:<8} {difficulty.average_attempts:<15,} "
            f"{str(time_cpu):<15} {str(time_gpu):<15}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    # Demo difficulty calculations
    print(format_difficulty_table())
