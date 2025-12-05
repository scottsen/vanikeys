"""
Pattern Matching and Difficulty Estimation

Implements pattern matching for SSH fingerprints and difficulty estimation
for vanity pattern search.

Supports:
- Simple substring matching
- Regex pattern matching
- Case-sensitive and case-insensitive modes
- Pattern difficulty estimation (expected attempts, time, cost)
"""

import re
import math
from typing import Callable
from .fingerprint import extract_fingerprint_searchable


def create_pattern_matcher(
    pattern: str, case_sensitive: bool = False
) -> Callable[[str], bool]:
    """
    Create pattern matcher function for SSH fingerprints.

    Supports:
    - Simple string: "lab123"
    - Regex patterns: "lab[0-9]{3}", "dev-[a-z]+"

    Args:
        pattern: Pattern to search for
            - Simple string for substring match
            - Regex if contains special characters
        case_sensitive: Whether matching is case-sensitive

    Returns:
        Function that takes fingerprint and returns True if matches

    Example:
        >>> matcher = create_pattern_matcher("lab", case_sensitive=False)
        >>> matcher("SHA256:lab123xxxxxxxxx")
        True
        >>> matcher("SHA256:xyz999xxxxxxxxx")
        False

        >>> regex_matcher = create_pattern_matcher("lab[0-9]{3}")
        >>> regex_matcher("SHA256:lab123xxxxxxxxx")
        True
        >>> regex_matcher("SHA256:labABCxxxxxxxxx")
        False
    """
    if not case_sensitive:
        pattern = pattern.lower()

    # Detect if regex (contains special characters)
    is_regex = any(c in pattern for c in r"[](){}^$.*+?|\\")

    if is_regex:
        # Compile regex
        compiled_regex = re.compile(
            pattern, flags=0 if case_sensitive else re.IGNORECASE
        )

        def regex_matcher(fingerprint: str) -> bool:
            searchable = extract_fingerprint_searchable(fingerprint)
            if not case_sensitive:
                searchable = searchable.lower()
            return compiled_regex.search(searchable) is not None

        return regex_matcher
    else:
        # Simple substring search (faster)
        def substring_matcher(fingerprint: str) -> bool:
            searchable = extract_fingerprint_searchable(fingerprint)
            if not case_sensitive:
                searchable = searchable.lower()
            return pattern in searchable

        return substring_matcher


def matches_pattern(
    pattern: str, fingerprint: str, case_sensitive: bool = False
) -> bool:
    """
    Check if fingerprint matches pattern (convenience wrapper).

    Args:
        pattern: Pattern to search for
        fingerprint: SSH fingerprint to check
        case_sensitive: Whether matching is case-sensitive

    Returns:
        True if fingerprint matches pattern, False otherwise

    Example:
        >>> matches_pattern("lab", "SHA256:lab123xxxxxxxxx")
        True
        >>> matches_pattern("xyz", "SHA256:lab123xxxxxxxxx")
        False
    """
    matcher = create_pattern_matcher(pattern, case_sensitive)
    return matcher(fingerprint)


def estimate_pattern_difficulty(
    pattern: str, case_sensitive: bool = False
) -> dict:
    """
    Estimate search difficulty for a vanity pattern.

    Calculates:
    - Expected number of attempts (keys to generate)
    - Expected time at various speeds
    - Difficulty classification
    - Cost estimate

    Assumptions:
    - SSH fingerprint is SHA256 in base64 (43 characters)
    - Base64 charset: A-Z, a-z, 0-9, +, / = 64 characters
    - Case-insensitive reduces effective charset to ~44 characters
    - Substring match can occur at any position

    Args:
        pattern: Pattern to search for
        case_sensitive: Case-sensitive matching

    Returns:
        Dict with difficulty metrics:
            - pattern: Original pattern
            - pattern_length: Length in characters
            - expected_attempts: Average paths to search
            - expected_seconds_1m: Time at 1M keys/sec
            - expected_seconds_10m: Time at 10M keys/sec
            - expected_seconds_100m: Time at 100M keys/sec
            - difficulty_class: easy/medium/hard/extreme
            - cost_estimate_usd: Estimated cost in USD

    Example:
        >>> est = estimate_pattern_difficulty("lab", case_sensitive=False)
        >>> est['difficulty_class']
        'easy'
        >>> est['expected_attempts'] < 10000
        True

        >>> est_hard = estimate_pattern_difficulty("lab1234", case_sensitive=False)
        >>> est_hard['difficulty_class'] in ['hard', 'extreme']
        True
    """
    # Base64 character set in SSH fingerprints
    charset_size = 64  # Full base64: A-Z, a-z, 0-9, +, /

    if not case_sensitive:
        # Case-insensitive reduces effective charset
        # A/a are same, so ~44 effective characters (approximation)
        charset_size = 44

    # SHA256 base64 fingerprint length (without padding)
    fingerprint_length = 43

    # Pattern characteristics
    pattern_length = len(pattern)

    # Number of positions where pattern can start
    positions = max(1, fingerprint_length - pattern_length + 1)

    # Probability of match at one specific position
    # Each character has 1/charset_size probability
    prob_at_position = (1 / charset_size) ** pattern_length

    # Probability of match at any position (union bound approximation)
    # For rare events, P(A or B) ≈ P(A) + P(B)
    prob_any_position = min(1.0, positions * prob_at_position)

    # Expected attempts = 1 / probability
    expected_attempts = int(1 / prob_any_position) if prob_any_position > 0 else 10**15

    # Time estimates at different speeds
    keys_per_second_slow = 1_000_000  # 1M keys/sec (CPU)
    keys_per_second_medium = 10_000_000  # 10M keys/sec (multi-core)
    keys_per_second_fast = 100_000_000  # 100M keys/sec (GPU cluster)

    expected_seconds_1m = expected_attempts / keys_per_second_slow
    expected_seconds_10m = expected_attempts / keys_per_second_medium
    expected_seconds_100m = expected_attempts / keys_per_second_fast

    # Difficulty classification (based on time at 1M keys/sec)
    if expected_seconds_1m < 10:
        difficulty_class = "easy"
    elif expected_seconds_1m < 300:  # 5 minutes
        difficulty_class = "medium"
    elif expected_seconds_1m < 3600:  # 1 hour
        difficulty_class = "hard"
    else:
        difficulty_class = "extreme"

    # Cost estimation (simplified)
    # Assumptions:
    # - GPU compute: $0.008 per 1M keys generated
    # - Pricing includes margin
    cost_per_million_keys = 0.01  # $0.01 per 1M keys
    cost_estimate_raw = (expected_attempts / 1_000_000) * cost_per_million_keys

    # Price tiers based on difficulty
    if difficulty_class == "easy":
        cost_estimate_usd = max(0.50, cost_estimate_raw * 50)  # Min $0.50
    elif difficulty_class == "medium":
        cost_estimate_usd = max(2.50, cost_estimate_raw * 25)  # Min $2.50
    elif difficulty_class == "hard":
        cost_estimate_usd = max(10.00, cost_estimate_raw * 10)  # Min $10.00
    else:
        cost_estimate_usd = max(50.00, cost_estimate_raw * 5)  # Min $50.00

    return {
        "pattern": pattern,
        "pattern_length": pattern_length,
        "expected_attempts": expected_attempts,
        "expected_seconds_1m": expected_seconds_1m,
        "expected_seconds_10m": expected_seconds_10m,
        "expected_seconds_100m": expected_seconds_100m,
        "expected_time_human_1m": format_duration(expected_seconds_1m),
        "expected_time_human_10m": format_duration(expected_seconds_10m),
        "expected_time_human_100m": format_duration(expected_seconds_100m),
        "difficulty_class": difficulty_class,
        "charset_size": charset_size,
        "case_sensitive": case_sensitive,
        "cost_estimate_usd": round(cost_estimate_usd, 2),
        "probability": prob_any_position,
        "probability_human": format_probability(prob_any_position),
    }


def format_duration(seconds: float) -> str:
    """
    Format seconds as human-readable duration.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable string

    Example:
        >>> format_duration(45)
        '45.0 seconds'
        >>> format_duration(180)
        '3.0 minutes'
        >>> format_duration(7200)
        '2.0 hours'
        >>> format_duration(172800)
        '2.0 days'
    """
    if seconds < 1:
        return f"{seconds*1000:.0f} milliseconds"
    elif seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    elif seconds < 604800:
        return f"{seconds/86400:.1f} days"
    else:
        return f"{seconds/604800:.1f} weeks"


def format_probability(prob: float) -> str:
    """
    Format probability as human-readable odds.

    Args:
        prob: Probability (0.0 to 1.0)

    Returns:
        Human-readable string (e.g., "1 in 4.2M")

    Example:
        >>> format_probability(0.5)
        '1 in 2'
        >>> format_probability(0.0001)
        '1 in 10.0K'
        >>> format_probability(0.000001)
        '1 in 1.0M'
    """
    if prob <= 0:
        return "impossible"
    if prob >= 1:
        return "certain"

    odds = 1 / prob

    if odds < 1000:
        return f"1 in {odds:.0f}"
    elif odds < 1_000_000:
        return f"1 in {odds/1000:.1f}K"
    elif odds < 1_000_000_000:
        return f"1 in {odds/1_000_000:.1f}M"
    else:
        return f"1 in {odds/1_000_000_000:.1f}B"


def suggest_pattern_alternatives(pattern: str) -> list[dict]:
    """
    Suggest alternative patterns that are easier to find.

    Given a difficult pattern, suggest shorter variations.

    Args:
        pattern: Original pattern (may be too difficult)

    Returns:
        List of alternative pattern suggestions with difficulty estimates

    Example:
        >>> alternatives = suggest_pattern_alternatives("verylong")
        >>> len(alternatives) > 0
        True
        >>> alternatives[0]['pattern'] != "verylong"
        True
    """
    suggestions = []

    # Original pattern
    original_diff = estimate_pattern_difficulty(pattern, case_sensitive=False)
    suggestions.append(
        {
            "pattern": pattern,
            "reason": "Original pattern",
            "difficulty": original_diff,
        }
    )

    # If too long, suggest shorter versions
    if len(pattern) > 4:
        # First 4 characters
        short = pattern[:4]
        short_diff = estimate_pattern_difficulty(short, case_sensitive=False)
        suggestions.append(
            {
                "pattern": short,
                "reason": f"First {len(short)} characters (easier)",
                "difficulty": short_diff,
            }
        )

        # First 5 characters
        if len(pattern) > 5:
            medium = pattern[:5]
            medium_diff = estimate_pattern_difficulty(medium, case_sensitive=False)
            suggestions.append(
                {
                    "pattern": medium,
                    "reason": f"First {len(medium)} characters (moderate)",
                    "difficulty": medium_diff,
                }
            )

    # If very difficult, suggest much shorter version
    if original_diff["difficulty_class"] == "extreme":
        short = pattern[:3]
        short_diff = estimate_pattern_difficulty(short, case_sensitive=False)
        suggestions.append(
            {
                "pattern": short,
                "reason": f"First {len(short)} characters (easy)",
                "difficulty": short_diff,
            }
        )

    return suggestions


def validate_pattern(pattern: str) -> dict:
    """
    Validate that a pattern is searchable in SSH fingerprints.

    Checks:
    - Pattern is not empty
    - Characters are valid for base64 fingerprints
    - Pattern is not too long
    - Pattern is not too difficult

    Args:
        pattern: Pattern to validate

    Returns:
        Dict with:
            - valid: True if pattern is valid
            - errors: List of error messages
            - warnings: List of warning messages

    Example:
        >>> result = validate_pattern("lab123")
        >>> result['valid']
        True
        >>> result['errors']
        []

        >>> result = validate_pattern("verylongpattern123456")
        >>> result['valid']
        False
        >>> len(result['warnings']) > 0
        True
    """
    errors = []
    warnings = []

    # Check not empty
    if not pattern:
        errors.append("Pattern cannot be empty")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # Check length
    if len(pattern) > 20:
        errors.append("Pattern too long (max 20 characters)")

    # Check valid base64 characters (for simple patterns)
    # Base64: A-Z, a-z, 0-9, +, /
    # Allow regex special chars: [](){}^$.*+?|\\
    valid_chars = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/[](){}^$.*?|\\"
    )
    invalid_chars = set(pattern) - valid_chars
    if invalid_chars:
        warnings.append(
            f"Pattern contains unusual characters: {', '.join(invalid_chars)}"
        )

    # Check difficulty
    difficulty = estimate_pattern_difficulty(pattern, case_sensitive=False)
    if difficulty["difficulty_class"] == "extreme":
        time_str = difficulty['expected_time_human_1m']
        warnings.append(
            f"Pattern is extremely difficult: {time_str} expected"
        )
    elif difficulty["difficulty_class"] == "hard":
        time_str = difficulty['expected_time_human_1m']
        warnings.append(
            f"Pattern is difficult: {time_str} expected"
        )

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "difficulty": difficulty if valid else None,
    }
