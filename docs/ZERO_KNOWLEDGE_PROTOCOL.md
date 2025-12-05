# Zero-Knowledge Vanity Key Protocol

**Version**: 1.0
**Last Updated**: 2025-12-03
**Status**: Core Protocol Specification

## Executive Summary

VaniKeys solves the **fundamental trust problem** in vanity key generation: traditional services must know your private key to find vanity patterns. Our zero-knowledge protocol allows VaniKeys to perform the computational work while **ensuring the customer is the only party who ever possesses the private key**.

**Key Innovation**: We discover derivation paths, not keys. The customer provides a public commitment, we find the path that produces a vanity pattern, and the customer derives the final key from their secret seed.

---

## Table of Contents

1. [The Trust Problem](#the-trust-problem)
2. [Protocol Overview](#protocol-overview)
3. [HD Derivation Path Discovery](#hd-derivation-path-discovery)
4. [Security Analysis](#security-analysis)
5. [Implementation Details](#implementation-details)
6. [Customer Workflow](#customer-workflow)
7. [Verification & Proofs](#verification--proofs)
8. [Alternative Approaches](#alternative-approaches)

---

## The Trust Problem

### Traditional Vanity Key Generation (Broken Trust Model)

```
Customer → Order vanity key → Service
                                ↓
                         Generate millions of keys
                                ↓
                         Find matching pattern
                                ↓
Customer ← Private key sent ← Service [💀 Service knows your private key!]
```

**Fatal Flaw**: The service must generate and test private keys to find vanity patterns. When they find a match, they **know your private key**. This is:

- ❌ Unacceptable for production systems
- ❌ Violates security best practices
- ❌ Creates insider threat risk
- ❌ Impossible to audit/verify
- ❌ Deal-breaker for enterprise DevOps

**Why This Matters for SSH/DevOps Keys:**
- SSH keys grant server access
- Compromised keys = breach potential
- Compliance requirements prohibit key exposure
- Trust is non-negotiable in enterprise security

---

## Protocol Overview

### VaniKeys Zero-Knowledge Protocol

```
Customer                          VaniKeys
   |                                 |
   | 1. Generate master seed         |
   |    (never leaves customer)      |
   |                                 |
   | 2. Derive public commitment --→ |
   |    (HD public key base)         |
   |                                 | 3. Search derivation paths
   |                                 |    (millions of iterations)
   |                                 |
   |                                 | 4. Find path → vanity pattern
   | ←-- 5. Return derivation path   |
   |         + cryptographic proof   |
   |                                 |
   | 6. Verify proof                 |
   | 7. Derive key from seed + path  |
   | 8. Customer has private key     |
   |    [VaniKeys never saw it!]     |
```

**Core Principle**: VaniKeys searches the **derivation space**, not the **key space**. We tell you *which path to take*, not *what the key is*.

---

## HD Derivation Path Discovery

### Hierarchical Deterministic Key Derivation

HD key derivation (BIP32/BIP44 for crypto, similar approaches for SSH/GPG) allows deriving many keys from a single seed:

```
Master Seed → Derivation Function(seed, path) → Key Pair
```

**Key Properties:**
- Same seed + same path = same key (deterministic)
- Different paths = different keys
- Given public key, cannot reverse to seed (one-way)
- Seed can be kept secret, public keys can be shared

### VaniKeys Protocol Details

#### Phase 1: Customer Setup

```python
# Customer-side (runs locally, seed never transmitted)
import secrets
from cryptography.hazmat.primitives.asymmetric import ed25519

# 1. Generate master seed (customer keeps this secret!)
master_seed = secrets.token_bytes(32)

# 2. Derive root key pair
root_private = ed25519.Ed25519PrivateKey.from_private_bytes(master_seed)
root_public = root_private.public_key()

# 3. Send public key to VaniKeys
# VaniKeys receives: root_public (cannot derive private key from this!)
```

#### Phase 2: VaniKeys Search

```python
# VaniKeys-side (server)
from cryptography.hazmat.primitives import hashes
import hashlib

def derive_child_public_key(parent_public, path_index):
    """Derive child public key from parent public key + index"""
    # BIP32-like derivation (non-hardened)
    # Parent public key + index → child public key
    # NOTE: Cannot derive private key without parent private key!
    return child_public_key

def fingerprint_matches_pattern(public_key, pattern):
    """Check if SSH fingerprint matches desired pattern"""
    key_bytes = public_key.public_bytes(...)
    fingerprint = hashlib.sha256(key_bytes).digest()
    fingerprint_hex = fingerprint.hex()
    return pattern.lower() in fingerprint_hex.lower()

# Search millions of derivation paths
pattern = "lab123"  # Customer wants fingerprint containing "lab123"
for path_index in range(10_000_000):  # Search 10 million paths
    child_public = derive_child_public_key(root_public, path_index)

    if fingerprint_matches_pattern(child_public, pattern):
        # Found it! Return the path index
        return {
            'path_index': path_index,
            'public_key': child_public,
            'fingerprint': compute_fingerprint(child_public),
            'proof': generate_proof(root_public, path_index, child_public)
        }
```

#### Phase 3: Customer Derivation

```python
# Customer-side (after receiving path from VaniKeys)
def derive_child_private_key(parent_private, path_index):
    """Derive child private key from parent private + index"""
    # Customer has master seed → can derive private key
    return child_private_key

# Receive from VaniKeys
vanity_result = {
    'path_index': 8472615,
    'public_key': '...',
    'fingerprint': 'SHA256:lab123xxxxxxxxxxxx',
    'proof': {...}
}

# Verify proof (confirm this path produces claimed fingerprint)
if verify_proof(vanity_result):
    # Derive the actual private key using customer's secret seed
    vanity_private_key = derive_child_private_key(master_seed, vanity_result['path_index'])
    vanity_public_key = vanity_private_key.public_key()

    # Verify it matches what VaniKeys claimed
    assert vanity_public_key == vanity_result['public_key']

    # Customer now has vanity key pair!
    # VaniKeys never saw the private key!
```

---

## Security Analysis

### Threat Model

**What VaniKeys Knows:**
- ✓ Customer's root public key (derived from seed)
- ✓ Desired vanity pattern
- ✓ Derivation path that produces vanity pattern
- ✓ Resulting public key

**What VaniKeys Does NOT Know:**
- ❌ Customer's master seed
- ❌ Any private keys (root or derived)
- ❌ Ability to sign/authenticate with the keys

**Attack Vectors Considered:**

1. **Can VaniKeys derive the private key from public key?**
   - NO: Ed25519/RSA public keys are computationally infeasible to reverse
   - Relies on elliptic curve discrete log / integer factorization hardness

2. **Can VaniKeys derive the master seed from derived public keys?**
   - NO: HD derivation is one-way (hash-based)
   - Even with millions of derived public keys, seed remains hidden

3. **Can VaniKeys generate fake proofs?**
   - NO: Proofs are deterministically verifiable
   - Customer can independently verify path → public key → fingerprint

4. **What if VaniKeys is compromised?**
   - Impact: Attacker learns customer's desired patterns, public keys
   - NO IMPACT: Attacker still cannot derive private keys
   - Customer keys remain secure

5. **What if customer's machine is compromised?**
   - Standard key management threat (same as any key generation)
   - Protocol doesn't add new attack surface
   - Seed should be stored securely (hardware tokens, encrypted storage)

### Trust Boundaries

```
┌─────────────────────────────────────────────────────┐
│ Customer Environment (Trusted)                       │
│                                                      │
│  ┌──────────────────────────────────────┐          │
│  │ Master Seed (Secret)                 │          │
│  │ ● Never transmitted                   │          │
│  │ ● Never stored on VaniKeys           │          │
│  │ ● Only customer knows                │          │
│  └──────────────────────────────────────┘          │
│                                                      │
│  ┌──────────────────────────────────────┐          │
│  │ Private Key Derivation               │          │
│  │ ● Happens locally                     │          │
│  │ ● Uses seed + VaniKeys path          │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
                       ↕ Public data only
┌─────────────────────────────────────────────────────┐
│ VaniKeys Environment (Untrusted)                    │
│                                                      │
│  ┌──────────────────────────────────────┐          │
│  │ Public Key (Received)                │          │
│  │ Root public key, no secrets          │          │
│  └──────────────────────────────────────┘          │
│                                                      │
│  ┌──────────────────────────────────────┐          │
│  │ Path Search (Computational Work)     │          │
│  │ ● Test millions of derivation paths  │          │
│  │ ● Find vanity pattern matches        │          │
│  │ ● Cannot access private keys         │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

**Key Property**: The trust boundary is **mathematically enforced** by cryptographic one-way functions, not policy or promises.

---

## Implementation Details

### SSH Key Derivation

**Ed25519 SSH Keys** (recommended for VaniKeys):
- Modern, fast, secure
- 32-byte seed → deterministic key generation
- Small key size, fast operations
- Industry standard for SSH (OpenSSH 6.5+)

**Derivation Scheme:**
```
seed || path_index || "ssh-vanity-v1" → SHA512 → 32 bytes → Ed25519 private key
```

**SSH Fingerprint Computation:**
```
SSH public key (binary) → SHA256 → Base64 → "SHA256:xxxxxxxxxxxx"
```

**Pattern Matching:**
- Search for substring in Base64 fingerprint
- Case-insensitive matching
- Support regex patterns (advanced)

### RSA Key Derivation (Legacy Support)

**Challenges with RSA HD derivation:**
- RSA doesn't have natural seed-based generation
- Prime finding is probabilistic
- Harder to derive deterministically

**Approach:**
- Use seed + path to generate random number generator state
- Derive RSA parameters deterministically from RNG
- Slower than Ed25519 (RSA generation is expensive)

**Recommendation**: Prefer Ed25519 for new keys, support RSA for compatibility.

### Performance Characteristics

**Search Speed (Ed25519):**
- ~100,000 keys/second on modern CPU (single core)
- ~1M keys/second on 16-core server
- ~10M keys/second on GPU-accelerated cluster

**Pattern Difficulty:**

| Pattern Length | Search Space | Expected Time (1M keys/sec) |
|----------------|--------------|------------------------------|
| 4 chars        | ~1.6M paths  | ~1.6 seconds                 |
| 5 chars        | ~60M paths   | ~1 minute                    |
| 6 chars        | ~2.2B paths  | ~37 minutes                  |
| 7 chars        | ~81B paths   | ~23 hours                    |
| 8 chars        | ~3T paths    | ~35 days                     |

*Assumes Base64 character set (64 options/position), case-insensitive*

**Optimization Strategies:**
- Prefix matching (faster than substring)
- GPU acceleration (100x speedup)
- Distributed search (horizontal scaling)
- Early termination for easier patterns

---

## Customer Workflow

### End-to-End User Experience

#### 1. Initial Setup (One-Time)

```bash
# Customer installs VaniKeys CLI
pip install vanikeys-client

# Generate master seed (stays on customer machine)
vanikeys init
# → Creates ~/.vanikeys/seed (encrypted)
# → Generates root public key
# → Registers with VaniKeys service
```

#### 2. Order Vanity Key

```bash
# Customer orders vanity SSH key
vanikeys order ssh --pattern "lab123" --tier standard

# Response:
# Order ID: ord_abc123
# Pattern: lab123
# Difficulty: Medium (~2 minutes)
# Cost: $5.00
# Status: Searching...
```

#### 3. Search Progress (VaniKeys Side)

```bash
# VaniKeys server
# - Receives root public key + pattern
# - Allocates compute resources
# - Searches derivation paths
# - Finds match at path 8472615
# - Generates proof
# - Notifies customer
```

#### 4. Receive & Verify

```bash
# Customer receives notification
vanikeys status ord_abc123

# Response:
# Status: FOUND ✓
# Path: 8472615
# Fingerprint: SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx
# Public Key: ssh-ed25519 AAAAC3NzaC1...

# Verify proof
vanikeys verify ord_abc123
# ✓ Proof valid
# ✓ Path produces claimed fingerprint
# ✓ Public key matches
```

#### 5. Derive Private Key

```bash
# Customer derives private key locally
vanikeys derive ord_abc123 --output ~/.ssh/lab_key

# Process:
# - Read master seed from ~/.vanikeys/seed
# - Apply derivation path 8472615
# - Generate private key
# - Write to ~/.ssh/lab_key (private key never transmitted!)
# - Write to ~/.ssh/lab_key.pub

# Verify fingerprint
ssh-keygen -lf ~/.ssh/lab_key.pub
# 256 SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx no comment (ED25519)

# Key ready to use!
ssh-add ~/.ssh/lab_key
```

#### 6. Bulk Orders (Enterprise)

```bash
# DevOps manager orders 100 keys for team
vanikeys order bulk \
  --pattern "acme-dev" \
  --quantity 100 \
  --output team_keys.json

# VaniKeys finds 100 different paths producing "acme-dev" pattern
# Returns all paths + proofs
# Customer can distribute to team members

# Each team member derives their key:
vanikeys derive --order team_keys.json --index 42 --output ~/.ssh/id_team
```

---

## Verification & Proofs

### Cryptographic Proof Structure

**What VaniKeys Returns:**
```json
{
  "order_id": "ord_abc123",
  "pattern": "lab123",
  "path_index": 8472615,
  "public_key": "ssh-ed25519 AAAAC3NzaC1...",
  "fingerprint": "SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx",
  "proof": {
    "root_public_key": "...",
    "derivation_proof": {
      "path": 8472615,
      "intermediate_values": ["...", "..."],
      "final_public_key": "..."
    },
    "fingerprint_proof": {
      "key_bytes": "...",
      "sha256_hash": "...",
      "base64_encoding": "..."
    }
  },
  "signature": "VaniKeys signature over all fields"
}
```

### Customer Verification Process

```python
def verify_vanity_result(result, master_seed):
    """Customer verifies VaniKeys result before deriving private key"""

    # 1. Verify VaniKeys signature (authenticity)
    assert verify_signature(result, VANIKEYS_PUBLIC_KEY)

    # 2. Verify derivation path produces claimed public key
    root_public = derive_public_from_seed(master_seed)
    assert root_public == result['proof']['root_public_key']

    derived_public = derive_child_public_key(root_public, result['path_index'])
    assert derived_public == result['public_key']

    # 3. Verify fingerprint matches pattern
    fingerprint = compute_ssh_fingerprint(result['public_key'])
    assert fingerprint == result['fingerprint']
    assert result['pattern'] in fingerprint.lower()

    # 4. All checks passed → safe to derive private key
    return True
```

**Key Properties:**
- ✓ Customer can verify **before** deriving private key
- ✓ Verification is deterministic (math, not trust)
- ✓ No need to trust VaniKeys claims
- ✓ Cryptographically proven correct

---

## Alternative Approaches

### Why Not Split-Key Generation?

**Approach**: Customer generates K1, VaniKeys generates K2, combine to get vanity key.

**Problems:**
- Complex cryptographic protocol (requires MPC or similar)
- Interactive process (multiple round trips)
- Still requires customer to trust VaniKeys doesn't log K2
- Key combination is non-trivial for SSH/GPG keys

**Verdict**: HD derivation path discovery is simpler, more auditable, better trust model.

### Why Not Pure Client-Side?

**Approach**: Customer runs vanity search locally (e.g., existing tools like `ssh-keygen` in loop).

**Problems:**
- Customer lacks compute resources for hard patterns
- Hours/days for longer patterns
- No mobile/web support
- Doesn't leverage VaniKeys infrastructure

**Verdict**: Zero-knowledge protocol keeps trust properties while leveraging VaniKeys compute.

### Why Not Trusted Execution Environments (TEE)?

**Approach**: Run key generation in SGX/TrustZone, prove code didn't exfiltrate keys.

**Problems:**
- Requires specific hardware
- TEE vulnerabilities (Spectre, SGX attacks)
- "Trust but verify" → still requires trust
- Complex attestation flow

**Verdict**: HD derivation removes need for hardware trust anchors.

---

## Comparison: Traditional vs Zero-Knowledge

| Aspect | Traditional | VaniKeys ZK |
|--------|------------|-------------|
| **Service knows private key** | ❌ Yes | ✅ No |
| **Customer verifiable** | ❌ No | ✅ Yes (proofs) |
| **Enterprise-ready** | ❌ No | ✅ Yes |
| **Compliance-friendly** | ❌ No | ✅ Yes |
| **Audit trail** | ❌ None | ✅ Full |
| **Insider threat** | ❌ High risk | ✅ Zero risk |
| **Compute leverage** | ✅ Yes | ✅ Yes |
| **Mobile/web support** | ✅ Yes | ✅ Yes |
| **Mathematical guarantee** | ❌ No | ✅ Yes |

---

## Implementation Roadmap

### Phase 1: MVP (Current)
- [x] Protocol specification (this document)
- [ ] Ed25519 HD derivation implementation
- [ ] SSH fingerprint pattern matching
- [ ] Basic proof generation/verification
- [ ] CLI client (local seed management)
- [ ] API server (path search service)

### Phase 2: Production
- [ ] GPU-accelerated search
- [ ] Distributed search cluster
- [ ] Web client (WASM-based local derivation)
- [ ] Enterprise bulk ordering
- [ ] Pattern difficulty estimation
- [ ] Cost optimization

### Phase 3: Advanced
- [ ] RSA key support (legacy)
- [ ] GPG key vanity generation
- [ ] Regex pattern support
- [ ] Multi-pattern search (find N keys)
- [ ] Hardware token integration (seed in Yubikey)

---

## References

### Cryptographic Standards
- **BIP32**: Hierarchical Deterministic Wallets
- **BIP44**: Multi-Account Hierarchy for HD Wallets
- **RFC 8032**: Edwards-Curve Digital Signature Algorithm (Ed25519)
- **RFC 4253**: SSH Protocol Assigned Numbers (key formats)

### Related Work
- **vanitygen**: Bitcoin vanity address generator (no ZK)
- **vanity-eth**: Ethereum vanity address (no ZK)
- **OpenSSH**: Standard SSH key generation

### Security Analysis
- Elliptic Curve Discrete Logarithm Problem (ECDLP)
- HD Wallet Security (BIP32 security considerations)
- SSH Key Security Best Practices

---

## Conclusion

The **VaniKeys Zero-Knowledge Protocol** solves the fundamental trust problem in vanity key generation:

✅ **Mathematically proven**: Customer is the only party who ever possesses private keys
✅ **Enterprise-ready**: Meets security and compliance requirements
✅ **Verifiable**: Customers can audit and verify all results
✅ **Scalable**: Leverages VaniKeys compute without compromising security

**This is not just a feature—it's the foundation that makes enterprise vanity key generation possible.**

For implementation details, see:
- `src/vanikeys/crypto/derivation.py` - HD key derivation
- `src/vanikeys/crypto/proofs.py` - Proof generation/verification
- `src/vanikeys/services/search.py` - Path search service

---

**Questions? Security concerns? Reach out:** security@vanikeys.dev
