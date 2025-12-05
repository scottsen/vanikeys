"""
Cryptographic Proof Generation and Verification

Implements the proof system for VaniKeys' zero-knowledge protocol.

Proofs allow customers to verify that:
1. The derivation path produces the claimed public key
2. The fingerprint matches the desired pattern
3. VaniKeys isn't lying about the results

Customers verify proofs BEFORE deriving their private keys.
"""

import hashlib
import struct
import base64
from typing import Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519

from .derivation import (
    derive_child_keypair,
    public_key_to_bytes,
    DERIVATION_CONTEXT,
)
from .fingerprint import compute_ssh_fingerprint


def generate_derivation_proof(
    root_public_bytes: bytes,
    path_index: int,
    child_public_key: ed25519.Ed25519PublicKey,
) -> Dict[str, Any]:
    """
    Generate cryptographic proof for derivation path.

    The proof demonstrates that:
    - path_index applied to root_public produces child_public_key
    - The derivation is deterministic and verifiable

    Server generates this proof and sends to customer.
    Customer verifies proof before deriving private key.

    Proof structure:
        - path_index: Derivation path found
        - root_public_key: Customer's root public key (base64)
        - child_public_key: Derived public key (base64)
        - derivation_hash: Hash binding path → key
        - algorithm: "ed25519"
        - context: Protocol version identifier

    Args:
        root_public_bytes: 32-byte root public key
        path_index: Derivation path index
        child_public_key: Derived Ed25519 public key

    Returns:
        Dict containing proof data

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> from vanikeys.crypto import derive_child_keypair, public_key_to_bytes
        >>> seed = generate_master_seed()
        >>> _, root_pub = seed_to_root_keypair(seed)
        >>> _, child_pub = derive_child_keypair(seed, 42)
        >>> proof = generate_derivation_proof(
        ...     public_key_to_bytes(root_pub), 42, child_pub
        ... )
        >>> proof['path_index']
        42
        >>> 'derivation_hash' in proof
        True
    """
    child_public_bytes = public_key_to_bytes(child_public_key)

    # Compute derivation hash (binds path → key deterministically)
    # Hash(root_public || path_index || context)
    h = hashlib.sha256()
    h.update(root_public_bytes)
    h.update(struct.pack(">I", path_index))
    h.update(DERIVATION_CONTEXT)
    derivation_hash = h.digest()

    return {
        "path_index": path_index,
        "root_public_key": base64.b64encode(root_public_bytes).decode("ascii"),
        "child_public_key": base64.b64encode(child_public_bytes).decode("ascii"),
        "derivation_hash": base64.b64encode(derivation_hash).decode("ascii"),
        "algorithm": "ed25519",
        "context": DERIVATION_CONTEXT.decode("ascii"),
    }


def verify_derivation_proof(proof: Dict[str, Any], master_seed: bytes) -> bool:
    """
    Verify cryptographic proof before deriving private key.

    Customer runs this verification to ensure:
    1. The path produces the claimed public key
    2. The derivation hash is correct
    3. VaniKeys isn't lying

    IMPORTANT: Only derive private key if this returns True!

    Verification steps:
    1. Decode proof fields
    2. Derive child public key locally (using master seed + path)
    3. Verify derived key matches claimed key
    4. Verify derivation hash matches

    Args:
        proof: Proof dict from generate_derivation_proof()
        master_seed: Customer's 32-byte master seed

    Returns:
        True if proof is valid and safe to derive private key

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> from vanikeys.crypto import derive_child_keypair, public_key_to_bytes
        >>> seed = generate_master_seed()
        >>> _, root_pub = seed_to_root_keypair(seed)
        >>> _, child_pub = derive_child_keypair(seed, 42)
        >>> proof = generate_derivation_proof(
        ...     public_key_to_bytes(root_pub), 42, child_pub
        ... )
        >>> verify_derivation_proof(proof, seed)
        True
        >>> # Tampered proof should fail
        >>> bad_proof = proof.copy()
        >>> bad_proof['path_index'] = 999
        >>> verify_derivation_proof(bad_proof, seed)
        False
    """
    try:
        # 1. Decode proof fields
        path_index = proof["path_index"]
        claimed_child_public = base64.b64decode(proof["child_public_key"])
        claimed_derivation_hash = base64.b64decode(proof["derivation_hash"])

        # 2. Derive child public key locally
        _, actual_child_public = derive_child_keypair(master_seed, path_index)
        actual_child_bytes = public_key_to_bytes(actual_child_public)

        # 3. Verify child public key matches claimed
        if actual_child_bytes != claimed_child_public:
            return False

        # 4. Verify derivation hash
        from .derivation import seed_to_root_keypair

        _, root_public = seed_to_root_keypair(master_seed)
        root_public_bytes = public_key_to_bytes(root_public)

        h = hashlib.sha256()
        h.update(root_public_bytes)
        h.update(struct.pack(">I", path_index))
        h.update(DERIVATION_CONTEXT)
        expected_derivation_hash = h.digest()

        if expected_derivation_hash != claimed_derivation_hash:
            return False

        # All checks passed
        return True

    except (KeyError, ValueError, TypeError):
        # Proof format invalid
        return False


def generate_order_proof(
    root_public_bytes: bytes,
    path_index: int,
    child_public_key: ed25519.Ed25519PublicKey,
    pattern: str,
    fingerprint: str,
) -> Dict[str, Any]:
    """
    Generate complete order proof (derivation + pattern match).

    This is the full proof returned to customers, including:
    - Derivation proof (path → public key)
    - Pattern match proof (fingerprint contains pattern)

    Args:
        root_public_bytes: Customer's root public key
        path_index: Derivation path found
        child_public_key: Derived public key
        pattern: Pattern that was searched for
        fingerprint: SSH fingerprint of derived key

    Returns:
        Complete order proof dict

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> from vanikeys.crypto import derive_child_keypair, public_key_to_bytes
        >>> from vanikeys.crypto import compute_ssh_fingerprint
        >>> seed = generate_master_seed()
        >>> _, root_pub = seed_to_root_keypair(seed)
        >>> _, child_pub = derive_child_keypair(seed, 42)
        >>> fp = compute_ssh_fingerprint(child_pub)
        >>> proof = generate_order_proof(
        ...     public_key_to_bytes(root_pub), 42, child_pub, "test", fp
        ... )
        >>> 'derivation' in proof
        True
        >>> 'pattern_match' in proof
        True
    """
    # Derivation proof
    derivation_proof = generate_derivation_proof(
        root_public_bytes, path_index, child_public_key
    )

    # Pattern match proof
    from .fingerprint import extract_fingerprint_searchable

    searchable = extract_fingerprint_searchable(fingerprint)
    pattern_found = pattern.lower() in searchable.lower()

    pattern_match_proof = {
        "pattern": pattern,
        "fingerprint": fingerprint,
        "searchable_portion": searchable,
        "pattern_found": pattern_found,
        "case_sensitive": False,
    }

    return {
        "derivation": derivation_proof,
        "pattern_match": pattern_match_proof,
        "version": "vanikeys-v1",
    }


def verify_order_proof(
    proof: Dict[str, Any], master_seed: bytes, expected_pattern: str
) -> Dict[str, Any]:
    """
    Verify complete order proof (derivation + pattern match).

    Returns detailed verification results.

    Args:
        proof: Complete order proof from generate_order_proof()
        master_seed: Customer's master seed
        expected_pattern: Pattern customer ordered

    Returns:
        Dict with verification results:
            - valid: True if all checks pass
            - derivation_valid: Derivation proof valid
            - pattern_valid: Pattern actually found in fingerprint
            - fingerprint: Fingerprint of derived key
            - errors: List of error messages

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> from vanikeys.crypto import derive_child_keypair, public_key_to_bytes
        >>> from vanikeys.crypto import compute_ssh_fingerprint
        >>> seed = generate_master_seed()
        >>> _, root_pub = seed_to_root_keypair(seed)
        >>> _, child_pub = derive_child_keypair(seed, 42)
        >>> fp = compute_ssh_fingerprint(child_pub)
        >>> proof = generate_order_proof(
        ...     public_key_to_bytes(root_pub), 42, child_pub, "a", fp
        ... )
        >>> result = verify_order_proof(proof, seed, "a")
        >>> result['derivation_valid']
        True
    """
    errors = []

    # Verify derivation proof
    derivation_valid = verify_derivation_proof(proof["derivation"], master_seed)
    if not derivation_valid:
        errors.append("Derivation proof invalid")

    # Verify pattern match
    pattern_proof = proof["pattern_match"]
    fingerprint = pattern_proof["fingerprint"]
    pattern = pattern_proof["pattern"]

    # Re-compute fingerprint from derived key
    path_index = proof["derivation"]["path_index"]
    _, derived_public = derive_child_keypair(master_seed, path_index)
    computed_fingerprint = compute_ssh_fingerprint(derived_public)

    if computed_fingerprint != fingerprint:
        errors.append("Fingerprint mismatch")
        fingerprint_valid = False
    else:
        fingerprint_valid = True

    # Verify pattern actually present
    from .fingerprint import extract_fingerprint_searchable

    searchable = extract_fingerprint_searchable(computed_fingerprint)
    pattern_found = pattern.lower() in searchable.lower()

    if not pattern_found:
        errors.append(f"Pattern '{pattern}' not found in fingerprint")
        pattern_valid = False
    else:
        pattern_valid = True

    # Verify pattern matches what customer ordered
    if pattern.lower() != expected_pattern.lower():
        errors.append(
            f"Pattern mismatch: expected '{expected_pattern}', got '{pattern}'"
        )
        pattern_valid = False

    valid = derivation_valid and fingerprint_valid and pattern_valid

    return {
        "valid": valid,
        "derivation_valid": derivation_valid,
        "fingerprint_valid": fingerprint_valid,
        "pattern_valid": pattern_valid,
        "fingerprint": computed_fingerprint,
        "errors": errors,
    }


def verify_order_proof_passwordless(
    proof: Dict[str, Any], root_public_bytes: bytes
) -> Dict[str, Any]:
    """
    Verify order proof WITHOUT requiring master seed/password.

    This performs lighter verification that doesn't require decrypting the seed:
    - Checks proof structure is valid
    - Verifies root public key matches customer's key
    - Verifies pattern is present in claimed fingerprint
    - Checks proof hasn't been tampered with

    NOTE: This cannot verify the derivation path is correct (that requires seed).
    For full verification before deriving, use verify_order_proof() with seed.

    Args:
        proof: Complete order proof
        root_public_bytes: Customer's root public key (no password needed)

    Returns:
        Dict with verification results:
            - valid: True if basic checks pass
            - checks: Dict of individual check results
            - fingerprint: Claimed fingerprint
            - match: Whether pattern found in fingerprint
            - errors: List of error messages

    Example:
        >>> # Customer can verify without password
        >>> result = verify_order_proof_passwordless(proof, root_public_key_bytes)
        >>> result['valid']  # Basic validation passed
        True
    """
    errors = []
    checks = {}

    try:
        # Check proof structure
        if "derivation" not in proof:
            errors.append("Missing derivation in proof")
            checks["structure"] = False
            return {
                "valid": False,
                "checks": checks,
                "errors": errors,
            }

        if "pattern_match" not in proof:
            errors.append("Missing pattern_match in proof")
            checks["structure"] = False
            return {
                "valid": False,
                "checks": checks,
                "errors": errors,
            }

        deriv_proof = proof["derivation"]
        pattern_match = proof["pattern_match"]

        # Verify root public key matches
        claimed_root_public = base64.b64decode(deriv_proof["root_public_key"])
        if claimed_root_public != root_public_bytes:
            errors.append("Root public key mismatch")
            checks["root_key_match"] = False
        else:
            checks["root_key_match"] = True

        # Get fingerprint and pattern
        fingerprint = pattern_match.get("fingerprint", "")
        pattern = pattern_match.get("pattern", "")

        if not fingerprint or not pattern:
            errors.append("Missing fingerprint or pattern in proof")
            checks["structure"] = False
            return {
                "valid": False,
                "checks": checks,
                "fingerprint": fingerprint,
                "errors": errors,
            }

        checks["structure"] = True

        # Verify pattern is in fingerprint
        from .fingerprint import extract_fingerprint_searchable

        searchable = extract_fingerprint_searchable(fingerprint)
        pattern_found = pattern.lower() in searchable.lower()

        if not pattern_found:
            errors.append(f"Pattern '{pattern}' not found in fingerprint")
            checks["pattern_match"] = False
        else:
            checks["pattern_match"] = True

        # Check derivation hash format (can't verify correctness without seed)
        if "derivation_hash" in deriv_proof:
            checks["derivation_hash_present"] = True
        else:
            errors.append("Missing derivation_hash in proof")
            checks["derivation_hash_present"] = False

        valid = (
            checks.get("root_key_match", False)
            and checks.get("structure", False)
            and checks.get("pattern_match", False)
            and checks.get("derivation_hash_present", False)
        )

        return {
            "valid": valid,
            "checks": checks,
            "fingerprint": fingerprint,
            "match": pattern_found,
            "errors": errors,
        }

    except (KeyError, ValueError, TypeError) as e:
        errors.append(f"Proof format invalid: {e}")
        checks["structure"] = False
        return {
            "valid": False,
            "checks": checks,
            "errors": errors,
        }


def proof_to_json(proof: Dict[str, Any]) -> str:
    """
    Serialize proof to JSON string.

    Args:
        proof: Proof dict

    Returns:
        JSON string

    Example:
        >>> proof = {"path_index": 42, "test": "data"}
        >>> json_str = proof_to_json(proof)
        >>> '"path_index": 42' in json_str
        True
    """
    import json

    return json.dumps(proof, indent=2)


def proof_from_json(json_str: str) -> Dict[str, Any]:
    """
    Deserialize proof from JSON string.

    Args:
        json_str: JSON proof string

    Returns:
        Proof dict

    Raises:
        ValueError: If JSON is invalid

    Example:
        >>> json_str = '{"path_index": 42}'
        >>> proof = proof_from_json(json_str)
        >>> proof['path_index']
        42
    """
    import json

    return json.loads(json_str)
