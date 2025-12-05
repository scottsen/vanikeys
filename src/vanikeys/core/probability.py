"""
Probability calculator for vanity key pattern difficulty estimation.

Estimates:
- Probability of matching a pattern
- Expected number of attempts
- Human-readable odds (e.g., "1 in 4.2B")
- Cost in VaniTokens (based on difficulty)

Based on base58 encoding characteristics of DID keys.
"""

import math
from typing import Any, Dict

from ..domain import FuzzyMode, MatchMode, Pattern


class ProbabilityCalculator:
    """
    Calculate probability and cost for vanity key patterns.

    DID keys use base58 encoding: [A-Za-z0-9] excluding 0, O, I, l
    Character set: 58 characters (actually 62 - 4 confusing chars)

    For base58 (no 0, O, I, l):
        Charset: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz

    Examples:
        calc = ProbabilityCalculator()

        # Simple prefix
        pattern = Pattern(substrings=["ALICE"], mode=MatchMode.PREFIX)
        prob = calc.calculate(pattern)
        # → probability: 1/58^5 ≈ 1 in 656M

        # Multi-substring
        pattern = Pattern(
            substrings=["GO", "BE", "AWE"], mode=MatchMode.MULTI_SUBSTRING
        )
        prob = calc.calculate(pattern)
        # → Much harder: sequential substrings

        # Fuzzy matching
        pattern = Pattern(
            substrings=["B00M"], mode=MatchMode.PREFIX, fuzzy=FuzzyMode.LEETSPEAK
        )
        prob = calc.calculate(pattern)
        # → Easier: multiple valid chars per position
    """

    # Base58 charset used in DID keys (excluding 0, O, I, l)
    BASE58_CHARS = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    BASE58_SIZE = len(BASE58_CHARS)  # 58

    # Fuzzy matching multipliers (how many valid chars per position)
    FUZZY_EQUIVALENTS = {
        "0": 2,  # 0 or O
        "O": 2,  # O or 0
        "1": 2,  # 1 or I (but 1 not in base58, so effectively just I)
        "I": 2,  # I or 1
        "3": 2,  # 3 or E
        "E": 2,  # E or 3
        "4": 2,  # 4 or A
        "A": 2,  # A or 4
        "5": 2,  # 5 or S
        "S": 2,  # S or 5
        "7": 2,  # 7 or T
        "T": 2,  # T or 7
        "8": 2,  # 8 or B
        "B": 2,  # B or 8
    }

    # Cost scaling (VaniTokens per order of magnitude of difficulty)
    BASE_COST = 50  # Base cost for easiest patterns
    COST_PER_ORDER = 10  # Additional cost per 10x difficulty

    def __init__(self):
        """Initialize calculator."""
        pass

    def calculate(self, pattern: Pattern) -> Dict[str, Any]:
        """
        Calculate probability and cost for a pattern.

        Args:
            pattern: The pattern to analyze

        Returns:
            Dictionary with:
                - probability: Float probability (0.0 to 1.0)
                - expected_attempts: Expected number of keys to generate
                - odds_display: Human-readable odds (e.g., "1 in 4.2B")
                - difficulty_score: Log10 of expected attempts
                - cost_tokens: VaniTokens cost for gacha pull
                - cost_guaranteed_usd: USD cost for guaranteed mode
        """
        # Calculate based on match mode
        if pattern.mode == MatchMode.PREFIX:
            prob = self._calculate_prefix(pattern)
        elif pattern.mode == MatchMode.SUFFIX:
            prob = self._calculate_suffix(pattern)
        elif pattern.mode == MatchMode.CONTAINS:
            prob = self._calculate_contains(pattern)
        elif pattern.mode == MatchMode.MULTI_SUBSTRING:
            prob = self._calculate_multi_substring(pattern)
        elif pattern.mode == MatchMode.REGEX:
            # For regex, we can't easily calculate - use conservative estimate
            prob = self._calculate_regex_conservative(pattern)
        else:
            raise ValueError(f"Unknown match mode: {pattern.mode}")

        # Calculate derived metrics
        expected_attempts = 1.0 / prob if prob > 0 else float("inf")
        difficulty_score = math.log10(expected_attempts) if expected_attempts > 1 else 0
        odds_display = self._format_odds(expected_attempts)
        cost_tokens = self._calculate_token_cost(difficulty_score)
        cost_guaranteed_usd = self._calculate_guaranteed_cost(expected_attempts)

        return {
            "probability": prob,
            "expected_attempts": expected_attempts,
            "odds_display": odds_display,
            "difficulty_score": difficulty_score,
            "cost_tokens": cost_tokens,
            "cost_guaranteed_usd": cost_guaranteed_usd,
        }

    def _calculate_prefix(self, pattern: Pattern) -> float:
        """Calculate probability for prefix match."""
        substring = pattern.substrings[0]
        length = len(substring)

        # Base probability: 1 / (58^length)
        if pattern.fuzzy == FuzzyMode.NONE:
            return 1.0 / (self.BASE58_SIZE ** length)

        # Fuzzy matching: some positions have more valid chars
        denominator = 1.0
        for char in substring.upper():
            if char in self.FUZZY_EQUIVALENTS:
                # Multiple valid chars for this position
                valid_chars = self.FUZZY_EQUIVALENTS[char]
                denominator *= valid_chars
            else:
                # Single char (case-insensitive: 2 options if alpha)
                denominator *= 2 if char.isalpha() else 1

        # Probability is higher with fuzzy matching
        return 1.0 / denominator

    def _calculate_suffix(self, pattern: Pattern) -> float:
        """Calculate probability for suffix match."""
        # Same as prefix (suffix is just position-specific)
        return self._calculate_prefix(pattern)

    def _calculate_contains(self, pattern: Pattern) -> float:
        """
        Calculate probability for "contains anywhere" match.

        This is harder to calculate exactly, but we can approximate:
        For a key of length N and pattern of length P:
            Probability ≈ P / (58^P)

        The key might have multiple positions where the pattern could appear.
        """
        substring = pattern.substrings[0]
        length = len(substring)

        # Base probability for prefix
        base_prob = self._calculate_prefix(pattern)

        # DID keys are ~44 chars after "did:key:z6Mk"
        # So roughly 44 positions where pattern could start
        # But this is a rough approximation
        avg_key_length = 44
        num_positions = max(1, avg_key_length - length + 1)

        # Approximate probability: more positions to match
        return min(1.0, base_prob * num_positions)

    def _calculate_multi_substring(self, pattern: Pattern) -> float:
        """
        Calculate probability for multi-substring match.

        This is the VaniKeys innovation! Sequential substring matching.

        Probability approximation:
        - Each substring must appear in order
        - Rough model: probability ≈ product of individual probabilities
        - But slightly better because we have more text to work with

        Conservative estimate: treat each substring as independent.
        """
        # For each substring, calculate "contains" probability
        total_prob = 1.0

        for substring in pattern.substrings:
            # Create temporary pattern for this substring
            temp_pattern = Pattern(
                substrings=[substring],
                mode=MatchMode.CONTAINS,
                fuzzy=pattern.fuzzy,
            )
            sub_prob = self._calculate_contains(temp_pattern)
            total_prob *= sub_prob

        return total_prob

    def _calculate_regex_conservative(self, pattern: Pattern) -> float:
        """
        Conservative estimate for regex patterns.

        We can't easily calculate exact probability for arbitrary regex,
        so use a conservative estimate based on pattern complexity.
        """
        # Count character positions in pattern
        pattern_str = pattern.pattern_string
        # Rough estimate: treat like "contains" with length
        length = len(pattern_str.replace(".*", "").replace("\\", ""))
        return 1.0 / (self.BASE58_SIZE ** max(1, length))

    def _format_odds(self, expected_attempts: float) -> str:
        """
        Format expected attempts as human-readable odds.

        Examples:
            1.5 → "1 in 1.5"
            1000 → "1 in 1.0K"
            1000000 → "1 in 1.0M"
            4200000000 → "1 in 4.2B"
        """
        if expected_attempts == float("inf"):
            return "1 in ∞ (impossible)"

        if expected_attempts < 1:
            return "~100% chance"

        if expected_attempts < 1000:
            return f"1 in {expected_attempts:.1f}"

        if expected_attempts < 1_000_000:
            return f"1 in {expected_attempts / 1000:.1f}K"

        if expected_attempts < 1_000_000_000:
            return f"1 in {expected_attempts / 1_000_000:.1f}M"

        if expected_attempts < 1_000_000_000_000:
            return f"1 in {expected_attempts / 1_000_000_000:.1f}B"

        return f"1 in {expected_attempts / 1_000_000_000_000:.1f}T"

    def _calculate_token_cost(self, difficulty_score: float) -> int:
        """
        Calculate VaniToken cost based on difficulty.

        Scaling:
            difficulty 1.0 (10 attempts) → 50 tokens
            difficulty 2.0 (100 attempts) → 60 tokens
            difficulty 3.0 (1K attempts) → 70 tokens
            difficulty 6.0 (1M attempts) → 100 tokens
            difficulty 9.0 (1B attempts) → 130 tokens

        Args:
            difficulty_score: Log10 of expected attempts

        Returns:
            VaniTokens cost (50-500 range)
        """
        if difficulty_score <= 1.0:
            return self.BASE_COST

        # Linear scaling with difficulty
        cost = self.BASE_COST + int(difficulty_score * self.COST_PER_ORDER)

        # Cap at reasonable maximum
        return min(500, max(50, cost))

    def _calculate_guaranteed_cost(self, expected_attempts: float) -> float:
        """
        Calculate USD cost for guaranteed mode.

        Model:
            - Base cost: compute time for expected attempts
            - RunPod Serverless: ~$0.008 per 10K attempts
            - Add 15% premium for guaranteed delivery
            - Minimum: $5.00

        Args:
            expected_attempts: Expected number of attempts

        Returns:
            USD cost for guaranteed delivery
        """
        if expected_attempts == float("inf"):
            return 999.99  # Effectively impossible

        # Cost per 10K attempts on RunPod Serverless GPU
        cost_per_10k = 0.008

        # Base compute cost
        compute_cost = (expected_attempts / 10_000) * cost_per_10k

        # Add 15% premium for guaranteed delivery
        guaranteed_cost = compute_cost * 1.15

        # Minimum $5.00, maximum $999.99
        return min(999.99, max(5.00, guaranteed_cost))

    def explain_calculation(self, pattern: Pattern) -> str:
        """
        Generate human-readable explanation of probability calculation.

        Args:
            pattern: Pattern to explain

        Returns:
            Multi-line explanation string
        """
        result = self.calculate(pattern)

        lines = [
            f"Pattern: {pattern.pattern_string}",
            f"Mode: {pattern.mode.value}",
            f"Fuzzy: {pattern.fuzzy.value}",
            "",
            "Calculation:",
        ]

        # Explain based on mode
        if pattern.mode == MatchMode.PREFIX:
            substring = pattern.substrings[0]
            lines.append(f"  Prefix match: '{substring}' must appear at start")
            lines.append(f"  Length: {len(substring)} characters")
            lines.append(f"  Base58 charset: {self.BASE58_SIZE} characters")

            if pattern.fuzzy == FuzzyMode.NONE:
                prob_str = f"{result['probability']:.2e}"
                lines.append(
                    f"  Probability: 1 / {self.BASE58_SIZE}^{len(substring)} = "
                    f"{prob_str}"
                )
            else:
                lines.append("  Fuzzy matching increases valid characters per position")
                lines.append(f"  Probability: {result['probability']:.2e}")

        elif pattern.mode == MatchMode.MULTI_SUBSTRING:
            lines.append(
                f"  Multi-substring: {len(pattern.substrings)} substrings "
                f"in order"
            )
            for i, sub in enumerate(pattern.substrings, 1):
                lines.append(f"    {i}. '{sub}' ({len(sub)} chars)")
            lines.append("  Each substring must appear sequentially")
            lines.append(f"  Combined probability: {result['probability']:.2e}")

        # Results
        lines.extend([
            "",
            "Results:",
            f"  Expected attempts: {result['expected_attempts']:.0f}",
            f"  Odds: {result['odds_display']}",
            f"  Difficulty score: {result['difficulty_score']:.1f}",
            "",
            "Costs:",
            f"  Gacha pull: {result['cost_tokens']} VaniTokens "
            f"(~${result['cost_tokens'] * 0.05:.2f})",
            f"  Guaranteed: ${result['cost_guaranteed_usd']:.2f} USD",
        ])

        return "\n".join(lines)
