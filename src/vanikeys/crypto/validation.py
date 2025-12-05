"""
Validation utilities for cryptographic inputs.

Provides input validation for seeds, keys, paths, and patterns to ensure
safe operation and clear error messages.
"""

from typing import Optional


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_seed(seed: bytes, name: str = "seed") -> None:
    """
    Validate a cryptographic seed.

    Args:
        seed: The seed bytes to validate
        name: Name for error messages (default: "seed")

    Raises:
        ValidationError: If seed is invalid

    Example:
        >>> validate_seed(b"0" * 32)  # OK
        >>> validate_seed(b"short")   # Raises ValidationError
    """
    if not isinstance(seed, bytes):
        raise ValidationError(
            f"{name} must be bytes, got {type(seed).__name__}"
        )

    if len(seed) != 32:
        raise ValidationError(
            f"{name} must be exactly 32 bytes, got {len(seed)} bytes"
        )


def validate_path_index(path: int, name: str = "path") -> None:
    """
    Validate a derivation path index.

    Args:
        path: The path index to validate
        name: Name for error messages (default: "path")

    Raises:
        ValidationError: If path is invalid

    Example:
        >>> validate_path_index(0)          # OK
        >>> validate_path_index(2**32 - 1)  # OK
        >>> validate_path_index(-1)         # Raises ValidationError
        >>> validate_path_index(2**32)      # Raises ValidationError
    """
    if not isinstance(path, int):
        raise ValidationError(
            f"{name} must be an integer, got {type(path).__name__}"
        )

    if path < 0:
        raise ValidationError(
            f"{name} must be non-negative, got {path}"
        )

    if path >= 2**32:
        raise ValidationError(
            f"{name} must be less than 2^32 (4,294,967,296), got {path}"
        )


def validate_pattern(pattern: str, name: str = "pattern") -> Optional[str]:
    """
    Validate a vanity pattern.

    Args:
        pattern: The pattern string to validate
        name: Name for error messages (default: "pattern")

    Returns:
        Warning message if pattern is valid but problematic, None otherwise

    Raises:
        ValidationError: If pattern is invalid

    Example:
        >>> validate_pattern("ALICE")  # OK, returns None
        >>> validate_pattern("")       # Raises ValidationError
        >>> validate_pattern("A" * 50) # Raises ValidationError
    """
    if not isinstance(pattern, str):
        raise ValidationError(
            f"{name} must be a string, got {type(pattern).__name__}"
        )

    if not pattern:
        raise ValidationError(
            f"{name} cannot be empty"
        )

    if len(pattern) > 43:
        raise ValidationError(
            f"{name} is too long (max 43 chars for SSH fingerprint), "
            f"got {len(pattern)} chars"
        )

    # Warnings for problematic patterns
    if len(pattern) >= 8:
        return (
            f"Warning: Pattern '{pattern}' is very long ({len(pattern)} chars). "
            "This will take a very long time to find. "
            "Consider using a shorter pattern."
        )

    return None


def validate_public_key_bytes(key_bytes: bytes, name: str = "public_key") -> None:
    """
    Validate public key bytes.

    Args:
        key_bytes: The public key bytes to validate
        name: Name for error messages (default: "public_key")

    Raises:
        ValidationError: If key bytes are invalid

    Example:
        >>> validate_public_key_bytes(b"0" * 32)  # OK
        >>> validate_public_key_bytes(b"short")  # Raises ValidationError
    """
    if not isinstance(key_bytes, bytes):
        raise ValidationError(
            f"{name} must be bytes, got {type(key_bytes).__name__}"
        )

    if len(key_bytes) != 32:
        raise ValidationError(
            f"{name} must be exactly 32 bytes (Ed25519), got {len(key_bytes)} bytes"
        )


def validate_fingerprint(fingerprint: str, name: str = "fingerprint") -> None:
    """
    Validate SSH fingerprint format.

    Args:
        fingerprint: The fingerprint string to validate
        name: Name for error messages (default: "fingerprint")

    Raises:
        ValidationError: If fingerprint is invalid

    Example:
        >>> validate_fingerprint("SHA256:abc123...")  # OK
        >>> validate_fingerprint("invalid")           # Raises ValidationError
    """
    if not isinstance(fingerprint, str):
        raise ValidationError(
            f"{name} must be a string, got {type(fingerprint).__name__}"
        )

    if not fingerprint.startswith("SHA256:"):
        raise ValidationError(
            f"{name} must start with 'SHA256:', got: {fingerprint[:20]}..."
        )

    # Extract the base64 part
    b64_part = fingerprint[7:]  # Skip "SHA256:"

    if len(b64_part) != 43:
        raise ValidationError(
            f"{name} must have 43 base64 characters after 'SHA256:', "
            f"got {len(b64_part)} chars"
        )

    # Check for valid base64 characters (A-Za-z0-9+/)
    valid_chars = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    )
    invalid_chars = set(b64_part) - valid_chars

    if invalid_chars:
        raise ValidationError(
            f"{name} contains invalid base64 characters: {invalid_chars}"
        )


def validate_password(password: str, min_length: int = 8) -> Optional[str]:
    """
    Validate a password for seed encryption.

    Args:
        password: The password to validate
        min_length: Minimum password length (default: 8)

    Returns:
        Warning message if password is weak but acceptable, None otherwise

    Raises:
        ValidationError: If password is invalid

    Example:
        >>> validate_password("strong_password123")  # OK
        >>> validate_password("weak")                # Raises ValidationError
    """
    if not isinstance(password, str):
        raise ValidationError(
            f"password must be a string, got {type(password).__name__}"
        )

    if len(password) < min_length:
        raise ValidationError(
            f"password must be at least {min_length} characters, "
            f"got {len(password)} chars"
        )

    # Check for common weak patterns
    if password.lower() in ["password", "12345678", "qwerty", "abc12345"]:
        raise ValidationError(
            "password is too common and easily guessable"
        )

    # Warnings for weak but acceptable passwords
    if len(password) < 12:
        return (
            "Warning: Password is short. Consider using at least 12 characters "
            "for better security."
        )

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    variety = sum([has_upper, has_lower, has_digit, has_special])

    if variety < 3:
        return (
            "Warning: Password could be stronger. Consider including uppercase, "
            "lowercase, digits, and special characters."
        )

    return None
