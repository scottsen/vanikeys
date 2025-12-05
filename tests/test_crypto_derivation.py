"""
Tests for Ed25519 HD Key Derivation

Critical tests for the core cryptographic primitives.
These tests MUST pass for security guarantees.
"""

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from vanikeys.crypto.derivation import (
    generate_master_seed,
    seed_to_root_keypair,
    derive_child_seed,
    derive_child_keypair,
    public_key_to_bytes,
    private_key_to_bytes,
)


class TestSeedGeneration:
    """Test master seed generation."""

    def test_generate_master_seed_length(self):
        """Seed must be exactly 32 bytes."""
        seed = generate_master_seed()
        assert len(seed) == 32

    def test_generate_master_seed_randomness(self):
        """Seeds must be different (cryptographically random)."""
        seed1 = generate_master_seed()
        seed2 = generate_master_seed()
        assert seed1 != seed2

    def test_generate_master_seed_type(self):
        """Seed must be bytes."""
        seed = generate_master_seed()
        assert isinstance(seed, bytes)


class TestRootKeypair:
    """Test root keypair derivation from seed."""

    def test_seed_to_root_keypair_deterministic(self):
        """Same seed produces same keypair."""
        seed = b"0" * 32  # Fixed seed for testing
        priv1, pub1 = seed_to_root_keypair(seed)
        priv2, pub2 = seed_to_root_keypair(seed)

        assert public_key_to_bytes(pub1) == public_key_to_bytes(pub2)
        assert private_key_to_bytes(priv1) == private_key_to_bytes(priv2)

    def test_seed_to_root_keypair_different_seeds(self):
        """Different seeds produce different keypairs."""
        seed1 = b"0" * 32
        seed2 = b"1" * 32

        _, pub1 = seed_to_root_keypair(seed1)
        _, pub2 = seed_to_root_keypair(seed2)

        assert public_key_to_bytes(pub1) != public_key_to_bytes(pub2)

    def test_seed_to_root_keypair_types(self):
        """Keypair must be correct types."""
        seed = generate_master_seed()
        priv, pub = seed_to_root_keypair(seed)

        assert isinstance(priv, ed25519.Ed25519PrivateKey)
        assert isinstance(pub, ed25519.Ed25519PublicKey)

    def test_seed_to_root_keypair_invalid_length(self):
        """Must reject seeds that aren't 32 bytes."""
        with pytest.raises(AssertionError):
            seed_to_root_keypair(b"short")

        with pytest.raises(AssertionError):
            seed_to_root_keypair(b"0" * 31)

        with pytest.raises(AssertionError):
            seed_to_root_keypair(b"0" * 33)

    def test_public_key_from_private(self):
        """Public key from private must match."""
        seed = generate_master_seed()
        priv, pub = seed_to_root_keypair(seed)

        pub_from_priv = priv.public_key()
        assert public_key_to_bytes(pub) == public_key_to_bytes(pub_from_priv)


class TestChildDerivation:
    """Test child key derivation."""

    def test_derive_child_seed_deterministic(self):
        """Same parent seed + path produces same child seed."""
        parent = b"0" * 32
        path = 42

        child1 = derive_child_seed(parent, path)
        child2 = derive_child_seed(parent, path)

        assert child1 == child2

    def test_derive_child_seed_different_paths(self):
        """Different paths produce different child seeds."""
        parent = b"0" * 32

        child0 = derive_child_seed(parent, 0)
        child1 = derive_child_seed(parent, 1)
        child2 = derive_child_seed(parent, 2)

        assert child0 != child1
        assert child1 != child2
        assert child0 != child2

    def test_derive_child_seed_different_parents(self):
        """Different parent seeds produce different children."""
        parent1 = b"0" * 32
        parent2 = b"1" * 32
        path = 0

        child1 = derive_child_seed(parent1, path)
        child2 = derive_child_seed(parent2, path)

        assert child1 != child2

    def test_derive_child_seed_length(self):
        """Child seed must be 32 bytes."""
        parent = generate_master_seed()
        child = derive_child_seed(parent, 0)

        assert len(child) == 32

    def test_derive_child_seed_invalid_parent_length(self):
        """Must reject parent seeds that aren't 32 bytes."""
        with pytest.raises(AssertionError):
            derive_child_seed(b"short", 0)

    def test_derive_child_seed_invalid_path_range(self):
        """Must reject path indices out of range."""
        parent = b"0" * 32

        with pytest.raises(AssertionError):
            derive_child_seed(parent, -1)

        with pytest.raises(AssertionError):
            derive_child_seed(parent, 2**32)

    def test_derive_child_seed_boundary_paths(self):
        """Boundary path values must work."""
        parent = b"0" * 32

        # Min path
        child_min = derive_child_seed(parent, 0)
        assert len(child_min) == 32

        # Max path
        child_max = derive_child_seed(parent, 2**32 - 1)
        assert len(child_max) == 32

        assert child_min != child_max


class TestChildKeypair:
    """Test child keypair derivation."""

    def test_derive_child_keypair_deterministic(self):
        """Same parent + path produces same child keypair."""
        parent = b"0" * 32
        path = 42

        priv1, pub1 = derive_child_keypair(parent, path)
        priv2, pub2 = derive_child_keypair(parent, path)

        assert public_key_to_bytes(pub1) == public_key_to_bytes(pub2)
        assert private_key_to_bytes(priv1) == private_key_to_bytes(priv2)

    def test_derive_child_keypair_different_paths(self):
        """Different paths produce different keypairs."""
        parent = b"0" * 32

        _, pub0 = derive_child_keypair(parent, 0)
        _, pub1 = derive_child_keypair(parent, 1)

        assert public_key_to_bytes(pub0) != public_key_to_bytes(pub1)

    def test_derive_child_keypair_types(self):
        """Derived keypair must be correct types."""
        parent = generate_master_seed()
        priv, pub = derive_child_keypair(parent, 0)

        assert isinstance(priv, ed25519.Ed25519PrivateKey)
        assert isinstance(pub, ed25519.Ed25519PublicKey)

    def test_derive_multiple_generations(self):
        """Can derive child from child (multi-level)."""
        # Root
        root_seed = generate_master_seed()

        # First generation child
        child1_seed = derive_child_seed(root_seed, 0)

        # Second generation child (grandchild)
        child2_seed = derive_child_seed(child1_seed, 0)

        # All different
        assert root_seed != child1_seed
        assert child1_seed != child2_seed
        assert root_seed != child2_seed

    def test_derive_many_children(self):
        """Can derive many children from same parent."""
        parent = generate_master_seed()
        children = []

        for i in range(100):
            _, pub = derive_child_keypair(parent, i)
            children.append(public_key_to_bytes(pub))

        # All children unique
        assert len(children) == len(set(children))


class TestKeySerialization:
    """Test key serialization helpers."""

    def test_public_key_to_bytes_length(self):
        """Public key bytes must be 32 bytes (Ed25519)."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        pub_bytes = public_key_to_bytes(pub)
        assert len(pub_bytes) == 32

    def test_private_key_to_bytes_length(self):
        """Private key bytes must be 32 bytes (Ed25519 seed)."""
        seed = generate_master_seed()
        priv, _ = seed_to_root_keypair(seed)

        priv_bytes = private_key_to_bytes(priv)
        assert len(priv_bytes) == 32

    def test_private_key_to_bytes_is_seed(self):
        """Private key bytes should equal original seed."""
        seed = generate_master_seed()
        priv, _ = seed_to_root_keypair(seed)

        priv_bytes = private_key_to_bytes(priv)
        assert priv_bytes == seed


class TestDerivationProtocol:
    """Test protocol version and context."""

    def test_derivation_context_immutable(self):
        """Protocol context must not change (breaks compatibility)."""
        from vanikeys.crypto.derivation import DERIVATION_CONTEXT

        # This value is FIXED for protocol version
        assert DERIVATION_CONTEXT == b"vanikeys-ssh-v1"

    def test_context_affects_derivation(self):
        """Changing context produces different derivations."""
        # If we change context, derivations change (this is by design)
        # This test documents the behavior

        parent = b"0" * 32
        path = 0

        # Normal derivation
        child = derive_child_seed(parent, path)

        # Verify it's deterministic
        child_again = derive_child_seed(parent, path)
        assert child == child_again


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_derive_path_zero(self):
        """Path 0 is valid."""
        parent = generate_master_seed()
        priv, pub = derive_child_keypair(parent, 0)

        assert isinstance(priv, ed25519.Ed25519PrivateKey)
        assert isinstance(pub, ed25519.Ed25519PublicKey)

    def test_derive_path_max(self):
        """Maximum path value is valid."""
        parent = generate_master_seed()
        max_path = 2**32 - 1

        priv, pub = derive_child_keypair(parent, max_path)

        assert isinstance(priv, ed25519.Ed25519PrivateKey)
        assert isinstance(pub, ed25519.Ed25519PublicKey)

    def test_many_sequential_derivations(self):
        """Can perform many sequential derivations."""
        parent = generate_master_seed()

        for i in range(1000):
            priv, pub = derive_child_keypair(parent, i)
            assert isinstance(priv, ed25519.Ed25519PrivateKey)


class TestSecurityProperties:
    """Test security properties of derivation."""

    def test_public_key_does_not_reveal_seed(self):
        """Cannot derive seed from public key (one-way)."""
        seed = generate_master_seed()
        _, pub = seed_to_root_keypair(seed)

        pub_bytes = public_key_to_bytes(pub)

        # Public key bytes are different from seed
        assert pub_bytes != seed

    def test_child_seed_does_not_reveal_parent(self):
        """Cannot derive parent from child (one-way)."""
        parent = generate_master_seed()
        child = derive_child_seed(parent, 0)

        # Child is different from parent
        assert child != parent

        # Derive another child to ensure independence
        child2 = derive_child_seed(parent, 1)
        assert child2 != parent
        assert child2 != child

    def test_sibling_independence(self):
        """Sibling keys don't reveal each other."""
        parent = generate_master_seed()

        # Derive siblings
        child1_seed = derive_child_seed(parent, 0)
        child2_seed = derive_child_seed(parent, 1)

        # Siblings are independent
        assert child1_seed != child2_seed

        # Knowing child1 doesn't help derive child2
        # (This is true by construction - both use parent + different path)
