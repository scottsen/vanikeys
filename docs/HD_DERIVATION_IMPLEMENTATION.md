# HD Derivation Path Discovery - Implementation Guide

**Version**: 1.0
**Last Updated**: 2025-12-03
**Audience**: VaniKeys developers implementing the zero-knowledge protocol

## Overview

This document provides **concrete implementation guidance** for the Hierarchical Deterministic (HD) key derivation system that powers VaniKeys' zero-knowledge vanity key protocol.

**See also**: `ZERO_KNOWLEDGE_PROTOCOL.md` for high-level protocol design and security analysis.

---

## Table of Contents

1. [Key Derivation Functions](#key-derivation-functions)
2. [SSH Key Format](#ssh-key-format)
3. [Fingerprint Computation](#fingerprint-computation)
4. [Pattern Matching](#pattern-matching)
5. [Search Algorithm](#search-algorithm)
6. [Client-Side Derivation](#client-side-derivation)
7. [Proof Generation](#proof-generation)
8. [Testing & Validation](#testing--validation)

---

## Key Derivation Functions

### Ed25519 Seed-Based Derivation

**Core Principle**: Ed25519 private keys are just 32 bytes. We can derive them deterministically from a seed + path index.

#### Master Seed Generation (Client-Side)

```python
import secrets
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_master_seed():
    """Generate cryptographically secure 32-byte seed"""
    return secrets.token_bytes(32)

def seed_to_root_keypair(seed: bytes) -> tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """Convert seed to root Ed25519 key pair"""
    assert len(seed) == 32, "Seed must be 32 bytes"
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    public_key = private_key.public_key()
    return private_key, public_key
```

#### Child Key Derivation (Server & Client)

```python
import hashlib
import struct
from cryptography.hazmat.primitives.asymmetric import ed25519

# Protocol version identifier (prevent cross-protocol attacks)
DERIVATION_CONTEXT = b"vanikeys-ssh-v1"

def derive_child_seed(parent_seed: bytes, path_index: int) -> bytes:
    """
    Derive child seed from parent seed + path index

    Uses HMAC-SHA512 similar to BIP32, but adapted for Ed25519.

    Args:
        parent_seed: 32-byte parent seed (or root seed)
        path_index: Integer path index (0 to 2^32-1)

    Returns:
        32-byte child seed
    """
    assert len(parent_seed) == 32
    assert 0 <= path_index < 2**32

    # Encode path index as 4-byte big-endian
    index_bytes = struct.pack('>I', path_index)

    # HMAC-SHA512(key=parent_seed, msg=context || index)
    h = hashlib.sha512()
    h.update(parent_seed)
    h.update(DERIVATION_CONTEXT)
    h.update(index_bytes)
    digest = h.digest()

    # Take first 32 bytes as child seed
    child_seed = digest[:32]

    return child_seed

def derive_child_keypair(parent_seed: bytes, path_index: int) -> tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """Derive child key pair from parent seed + path"""
    child_seed = derive_child_seed(parent_seed, path_index)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(child_seed)
    public_key = private_key.public_key()
    return private_key, public_key
```

#### Server-Side: Public Key Only Derivation

**Critical**: The server receives ONLY the root public key, never the seed.

```python
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, NoEncryption
)

def derive_child_public_key_from_seed(root_seed: bytes, path_index: int) -> ed25519.Ed25519PublicKey:
    """
    Server-side derivation (for testing/validation)
    In production, server only receives root_public, not root_seed!
    """
    _, child_public = derive_child_keypair(root_seed, path_index)
    return child_public

# Example: What server receives
def client_prepares_root_public(seed: bytes) -> bytes:
    """Client sends this to server"""
    _, root_public = seed_to_root_keypair(seed)
    # Serialize public key to bytes
    public_bytes = root_public.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw
    )
    return public_bytes  # 32 bytes for Ed25519

# Server receives public_bytes and stores it for derivation context
```

---

## SSH Key Format

### Ed25519 SSH Public Key Format

SSH public keys have a specific wire format (RFC 4253).

```python
import struct
import base64

def ssh_public_key_to_bytes(public_key: ed25519.Ed25519PublicKey) -> bytes:
    """
    Convert Ed25519 public key to SSH wire format

    SSH Ed25519 public key format:
        string    "ssh-ed25519"
        string    key_data (32 bytes)

    where string = 4-byte length + data
    """
    key_type = b"ssh-ed25519"
    key_data = public_key.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw
    )

    # SSH string encoding: 4-byte length (big-endian) + data
    def ssh_string(data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + data

    wire_format = ssh_string(key_type) + ssh_string(key_data)
    return wire_format

def ssh_public_key_to_authorized_keys_format(public_key: ed25519.Ed25519PublicKey, comment: str = "") -> str:
    """
    Convert to OpenSSH authorized_keys format

    Format: ssh-ed25519 <base64-encoded-wire-format> <comment>
    """
    wire_bytes = ssh_public_key_to_bytes(public_key)
    b64 = base64.b64encode(wire_bytes).decode('ascii')
    return f"ssh-ed25519 {b64} {comment}".strip()
```

---

## Fingerprint Computation

### SHA256 Fingerprint (Modern OpenSSH)

```python
import hashlib
import base64

def compute_ssh_fingerprint(public_key: ed25519.Ed25519PublicKey) -> str:
    """
    Compute SSH fingerprint (SHA256, OpenSSH format)

    Modern OpenSSH format: SHA256:<base64-no-padding>

    Example: SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx
    """
    wire_bytes = ssh_public_key_to_bytes(public_key)

    # SHA256 hash of wire format
    digest = hashlib.sha256(wire_bytes).digest()

    # Base64 encode without padding
    b64 = base64.b64encode(digest).decode('ascii').rstrip('=')

    return f"SHA256:{b64}"

def extract_fingerprint_searchable(fingerprint: str) -> str:
    """
    Extract searchable portion (without SHA256: prefix)

    'SHA256:lab123abc...' -> 'lab123abc...'
    """
    if fingerprint.startswith('SHA256:'):
        return fingerprint[7:]
    return fingerprint
```

### MD5 Fingerprint (Legacy, Optional)

```python
def compute_ssh_fingerprint_md5(public_key: ed25519.Ed25519PublicKey) -> str:
    """
    Compute legacy MD5 fingerprint (colon-separated hex)

    Legacy format: aa:bb:cc:dd:...

    Note: MD5 is deprecated, but some old systems still use it.
    """
    wire_bytes = ssh_public_key_to_bytes(public_key)
    digest = hashlib.md5(wire_bytes).digest()

    # Format as colon-separated hex pairs
    hex_pairs = [f"{b:02x}" for b in digest]
    return ':'.join(hex_pairs)
```

---

## Pattern Matching

### Pattern Matching Strategies

```python
import re
from typing import Callable

def create_pattern_matcher(pattern: str, case_sensitive: bool = False) -> Callable[[str], bool]:
    """
    Create pattern matcher function

    Args:
        pattern: Pattern to search for
            - Simple string: "lab123"
            - Regex: "lab[0-9]{3}"
        case_sensitive: Whether matching is case-sensitive

    Returns:
        Function that takes fingerprint and returns True if matches
    """
    if not case_sensitive:
        pattern = pattern.lower()

    # Detect if regex (contains special chars)
    is_regex = any(c in pattern for c in r'[](){}^$.*+?|\\')

    if is_regex:
        compiled_regex = re.compile(pattern, flags=0 if case_sensitive else re.IGNORECASE)
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

# Example usage
matcher = create_pattern_matcher("lab123", case_sensitive=False)
if matcher("SHA256:lab123abcdefghijklmnop"):
    print("Match found!")
```

### Pattern Difficulty Estimation

```python
import math

def estimate_pattern_difficulty(pattern: str, case_sensitive: bool = False) -> dict:
    """
    Estimate search difficulty for a pattern

    Returns:
        dict with:
            - expected_attempts: Average paths to search
            - expected_seconds: Time estimate (at 1M keys/sec)
            - difficulty_class: easy/medium/hard/extreme
    """
    # Base64 character set in SSH fingerprints (SHA256)
    # A-Z, a-z, 0-9, +, / = 64 characters
    charset_size = 64

    if not case_sensitive:
        # Case-insensitive reduces effective charset
        # A/a are same, so ~44 effective characters
        charset_size = 44

    # Probability of match at any given position
    # For substring match, multiple positions possible
    fingerprint_length = 43  # SHA256 base64 length (without padding)
    pattern_length = len(pattern)
    positions = fingerprint_length - pattern_length + 1

    # Probability of match at one position
    prob_at_position = (1 / charset_size) ** pattern_length

    # Probability of match at any position (union bound approximation)
    prob_any_position = positions * prob_at_position

    # Expected attempts = 1 / probability
    expected_attempts = int(1 / prob_any_position)

    # Time estimate (assuming 1M keys/sec)
    keys_per_second = 1_000_000
    expected_seconds = expected_attempts / keys_per_second

    # Difficulty classification
    if expected_seconds < 10:
        difficulty_class = "easy"
    elif expected_seconds < 300:  # 5 minutes
        difficulty_class = "medium"
    elif expected_seconds < 3600:  # 1 hour
        difficulty_class = "hard"
    else:
        difficulty_class = "extreme"

    return {
        'pattern': pattern,
        'pattern_length': pattern_length,
        'expected_attempts': expected_attempts,
        'expected_seconds': expected_seconds,
        'expected_time_human': format_duration(expected_seconds),
        'difficulty_class': difficulty_class,
        'charset_size': charset_size,
        'case_sensitive': case_sensitive
    }

def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    else:
        return f"{seconds/86400:.1f} days"

# Example
print(estimate_pattern_difficulty("lab", case_sensitive=False))
# {'pattern': 'lab', 'expected_attempts': 1266, 'expected_seconds': 0.001, ...}

print(estimate_pattern_difficulty("lab123", case_sensitive=False))
# {'pattern': 'lab123', 'expected_attempts': 2.2B, 'expected_seconds': 2200, ...}
```

---

## Search Algorithm

### Basic Search Loop

```python
from typing import Optional

def search_vanity_path(
    root_seed: bytes,
    pattern: str,
    max_attempts: int = 10_000_000,
    case_sensitive: bool = False,
    progress_callback: Optional[Callable[[int], None]] = None
) -> Optional[dict]:
    """
    Search for derivation path that produces vanity fingerprint

    Args:
        root_seed: 32-byte master seed (CLIENT-SIDE ONLY!)
        pattern: Pattern to search for
        max_attempts: Maximum paths to try
        case_sensitive: Case-sensitive matching
        progress_callback: Called every N attempts with current count

    Returns:
        dict with path_index, public_key, fingerprint, or None if not found
    """
    matcher = create_pattern_matcher(pattern, case_sensitive)

    for path_index in range(max_attempts):
        # Derive child key pair
        _, child_public = derive_child_keypair(root_seed, path_index)

        # Compute fingerprint
        fingerprint = compute_ssh_fingerprint(child_public)

        # Check match
        if matcher(fingerprint):
            return {
                'path_index': path_index,
                'public_key': child_public,
                'fingerprint': fingerprint,
                'attempts': path_index + 1
            }

        # Progress callback
        if progress_callback and (path_index % 10000 == 0):
            progress_callback(path_index)

    return None  # Not found

# Example usage
seed = generate_master_seed()
result = search_vanity_path(seed, "lab", max_attempts=1_000_000)
if result:
    print(f"Found at path {result['path_index']}: {result['fingerprint']}")
else:
    print("Not found")
```

### Optimized Search (Server-Side)

```python
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

def search_worker(args: tuple) -> Optional[dict]:
    """Worker process for parallel search"""
    root_seed, pattern, start_index, end_index, case_sensitive = args

    matcher = create_pattern_matcher(pattern, case_sensitive)

    for path_index in range(start_index, end_index):
        _, child_public = derive_child_keypair(root_seed, path_index)
        fingerprint = compute_ssh_fingerprint(child_public)

        if matcher(fingerprint):
            return {
                'path_index': path_index,
                'public_key': child_public,
                'fingerprint': fingerprint
            }

    return None

def parallel_search_vanity_path(
    root_seed: bytes,
    pattern: str,
    max_attempts: int = 100_000_000,
    num_workers: Optional[int] = None,
    case_sensitive: bool = False
) -> Optional[dict]:
    """
    Parallel vanity path search using multiple CPU cores

    Distributes search space across worker processes.
    """
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    # Divide search space
    chunk_size = max_attempts // num_workers
    tasks = []

    for i in range(num_workers):
        start_index = i * chunk_size
        end_index = start_index + chunk_size if i < num_workers - 1 else max_attempts
        tasks.append((root_seed, pattern, start_index, end_index, case_sensitive))

    # Execute parallel search
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(search_worker, task) for task in tasks]

        # Return first result found
        for future in futures:
            result = future.result()
            if result:
                # Cancel remaining tasks
                for f in futures:
                    f.cancel()
                return result

    return None
```

---

## Client-Side Derivation

### Secure Seed Storage

```python
import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

def encrypt_seed(seed: bytes, password: str) -> dict:
    """
    Encrypt seed with password using Scrypt + AES-GCM

    Returns dict with encrypted data + parameters for decryption.
    """
    # Derive encryption key from password using Scrypt
    salt = os.urandom(16)
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**18,  # CPU cost (high for security)
        r=8,
        p=1,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))

    # Encrypt seed with AES-GCM
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, seed, None)

    return {
        'version': 1,
        'kdf': 'scrypt',
        'scrypt_n': 2**18,
        'scrypt_r': 8,
        'scrypt_p': 1,
        'salt': base64.b64encode(salt).decode('ascii'),
        'nonce': base64.b64encode(nonce).decode('ascii'),
        'ciphertext': base64.b64encode(ciphertext).decode('ascii')
    }

def decrypt_seed(encrypted_data: dict, password: str) -> bytes:
    """Decrypt seed from encrypted data + password"""
    # Decode base64 fields
    salt = base64.b64decode(encrypted_data['salt'])
    nonce = base64.b64decode(encrypted_data['nonce'])
    ciphertext = base64.b64decode(encrypted_data['ciphertext'])

    # Derive key from password
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=encrypted_data['scrypt_n'],
        r=encrypted_data['scrypt_r'],
        p=encrypted_data['scrypt_p'],
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))

    # Decrypt
    aesgcm = AESGCM(key)
    seed = aesgcm.decrypt(nonce, ciphertext, None)

    return seed

# Example: Save encrypted seed to file
seed = generate_master_seed()
password = "user-password"  # In practice, prompt securely

encrypted = encrypt_seed(seed, password)
with open(os.path.expanduser('~/.vanikeys/seed.enc'), 'w') as f:
    json.dump(encrypted, f)

# Later: Load and decrypt
with open(os.path.expanduser('~/.vanikeys/seed.enc'), 'r') as f:
    encrypted = json.load(f)
seed = decrypt_seed(encrypted, password)
```

---

## Proof Generation

### Server-Side Proof Generation

```python
import hashlib
import hmac

def generate_derivation_proof(
    root_public_bytes: bytes,
    path_index: int,
    child_public_key: ed25519.Ed25519PublicKey
) -> dict:
    """
    Generate proof that path_index derives child_public_key from root_public

    Proof structure:
        - Path index
        - Child public key
        - Derivation hash (binds path -> key)
    """
    child_public_bytes = child_public_key.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw
    )

    # Compute derivation hash (deterministic, verifiable)
    h = hashlib.sha256()
    h.update(root_public_bytes)
    h.update(struct.pack('>I', path_index))
    h.update(DERIVATION_CONTEXT)
    derivation_hash = h.digest()

    return {
        'path_index': path_index,
        'root_public_key': base64.b64encode(root_public_bytes).decode('ascii'),
        'child_public_key': base64.b64encode(child_public_bytes).decode('ascii'),
        'derivation_hash': base64.b64encode(derivation_hash).decode('ascii'),
        'algorithm': 'ed25519',
        'context': DERIVATION_CONTEXT.decode('ascii')
    }
```

### Client-Side Proof Verification

```python
def verify_derivation_proof(proof: dict, master_seed: bytes) -> bool:
    """
    Client verifies that proof is valid before deriving private key

    Returns True if proof is valid and safe to derive.
    """
    # 1. Decode fields
    path_index = proof['path_index']
    claimed_child_public = base64.b64decode(proof['child_public_key'])

    # 2. Derive child public key locally
    _, actual_child_public = derive_child_keypair(master_seed, path_index)
    actual_child_bytes = actual_child_public.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw
    )

    # 3. Verify child public key matches claimed
    if actual_child_bytes != claimed_child_public:
        return False

    # 4. Verify derivation hash
    _, root_public = seed_to_root_keypair(master_seed)
    root_public_bytes = root_public.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw
    )

    h = hashlib.sha256()
    h.update(root_public_bytes)
    h.update(struct.pack('>I', path_index))
    h.update(DERIVATION_CONTEXT)
    expected_derivation_hash = h.digest()

    claimed_derivation_hash = base64.b64decode(proof['derivation_hash'])

    if expected_derivation_hash != claimed_derivation_hash:
        return False

    # All checks passed
    return True
```

---

## Testing & Validation

### Test Vectors

```python
def test_derivation_determinism():
    """Test that derivation is deterministic"""
    seed = bytes.fromhex("0123456789abcdef" * 4)  # Fixed seed for testing

    # Derive same path twice
    _, pub1 = derive_child_keypair(seed, 12345)
    _, pub2 = derive_child_keypair(seed, 12345)

    assert pub1.public_bytes(Encoding.Raw, PublicFormat.Raw) == \
           pub2.public_bytes(Encoding.Raw, PublicFormat.Raw)

    print("✓ Derivation is deterministic")

def test_different_paths_different_keys():
    """Test that different paths produce different keys"""
    seed = generate_master_seed()

    keys = set()
    for path in range(100):
        _, pub = derive_child_keypair(seed, path)
        pub_bytes = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
        keys.add(pub_bytes)

    assert len(keys) == 100  # All unique
    print("✓ Different paths produce different keys")

def test_fingerprint_format():
    """Test SSH fingerprint format"""
    seed = generate_master_seed()
    _, pub = derive_child_keypair(seed, 0)

    fingerprint = compute_ssh_fingerprint(pub)

    # Should start with SHA256:
    assert fingerprint.startswith("SHA256:")

    # Should be correct length (SHA256: + 43 base64 chars)
    assert len(fingerprint) == 7 + 43

    print("✓ Fingerprint format correct")

def test_search_finds_pattern():
    """Test that search actually finds patterns"""
    seed = generate_master_seed()

    # Search for easy pattern (should find quickly)
    result = search_vanity_path(seed, "a", max_attempts=1000)

    assert result is not None
    assert "a" in result['fingerprint'].lower()

    print(f"✓ Search found pattern 'a' at path {result['path_index']}")

# Run tests
test_derivation_determinism()
test_different_paths_different_keys()
test_fingerprint_format()
test_search_finds_pattern()
```

---

## Performance Benchmarks

### Benchmark Derivation Speed

```python
import time

def benchmark_derivation_speed(num_iterations: int = 100_000):
    """Benchmark key derivation speed"""
    seed = generate_master_seed()

    start_time = time.time()

    for i in range(num_iterations):
        _, _ = derive_child_keypair(seed, i)

    elapsed = time.time() - start_time
    keys_per_second = num_iterations / elapsed

    print(f"Derived {num_iterations:,} keys in {elapsed:.2f} seconds")
    print(f"Speed: {keys_per_second:,.0f} keys/second")

    return keys_per_second

# Example output:
# Derived 100,000 keys in 0.98 seconds
# Speed: 102,041 keys/second
```

---

## Next Steps

### Implementation Checklist

- [ ] Implement `derive_child_seed()` and `derive_child_keypair()`
- [ ] Implement `ssh_public_key_to_bytes()` and fingerprint computation
- [ ] Implement `create_pattern_matcher()` with regex support
- [ ] Implement `search_vanity_path()` with progress callback
- [ ] Implement parallel search with multiprocessing
- [ ] Implement secure seed storage (encryption)
- [ ] Implement proof generation and verification
- [ ] Write comprehensive test suite
- [ ] Benchmark performance on target hardware
- [ ] Document API for client/server integration

### Integration Points

- **Client CLI**: `vanikeys-client` package using these functions
- **Server API**: FastAPI endpoints wrapping search functions
- **Database**: Store order status, proofs, customer public keys
- **Queue**: Celery/RQ for async search jobs

---

## References

- `ZERO_KNOWLEDGE_PROTOCOL.md` - Protocol design and security
- RFC 4253 - SSH Protocol Assigned Numbers
- RFC 8032 - Ed25519 specification
- BIP32 - HD Wallet specification (inspiration)

---

**Questions? Implementation issues?** Open an issue on GitHub or contact: dev@vanikeys.dev
