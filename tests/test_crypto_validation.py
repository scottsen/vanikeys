"""
Tests for cryptographic input validation.

Validates that validation functions catch invalid inputs and provide
clear error messages.
"""

import pytest
from vanikeys.crypto.validation import (
    ValidationError,
    validate_seed,
    validate_path_index,
    validate_pattern,
    validate_public_key_bytes,
    validate_fingerprint,
    validate_password,
)


class TestSeedValidation:
    """Test seed validation."""

    def test_valid_seed(self):
        """Valid 32-byte seed passes."""
        seed = b"0" * 32
        validate_seed(seed)  # Should not raise

    def test_seed_wrong_type(self):
        """Seed must be bytes, not string."""
        with pytest.raises(ValidationError, match="must be bytes"):
            validate_seed("not bytes")  # type: ignore

    def test_seed_too_short(self):
        """Seed must be 32 bytes."""
        with pytest.raises(ValidationError, match="exactly 32 bytes"):
            validate_seed(b"short")

    def test_seed_too_long(self):
        """Seed must be 32 bytes."""
        with pytest.raises(ValidationError, match="exactly 32 bytes"):
            validate_seed(b"0" * 64)

    def test_custom_name(self):
        """Custom name appears in error message."""
        with pytest.raises(ValidationError, match="master_seed"):
            validate_seed(b"short", name="master_seed")


class TestPathIndexValidation:
    """Test path index validation."""

    def test_valid_path_zero(self):
        """Path 0 is valid."""
        validate_path_index(0)  # Should not raise

    def test_valid_path_max(self):
        """Path 2^32 - 1 is valid (max uint32)."""
        validate_path_index(2**32 - 1)  # Should not raise

    def test_valid_path_middle(self):
        """Middle range paths are valid."""
        validate_path_index(1000000)  # Should not raise

    def test_path_wrong_type(self):
        """Path must be int."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_path_index("not int")  # type: ignore

    def test_path_negative(self):
        """Path cannot be negative."""
        with pytest.raises(ValidationError, match="must be non-negative"):
            validate_path_index(-1)

    def test_path_too_large(self):
        """Path cannot exceed 2^32."""
        with pytest.raises(ValidationError, match="less than 2\\^32"):
            validate_path_index(2**32)

    def test_custom_name(self):
        """Custom name appears in error message."""
        with pytest.raises(ValidationError, match="child_path"):
            validate_path_index(-1, name="child_path")


class TestPatternValidation:
    """Test pattern validation."""

    def test_valid_pattern_short(self):
        """Short pattern is valid."""
        warning = validate_pattern("ABC")
        assert warning is None

    def test_valid_pattern_medium(self):
        """Medium pattern is valid."""
        warning = validate_pattern("ALICE")
        assert warning is None

    def test_valid_pattern_long_with_warning(self):
        """Long pattern is valid but returns warning."""
        warning = validate_pattern("VERYLONGPATTERN")
        assert warning is not None
        assert "very long" in warning.lower()

    def test_pattern_wrong_type(self):
        """Pattern must be string."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_pattern(123)  # type: ignore

    def test_pattern_empty(self):
        """Pattern cannot be empty."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_pattern("")

    def test_pattern_too_long(self):
        """Pattern cannot exceed 43 chars (SSH fingerprint limit)."""
        with pytest.raises(ValidationError, match="too long"):
            validate_pattern("A" * 44)

    def test_pattern_max_length_valid(self):
        """Pattern with 43 chars is valid (but warns)."""
        warning = validate_pattern("A" * 43)
        assert warning is not None

    def test_custom_name(self):
        """Custom name appears in error message."""
        with pytest.raises(ValidationError, match="user_pattern"):
            validate_pattern("", name="user_pattern")


class TestPublicKeyBytesValidation:
    """Test public key bytes validation."""

    def test_valid_public_key(self):
        """Valid 32-byte public key passes."""
        key = b"0" * 32
        validate_public_key_bytes(key)  # Should not raise

    def test_public_key_wrong_type(self):
        """Public key must be bytes."""
        with pytest.raises(ValidationError, match="must be bytes"):
            validate_public_key_bytes("not bytes")  # type: ignore

    def test_public_key_too_short(self):
        """Public key must be 32 bytes."""
        with pytest.raises(ValidationError, match="exactly 32 bytes"):
            validate_public_key_bytes(b"short")

    def test_public_key_too_long(self):
        """Public key must be 32 bytes."""
        with pytest.raises(ValidationError, match="exactly 32 bytes"):
            validate_public_key_bytes(b"0" * 64)

    def test_custom_name(self):
        """Custom name appears in error message."""
        with pytest.raises(ValidationError, match="root_key"):
            validate_public_key_bytes(b"short", name="root_key")


class TestFingerprintValidation:
    """Test SSH fingerprint validation."""

    def test_valid_fingerprint(self):
        """Valid SHA256 fingerprint passes."""
        fp = "SHA256:" + "a" * 43  # Valid 43-char base64
        validate_fingerprint(fp)  # Should not raise

    def test_fingerprint_wrong_type(self):
        """Fingerprint must be string."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_fingerprint(123)  # type: ignore

    def test_fingerprint_missing_prefix(self):
        """Fingerprint must start with SHA256:."""
        with pytest.raises(ValidationError, match="must start with 'SHA256:'"):
            validate_fingerprint("abcdefghijklmnopqrstuvwxyz")

    def test_fingerprint_wrong_length(self):
        """Fingerprint must have exactly 43 base64 chars."""
        with pytest.raises(ValidationError, match="43 base64 characters"):
            validate_fingerprint("SHA256:short")

    def test_fingerprint_invalid_characters(self):
        """Fingerprint must contain only valid base64 chars."""
        with pytest.raises(ValidationError, match="invalid base64 characters"):
            # 43 chars but includes invalid @ and # characters
            validate_fingerprint("SHA256:" + "a" * 35 + "@#$%^&*(")

    def test_custom_name(self):
        """Custom name appears in error message."""
        with pytest.raises(ValidationError, match="ssh_fingerprint"):
            validate_fingerprint("invalid", name="ssh_fingerprint")


class TestPasswordValidation:
    """Test password validation."""

    def test_valid_strong_password(self):
        """Strong password passes with no warning."""
        warning = validate_password("MyStr0ng!Password123")
        assert warning is None

    def test_valid_short_password_with_warning(self):
        """Short but acceptable password returns warning."""
        warning = validate_password("Pass123!")
        assert warning is not None
        assert "short" in warning.lower()

    def test_valid_simple_password_with_warning(self):
        """Simple password returns warning."""
        warning = validate_password("abcdefghijkl")  # 12 chars, all lowercase
        assert warning is not None
        assert "stronger" in warning.lower()

    def test_password_wrong_type(self):
        """Password must be string."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_password(12345678)  # type: ignore

    def test_password_too_short(self):
        """Password must be at least 8 chars by default."""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            validate_password("short")

    def test_password_custom_min_length(self):
        """Can specify custom minimum length."""
        with pytest.raises(ValidationError, match="at least 12 characters"):
            validate_password("password11", min_length=12)

    def test_password_common_weak(self):
        """Common weak passwords are rejected."""
        weak_passwords = ["password", "12345678", "abc12345"]

        for weak in weak_passwords:
            with pytest.raises(ValidationError, match="too common"):
                validate_password(weak)

    def test_password_minimum_length_valid(self):
        """Minimum length password is valid but may warn."""
        result = validate_password("Pass123!")
        # Should not raise, but may return warning
        assert result is None or isinstance(result, str)


class TestValidationErrorMessages:
    """Test that error messages are clear and helpful."""

    def test_seed_error_includes_actual_length(self):
        """Seed error message includes actual length."""
        try:
            validate_seed(b"short")
        except ValidationError as e:
            assert "5 bytes" in str(e)

    def test_path_error_includes_actual_value(self):
        """Path error message includes actual value."""
        try:
            validate_path_index(-5)
        except ValidationError as e:
            assert "-5" in str(e)

    def test_pattern_error_includes_actual_length(self):
        """Pattern error message includes actual length."""
        try:
            validate_pattern("A" * 50)
        except ValidationError as e:
            assert "50 chars" in str(e)


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    def test_validate_user_input_pattern(self):
        """Validate pattern from user input."""
        # Good pattern
        warning = validate_pattern("ALICE")
        assert warning is None

        # Long pattern - valid but warns
        warning = validate_pattern("GOBEAWESOME")
        assert warning is not None
        assert "very long" in warning.lower()

    def test_validate_derived_seed(self):
        """Validate derived child seed."""
        parent_seed = b"\x00" * 32
        # In real code, this would be derived
        child_seed = parent_seed  # Simplified for test

        validate_seed(child_seed)  # Should not raise

    def test_validate_path_range(self):
        """Validate paths across full uint32 range."""
        # Common paths
        validate_path_index(0)
        validate_path_index(1)
        validate_path_index(100)
        validate_path_index(1000000)

        # Edge cases
        validate_path_index(2**32 - 1)  # Max valid

        # Invalid
        with pytest.raises(ValidationError):
            validate_path_index(2**32)

    def test_validate_encryption_password(self):
        """Validate password for seed encryption."""
        # Strong password
        warning = validate_password("MyVeryStr0ng!Pass#2025")
        assert warning is None

        # Weak but acceptable
        warning = validate_password("mypass123")
        assert warning is not None

        # Too weak
        with pytest.raises(ValidationError):
            validate_password("short")

    def test_validate_ssh_fingerprint_from_openssh(self):
        """Validate fingerprint from OpenSSH output."""
        # Typical OpenSSH fingerprint format
        fp = "SHA256:abcDEF123xyz+/ABCDEFGHIJKLMNOPQRSTUVWXYZ789"
        validate_fingerprint(fp)  # Should not raise
