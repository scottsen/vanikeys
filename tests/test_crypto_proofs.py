"""
Tests for Cryptographic Proofs

Critical tests for proof generation and verification.
"""

import pytest
from vanikeys.crypto.derivation import (
    generate_master_seed,
    seed_to_root_keypair,
    derive_child_keypair,
    public_key_to_bytes,
)
from vanikeys.crypto.fingerprint import compute_ssh_fingerprint
from vanikeys.crypto.proofs import (
    generate_derivation_proof,
    verify_derivation_proof,
    generate_order_proof,
    verify_order_proof,
)


class TestDerivationProof:
    """Test derivation proof generation and verification."""

    def test_generate_derivation_proof_structure(self):
        """Proof has required fields."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)

        proof = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub
        )

        assert "path_index" in proof
        assert "root_public_key" in proof
        assert "child_public_key" in proof
        assert "derivation_hash" in proof
        assert proof["path_index"] == 42

    def test_verify_derivation_proof_valid(self):
        """Valid proof verifies successfully."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)

        proof = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub
        )

        assert verify_derivation_proof(proof, seed)

    def test_verify_derivation_proof_wrong_path(self):
        """Tampered path fails verification."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)

        proof = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub
        )

        # Tamper with path
        proof["path_index"] = 999

        assert not verify_derivation_proof(proof, seed)

    def test_verify_derivation_proof_wrong_seed(self):
        """Wrong seed fails verification."""
        seed1 = generate_master_seed()
        seed2 = generate_master_seed()

        _, root_pub = seed_to_root_keypair(seed1)
        _, child_pub = derive_child_keypair(seed1, 42)

        proof = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub
        )

        # Verify with wrong seed
        assert not verify_derivation_proof(proof, seed2)


class TestOrderProof:
    """Test complete order proof."""

    def test_generate_order_proof_structure(self):
        """Order proof has required fields."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)
        fp = compute_ssh_fingerprint(child_pub)

        proof = generate_order_proof(
            public_key_to_bytes(root_pub), 42, child_pub, "test", fp
        )

        assert "derivation" in proof
        assert "pattern_match" in proof
        assert "version" in proof

    def test_verify_order_proof_valid(self):
        """Valid order proof verifies."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)
        fp = compute_ssh_fingerprint(child_pub)

        # Use pattern we know exists (single char)
        pattern = fp[7:8]  # Extract one char from fingerprint

        proof = generate_order_proof(
            public_key_to_bytes(root_pub), 42, child_pub, pattern, fp
        )

        result = verify_order_proof(proof, seed, pattern)

        assert result["valid"]
        assert result["derivation_valid"]
        assert result["fingerprint_valid"]
        assert result["pattern_valid"]

    def test_verify_order_proof_pattern_mismatch(self):
        """Wrong pattern fails verification."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)
        fp = compute_ssh_fingerprint(child_pub)

        proof = generate_order_proof(
            public_key_to_bytes(root_pub), 42, child_pub, "test", fp
        )

        # Verify with different pattern
        result = verify_order_proof(proof, seed, "different")

        assert not result["valid"]
        assert not result["pattern_valid"]


class TestProofSecurity:
    """Test security properties of proofs."""

    def test_proof_deterministic(self):
        """Same inputs produce same proof."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)
        _, child_pub = derive_child_keypair(seed, 42)

        proof1 = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub
        )
        proof2 = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub
        )

        assert proof1 == proof2

    def test_cannot_forge_proof(self):
        """Cannot create valid proof without correct data."""
        seed = generate_master_seed()
        _, root_pub = seed_to_root_keypair(seed)

        # Create proof for path 42 but verify with different path's key
        _, child_pub_42 = derive_child_keypair(seed, 42)
        _, child_pub_99 = derive_child_keypair(seed, 99)

        proof = generate_derivation_proof(
            public_key_to_bytes(root_pub), 42, child_pub_99  # Wrong key!
        )

        # Verification should fail
        assert not verify_derivation_proof(proof, seed)
