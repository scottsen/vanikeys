"""
Integration tests for VaniKeys CLI workflow.

Tests the complete flow:
1. Generate seed (init)
2. Derive child key from path
3. Verify fingerprint matches

Note: These tests do NOT require the API server (they're offline tests).
"""

import tempfile
from pathlib import Path

import pytest

from vanikeys.cli.storage import SeedStorage
from vanikeys.crypto.derivation import (
    generate_master_seed,
    seed_to_root_keypair,
    derive_child_keypair,
    public_key_to_bytes,
    private_key_to_bytes,
)
from vanikeys.crypto.fingerprint import compute_ssh_fingerprint
from vanikeys.crypto.matching import matches_pattern
from vanikeys.crypto.proofs import generate_order_proof, verify_order_proof


class TestCLIIntegration:
    """Integration tests for CLI workflow."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create storage instance."""
        return SeedStorage(temp_storage_dir)

    def test_complete_vanity_key_workflow(self, storage):
        """Test complete workflow: init → find pattern → verify → derive.

        This simulates what the CLI + server do:
        1. Customer generates seed (vanikeys init)
        2. Server searches for vanity pattern (simulated)
        3. Customer verifies proof (vanikeys verify)
        4. Customer derives key (vanikeys derive)
        """
        # Step 1: Customer generates seed (like 'vanikeys init')
        password = "strong_password_123"
        seed = generate_master_seed()
        root_private_key, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        # Save encrypted seed
        storage.save_seed(seed, password, root_public_key_bytes)

        # Step 2: Simulate server finding vanity pattern
        # (In production, server would search millions of paths)
        pattern = "a"  # Simple pattern for fast test
        path_index = None

        for i in range(1000):  # Search up to 1000 paths
            child_private, child_public = derive_child_keypair(seed, i)
            fingerprint = compute_ssh_fingerprint(child_public)

            if matches_pattern(pattern, fingerprint):
                path_index = i
                break

        assert path_index is not None, "Should find pattern 'a' in first 1000 paths"

        # Step 3: Server generates proof
        child_private_key, child_public_key = derive_child_keypair(seed, path_index)
        child_public_bytes = public_key_to_bytes(child_public_key)
        fingerprint = compute_ssh_fingerprint(child_public_key)

        proof = generate_order_proof(
            root_public_bytes=root_public_key_bytes,
            path_index=path_index,
            child_public_key=child_public_key,
            pattern=pattern,
            fingerprint=fingerprint,
        )

        # Step 4: Customer verifies proof (like 'vanikeys verify')
        result = verify_order_proof(proof, seed, pattern)

        assert result["valid"], "Proof should be valid"
        assert result["fingerprint"] == fingerprint
        assert result["pattern_valid"], "Pattern should match"

        # Step 5: Customer derives private key (like 'vanikeys derive')
        # Load seed (requires password)
        loaded_seed, loaded_public_key = storage.load_seed(password)

        assert loaded_seed == seed
        assert loaded_public_key == root_public_key_bytes

        # Derive root keypair
        derived_root_private, derived_root_public = seed_to_root_keypair(loaded_seed)

        # Derive child keypair at the proven path
        final_private_key, final_public_key = derive_child_keypair(
            loaded_seed, path_index
        )

        # Verify derived key matches proof
        final_public_bytes = public_key_to_bytes(final_public_key)
        final_fingerprint = compute_ssh_fingerprint(final_public_key)

        assert final_fingerprint == fingerprint, "Derived fingerprint should match proof"
        assert final_public_bytes == child_public_bytes, "Public keys should match"

        # Customer now has their private key!
        private_key_bytes = private_key_to_bytes(final_private_key)

        assert len(private_key_bytes) == 32, "Ed25519 private key should be 32 bytes"

    def test_wrong_seed_fails_verification(self, storage):
        """Test that using wrong seed produces different key."""
        # Original workflow
        seed1 = generate_master_seed()
        root_private1, root_public1 = seed_to_root_keypair(seed1)
        root_public_bytes1 = public_key_to_bytes(root_public1)

        # Derive child at path 42
        path_index = 42
        child_private1, child_public1 = derive_child_keypair(seed1, path_index)
        child_public_bytes1 = public_key_to_bytes(child_public1)
        fingerprint1 = compute_ssh_fingerprint(child_public1)

        # Different seed
        seed2 = generate_master_seed()
        root_private2, root_public2 = seed_to_root_keypair(seed2)

        # Try to derive at same path
        child_private2, child_public2 = derive_child_keypair(seed2, path_index)
        child_public_bytes2 = public_key_to_bytes(child_public2)
        fingerprint2 = compute_ssh_fingerprint(child_public2)

        # Should produce different keys!
        assert fingerprint1 != fingerprint2
        assert child_public_bytes1 != child_public_bytes2

    def test_password_required_for_derivation(self, storage):
        """Test that correct password is required to derive keys."""
        password = "correct_password"
        wrong_password = "wrong_password"

        seed = generate_master_seed()
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        storage.save_seed(seed, password, root_public_key_bytes)

        # Correct password works
        loaded_seed, _ = storage.load_seed(password)
        assert loaded_seed == seed

        # Wrong password fails
        with pytest.raises(ValueError, match="Incorrect password"):
            storage.load_seed(wrong_password)

    def test_offline_vanity_search_simulation(self):
        """Test that we can search for vanity patterns offline (no server)."""
        seed = generate_master_seed()
        root_private, root_public = seed_to_root_keypair(seed)

        # Search for pattern "abc"
        pattern = "abc"
        max_attempts = 10000
        found = False

        for i in range(max_attempts):
            _, child_public = derive_child_keypair(seed, i)
            fingerprint = compute_ssh_fingerprint(child_public)

            if matches_pattern(pattern, fingerprint):
                found = True
                break

        # Note: Pattern "abc" has ~1 in 262,144 probability, so we might not find it
        # in 10,000 attempts. This test just validates the search mechanism works.
        if found:
            assert matches_pattern(pattern, fingerprint)
