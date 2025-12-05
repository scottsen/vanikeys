"""
VaniKeys Cryptography Module

Zero-knowledge vanity key generation using Hierarchical Deterministic (HD)
key derivation.

This module implements the core cryptographic primitives for the VaniKeys protocol:
- Ed25519 HD key derivation
- SSH fingerprint computation
- Pattern matching
- Cryptographic proof generation and verification

See docs/ZERO_KNOWLEDGE_PROTOCOL.md for protocol specification.
"""

from .derivation import (
    generate_master_seed,
    seed_to_root_keypair,
    derive_child_seed,
    derive_child_keypair,
    public_key_to_bytes,
    private_key_to_bytes,
)

from .fingerprint import (
    ssh_public_key_to_bytes,
    ssh_public_key_to_authorized_keys_format,
    compute_ssh_fingerprint,
    compute_ssh_fingerprint_md5,
    extract_fingerprint_searchable,
)

from .matching import (
    create_pattern_matcher,
    estimate_pattern_difficulty,
)

from .proofs import (
    generate_derivation_proof,
    verify_derivation_proof,
)

__all__ = [
    # Derivation
    "generate_master_seed",
    "seed_to_root_keypair",
    "derive_child_seed",
    "derive_child_keypair",
    "public_key_to_bytes",
    "private_key_to_bytes",
    # Fingerprint
    "ssh_public_key_to_bytes",
    "ssh_public_key_to_authorized_keys_format",
    "compute_ssh_fingerprint",
    "compute_ssh_fingerprint_md5",
    "extract_fingerprint_searchable",
    # Matching
    "create_pattern_matcher",
    "estimate_pattern_difficulty",
    # Proofs
    "generate_derivation_proof",
    "verify_derivation_proof",
]
