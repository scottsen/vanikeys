"""
Tests for SSH Fingerprint Computation

Tests for SSH wire format encoding and fingerprint computation.
"""

import pytest
from vanikeys.crypto.derivation import generate_master_seed, seed_to_root_keypair
from vanikeys.crypto.fingerprint import (
    ssh_public_key_to_bytes,
    ssh_public_key_to_authorized_keys_format,
    compute_ssh_fingerprint,
    compute_ssh_fingerprint_md5,
    extract_fingerprint_searchable,
    compare_fingerprints,
)


class TestSSHWireFormat:
    """Test SSH wire format encoding."""

    def test_ssh_public_key_to_bytes_format(self):
        """Wire format must follow SSH protocol."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        wire_bytes = ssh_public_key_to_bytes(pub)

        # Wire format is: string("ssh-ed25519") + string(key_data)
        # string = 4-byte length + data
        # Should be larger than 32 bytes (raw key)
        assert len(wire_bytes) > 32

    def test_ssh_public_key_to_bytes_deterministic(self):
        """Same key produces same wire format."""
        seed = b"0" * 32
        _, pub = seed_to_root_keypair(seed)

        wire1 = ssh_public_key_to_bytes(pub)
        wire2 = ssh_public_key_to_bytes(pub)

        assert wire1 == wire2


class TestAuthorizedKeysFormat:
    """Test OpenSSH authorized_keys format."""

    def test_authorized_keys_format_starts_with_type(self):
        """Format must start with 'ssh-ed25519'."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        auth_key = ssh_public_key_to_authorized_keys_format(pub)

        assert auth_key.startswith("ssh-ed25519 ")

    def test_authorized_keys_format_with_comment(self):
        """Comment appears at end."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        comment = "user@example.com"
        auth_key = ssh_public_key_to_authorized_keys_format(pub, comment)

        assert comment in auth_key
        assert auth_key.endswith(comment)

    def test_authorized_keys_format_without_comment(self):
        """Format works without comment."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        auth_key = ssh_public_key_to_authorized_keys_format(pub)

        # Should have type + base64, no trailing spaces
        parts = auth_key.split()
        assert len(parts) == 2
        assert parts[0] == "ssh-ed25519"


class TestSHA256Fingerprint:
    """Test SHA256 fingerprint computation (modern)."""

    def test_compute_ssh_fingerprint_format(self):
        """Fingerprint must start with 'SHA256:'."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        fp = compute_ssh_fingerprint(pub)

        assert fp.startswith("SHA256:")

    def test_compute_ssh_fingerprint_length(self):
        """Fingerprint must be correct length."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        fp = compute_ssh_fingerprint(pub)

        # "SHA256:" (7) + base64(32 bytes SHA256) = 7 + 43 = 50
        assert len(fp) == 50

    def test_compute_ssh_fingerprint_deterministic(self):
        """Same key produces same fingerprint."""
        seed = b"0" * 32
        _, pub = seed_to_root_keypair(seed)

        fp1 = compute_ssh_fingerprint(pub)
        fp2 = compute_ssh_fingerprint(pub)

        assert fp1 == fp2

    def test_compute_ssh_fingerprint_different_keys(self):
        """Different keys produce different fingerprints."""
        seed1 = b"0" * 32
        seed2 = b"1" * 32

        _, pub1 = seed_to_root_keypair(seed1)
        _, pub2 = seed_to_root_keypair(seed2)

        fp1 = compute_ssh_fingerprint(pub1)
        fp2 = compute_ssh_fingerprint(pub2)

        assert fp1 != fp2

    def test_compute_ssh_fingerprint_no_padding(self):
        """Base64 should not have padding '='."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        fp = compute_ssh_fingerprint(pub)

        assert "=" not in fp


class TestMD5Fingerprint:
    """Test MD5 fingerprint computation (legacy)."""

    def test_compute_ssh_fingerprint_md5_format(self):
        """MD5 fingerprint is colon-separated hex."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        fp_md5 = compute_ssh_fingerprint_md5(pub)

        assert ":" in fp_md5
        parts = fp_md5.split(":")
        assert len(parts) == 16  # 16 bytes = 16 hex pairs

    def test_compute_ssh_fingerprint_md5_hex_chars(self):
        """MD5 fingerprint contains only hex and colons."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        fp_md5 = compute_ssh_fingerprint_md5(pub)

        # Remove colons and check remaining chars are hex
        hex_chars = fp_md5.replace(":", "")
        assert all(c in "0123456789abcdef" for c in hex_chars)

    def test_compute_ssh_fingerprint_md5_deterministic(self):
        """Same key produces same MD5 fingerprint."""
        seed = b"0" * 32
        _, pub = seed_to_root_keypair(seed)

        fp1 = compute_ssh_fingerprint_md5(pub)
        fp2 = compute_ssh_fingerprint_md5(pub)

        assert fp1 == fp2


class TestFingerprintUtilities:
    """Test fingerprint utility functions."""

    def test_extract_fingerprint_searchable_sha256(self):
        """Extract searchable portion from SHA256 fingerprint."""
        fp = "SHA256:abc123def456"
        searchable = extract_fingerprint_searchable(fp)

        assert searchable == "abc123def456"
        assert not searchable.startswith("SHA256:")

    def test_extract_fingerprint_searchable_md5(self):
        """MD5 fingerprint returned as-is."""
        fp = "16:27:ac:a5"
        searchable = extract_fingerprint_searchable(fp)

        assert searchable == fp

    def test_compare_fingerprints_equal(self):
        """Compare equal fingerprints."""
        fp1 = "SHA256:abc123"
        fp2 = "SHA256:abc123"

        assert compare_fingerprints(fp1, fp2)

    def test_compare_fingerprints_different(self):
        """Compare different fingerprints."""
        fp1 = "SHA256:abc123"
        fp2 = "SHA256:xyz789"

        assert not compare_fingerprints(fp1, fp2)

    def test_compare_fingerprints_with_spacing(self):
        """Compare ignores spacing differences."""
        fp1 = "SHA256:abc123"
        fp2 = "SHA256: abc123"

        assert compare_fingerprints(fp1, fp2)

    def test_compare_fingerprints_case_insensitive(self):
        """Compare is case-insensitive."""
        fp1 = "SHA256:ABC123"
        fp2 = "sha256:abc123"

        assert compare_fingerprints(fp1, fp2)


class TestRealWorldFingerprints:
    """Test with real-world scenarios."""

    def test_multiple_keys_unique_fingerprints(self):
        """Each key has unique fingerprint."""
        parent = generate_master_seed()
        fingerprints = set()

        for i in range(100):
            from vanikeys.crypto.derivation import derive_child_keypair

            _, pub = derive_child_keypair(parent, i)
            fp = compute_ssh_fingerprint(pub)
            fingerprints.add(fp)

        # All unique
        assert len(fingerprints) == 100

    def test_fingerprint_matches_openssh_format(self):
        """Fingerprint format matches OpenSSH output."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        fp = compute_ssh_fingerprint(pub)

        # Should match format:
        # SHA256:43base64characters (no padding)
        assert fp.startswith("SHA256:")
        searchable = extract_fingerprint_searchable(fp)
        assert len(searchable) == 43
        assert "=" not in searchable
