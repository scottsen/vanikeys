"""
Hierarchical Deterministic (HD) Key Derivation

Implements Ed25519 seed-based key derivation for the VaniKeys zero-knowledge protocol.

This module allows deriving child keys from a master seed deterministically:
- Client generates master seed (kept secret)
- Server searches derivation paths (using public keys only)
- Client derives final key from seed + path found by server

Protocol version: vanikeys-ssh-v1
Based on: BIP32 concepts adapted for Ed25519

See: docs/HD_DERIVATION_IMPLEMENTATION.md for implementation details
"""

import secrets
import hashlib
import struct
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)

# Protocol version identifier (prevents cross-protocol attacks)
DERIVATION_CONTEXT = b"vanikeys-ssh-v1"


def generate_master_seed() -> bytes:
    """
    Generate cryptographically secure 32-byte master seed.

    This seed is the root secret for all derived keys. It must be:
    - Generated with cryptographically secure randomness
    - Stored encrypted (never plaintext)
    - Never transmitted to VaniKeys servers
    - Backed up securely

    Returns:
        32-byte random seed

    Example:
        >>> seed = generate_master_seed()
        >>> len(seed)
        32
    """
    return secrets.token_bytes(32)


def seed_to_root_keypair(
    seed: bytes,
) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """
    Convert 32-byte seed to root Ed25519 key pair.

    Args:
        seed: 32-byte cryptographically secure seed

    Returns:
        Tuple of (private_key, public_key)

    Raises:
        AssertionError: If seed is not exactly 32 bytes

    Example:
        >>> seed = generate_master_seed()
        >>> private_key, public_key = seed_to_root_keypair(seed)
        >>> isinstance(private_key, ed25519.Ed25519PrivateKey)
        True
    """
    assert len(seed) == 32, "Seed must be exactly 32 bytes"

    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    public_key = private_key.public_key()

    return private_key, public_key


def derive_child_seed(parent_seed: bytes, path_index: int) -> bytes:
    """
    Derive child seed from parent seed + path index.

    Uses SHA-512 HMAC-like derivation (similar to BIP32) to produce
    deterministic child seeds. The derivation is one-way: knowing the
    child seed does not reveal the parent seed.

    Derivation formula:
        child_seed = SHA512(parent_seed || context || path_index)[:32]

    Args:
        parent_seed: 32-byte parent seed (or root seed)
        path_index: Integer path index (0 to 2^32-1)

    Returns:
        32-byte child seed

    Raises:
        AssertionError: If parent_seed is not 32 bytes or path_index out of range

    Example:
        >>> seed = generate_master_seed()
        >>> child1 = derive_child_seed(seed, 0)
        >>> child2 = derive_child_seed(seed, 1)
        >>> child1 != child2
        True
        >>> len(child1)
        32
    """
    assert len(parent_seed) == 32, "Parent seed must be 32 bytes"
    assert 0 <= path_index < 2**32, "Path index must be in range [0, 2^32)"

    # Encode path index as 4-byte big-endian
    index_bytes = struct.pack(">I", path_index)

    # Hash: parent_seed || context || index
    h = hashlib.sha512()
    h.update(parent_seed)
    h.update(DERIVATION_CONTEXT)
    h.update(index_bytes)
    digest = h.digest()

    # Take first 32 bytes as child seed
    child_seed = digest[:32]

    return child_seed


def derive_child_keypair(
    parent_seed: bytes, path_index: int
) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """
    Derive child key pair from parent seed + path index.

    This is the core function used by both client and server:
    - Client: Uses with master seed to derive final keys
    - Server: Cannot use (doesn't have seed), but protocol is same

    Args:
        parent_seed: 32-byte parent seed
        path_index: Integer path index

    Returns:
        Tuple of (child_private_key, child_public_key)

    Example:
        >>> seed = generate_master_seed()
        >>> priv, pub = derive_child_keypair(seed, 42)
        >>> isinstance(priv, ed25519.Ed25519PrivateKey)
        True
        >>> priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw) == \\
        ...     pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
        True
    """
    child_seed = derive_child_seed(parent_seed, path_index)
    return seed_to_root_keypair(child_seed)


def public_key_to_bytes(public_key: ed25519.Ed25519PublicKey) -> bytes:
    """
    Convert Ed25519 public key to raw 32-byte representation.

    This format is used for:
    - Sending root public key to VaniKeys server
    - Storing public keys
    - Proof generation

    Args:
        public_key: Ed25519 public key

    Returns:
        32-byte raw public key

    Example:
        >>> seed = generate_master_seed()
        >>> _, pub = seed_to_root_keypair(seed)
        >>> pub_bytes = public_key_to_bytes(pub)
        >>> len(pub_bytes)
        32
    """
    return public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)


def private_key_to_bytes(private_key: ed25519.Ed25519PrivateKey) -> bytes:
    """
    Convert Ed25519 private key to raw 32-byte seed representation.

    WARNING: This exposes the private key! Only use for:
    - Secure storage (encrypted)
    - Key export (user's machine only)
    - Never transmit over network!

    Args:
        private_key: Ed25519 private key

    Returns:
        32-byte raw private key seed

    Example:
        >>> seed = generate_master_seed()
        >>> priv, _ = seed_to_root_keypair(seed)
        >>> priv_bytes = private_key_to_bytes(priv)
        >>> len(priv_bytes)
        32
        >>> priv_bytes == seed
        True
    """
    return private_key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )


# Server-side function (for testing - server never has seed in production)
def search_vanity_path_simple(
    root_seed: bytes,
    pattern: str,
    max_attempts: int = 1_000_000,
    case_sensitive: bool = False,
) -> dict | None:
    """
    Simple single-threaded vanity path search.

    NOTE: This is for testing/demonstration. Production should use:
    - GPU-accelerated search
    - Distributed workers
    - Progress tracking

    Args:
        root_seed: 32-byte master seed (CLIENT-SIDE ONLY in production!)
        pattern: Pattern to search for in fingerprint
        max_attempts: Maximum paths to try
        case_sensitive: Case-sensitive matching

    Returns:
        Dict with path_index, public_key, fingerprint if found, else None

    Example:
        >>> seed = generate_master_seed()
        >>> result = search_vanity_path_simple(seed, "a", max_attempts=10000)
        >>> if result:
        ...     print(f"Found at path {result['path_index']}")
        ...     print(f"Fingerprint: {result['fingerprint']}")
    """
    from .fingerprint import compute_ssh_fingerprint
    from .matching import create_pattern_matcher

    matcher = create_pattern_matcher(pattern, case_sensitive)

    for path_index in range(max_attempts):
        _, child_public = derive_child_keypair(root_seed, path_index)
        fingerprint = compute_ssh_fingerprint(child_public)

        if matcher(fingerprint):
            return {
                "path_index": path_index,
                "public_key": child_public,
                "fingerprint": fingerprint,
                "attempts": path_index + 1,
            }

    return None
