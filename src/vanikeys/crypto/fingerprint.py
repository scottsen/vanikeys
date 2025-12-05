"""
SSH Fingerprint Computation

Implements SSH public key fingerprint computation according to OpenSSH standards.

Supports:
- SHA256 fingerprint (modern, default)
- MD5 fingerprint (legacy, for compatibility)
- SSH wire format encoding
- Authorized keys format

See: RFC 4253 (SSH Protocol) for key format specifications
"""

import hashlib
import struct
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)


def ssh_public_key_to_bytes(public_key: ed25519.Ed25519PublicKey) -> bytes:
    """
    Convert Ed25519 public key to SSH wire format.

    SSH Ed25519 public key wire format (RFC 4253):
        string    "ssh-ed25519"       (key type identifier)
        string    key_data            (32 bytes for Ed25519)

    where string = 4-byte length (big-endian) + data

    Args:
        public_key: Ed25519 public key

    Returns:
        SSH wire format bytes

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> seed = generate_master_seed()
        >>> _, pub = seed_to_root_keypair(seed)
        >>> wire_bytes = ssh_public_key_to_bytes(pub)
        >>> len(wire_bytes) > 32  # Wire format is larger than raw key
        True
    """
    key_type = b"ssh-ed25519"
    key_data = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)

    # SSH string encoding: 4-byte length (big-endian) + data
    def ssh_string(data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + data

    wire_format = ssh_string(key_type) + ssh_string(key_data)
    return wire_format


def ssh_public_key_to_authorized_keys_format(
    public_key: ed25519.Ed25519PublicKey, comment: str = ""
) -> str:
    """
    Convert Ed25519 public key to OpenSSH authorized_keys format.

    Format: ssh-ed25519 <base64-encoded-wire-format> <comment>

    This is the format used in:
    - ~/.ssh/authorized_keys
    - ~/.ssh/id_ed25519.pub
    - GitHub/GitLab SSH key upload

    Args:
        public_key: Ed25519 public key
        comment: Optional comment (e.g., email, identifier)

    Returns:
        OpenSSH authorized_keys format string

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> seed = generate_master_seed()
        >>> _, pub = seed_to_root_keypair(seed)
        >>> auth_key = ssh_public_key_to_authorized_keys_format(pub, "user@host")
        >>> auth_key.startswith("ssh-ed25519 ")
        True
        >>> "user@host" in auth_key
        True
    """
    wire_bytes = ssh_public_key_to_bytes(public_key)
    b64 = base64.b64encode(wire_bytes).decode("ascii")
    return f"ssh-ed25519 {b64} {comment}".strip()


def compute_ssh_fingerprint(public_key: ed25519.Ed25519PublicKey) -> str:
    """
    Compute SSH fingerprint (SHA256, modern OpenSSH format).

    Modern OpenSSH format: SHA256:<base64-no-padding>

    This is what you see when running:
        ssh-keygen -lf ~/.ssh/id_ed25519.pub

    The fingerprint is computed as:
        1. Encode public key to SSH wire format
        2. SHA256 hash of wire format
        3. Base64 encode hash (strip padding '=')
        4. Prepend "SHA256:"

    Args:
        public_key: Ed25519 public key

    Returns:
        SSH fingerprint string (e.g., "SHA256:lab123xxx...")

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> seed = generate_master_seed()
        >>> _, pub = seed_to_root_keypair(seed)
        >>> fp = compute_ssh_fingerprint(pub)
        >>> fp.startswith("SHA256:")
        True
        >>> len(fp)
        50  # "SHA256:" (7 chars) + 43 chars base64
    """
    wire_bytes = ssh_public_key_to_bytes(public_key)

    # SHA256 hash of wire format
    digest = hashlib.sha256(wire_bytes).digest()

    # Base64 encode without padding
    b64 = base64.b64encode(digest).decode("ascii").rstrip("=")

    return f"SHA256:{b64}"


def compute_ssh_fingerprint_md5(public_key: ed25519.Ed25519PublicKey) -> str:
    """
    Compute SSH fingerprint (MD5, legacy format).

    Legacy format: aa:bb:cc:dd:ee:...  (colon-separated hex pairs)

    This is the old format used by OpenSSH before version 6.8.
    Still used by some systems, but SHA256 is preferred.

    Example output: 16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48

    Args:
        public_key: Ed25519 public key

    Returns:
        MD5 fingerprint string (colon-separated hex)

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> seed = generate_master_seed()
        >>> _, pub = seed_to_root_keypair(seed)
        >>> fp_md5 = compute_ssh_fingerprint_md5(pub)
        >>> ":" in fp_md5
        True
        >>> len(fp_md5.split(":"))
        16  # 16 hex pairs
    """
    wire_bytes = ssh_public_key_to_bytes(public_key)

    # MD5 hash of wire format
    digest = hashlib.md5(wire_bytes).digest()

    # Format as colon-separated hex pairs
    hex_pairs = [f"{b:02x}" for b in digest]
    return ":".join(hex_pairs)


def extract_fingerprint_searchable(fingerprint: str) -> str:
    """
    Extract searchable portion of fingerprint (remove prefix).

    Converts:
        "SHA256:lab123abc..." → "lab123abc..."
        "16:27:ac:a5:..." → "16:27:ac:a5:..."

    This is the portion used for pattern matching.

    Args:
        fingerprint: Full SSH fingerprint string

    Returns:
        Searchable portion (without "SHA256:" prefix if present)

    Example:
        >>> fp = "SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx"
        >>> extract_fingerprint_searchable(fp)
        'lab123xxxxxxxxxxxxxxxxxxxxxxxxx'
        >>> extract_fingerprint_searchable("16:27:ac")
        '16:27:ac'
    """
    if fingerprint.startswith("SHA256:"):
        return fingerprint[7:]  # Remove "SHA256:" prefix
    return fingerprint


def format_fingerprint_human_readable(fingerprint: str) -> str:
    """
    Format fingerprint for human-readable display.

    Adds spacing for readability:
        "SHA256:lab123abc..." → "SHA256: lab123abc..."

    Args:
        fingerprint: SSH fingerprint

    Returns:
        Human-readable formatted fingerprint

    Example:
        >>> fp = "SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx"
        >>> format_fingerprint_human_readable(fp)
        'SHA256: lab123xxxxxxxxxxxxxxxxxxxxxxxxx'
    """
    if fingerprint.startswith("SHA256:") and not fingerprint.startswith("SHA256: "):
        return f"SHA256: {fingerprint[7:]}"
    return fingerprint


def fingerprint_to_bytes(fingerprint: str) -> bytes:
    """
    Convert base64 fingerprint back to raw bytes.

    Useful for cryptographic operations on fingerprints.

    Args:
        fingerprint: SSH fingerprint (SHA256 format)

    Returns:
        32-byte SHA256 hash

    Raises:
        ValueError: If fingerprint format is invalid

    Example:
        >>> from vanikeys.crypto import generate_master_seed, seed_to_root_keypair
        >>> seed = generate_master_seed()
        >>> _, pub = seed_to_root_keypair(seed)
        >>> fp = compute_ssh_fingerprint(pub)
        >>> fp_bytes = fingerprint_to_bytes(fp)
        >>> len(fp_bytes)
        32
    """
    if not fingerprint.startswith("SHA256:"):
        raise ValueError("Only SHA256 fingerprints supported for bytes conversion")

    # Extract base64 portion
    b64_part = extract_fingerprint_searchable(fingerprint)

    # Add back padding if needed
    padding_needed = (4 - len(b64_part) % 4) % 4
    b64_part += "=" * padding_needed

    # Decode
    return base64.b64decode(b64_part)


def compare_fingerprints(fp1: str, fp2: str) -> bool:
    """
    Compare two fingerprints for equality.

    Handles:
    - Different formats (with/without spacing)
    - Case differences

    Args:
        fp1: First fingerprint
        fp2: Second fingerprint

    Returns:
        True if fingerprints are equal

    Example:
        >>> fp1 = "SHA256:abc123"
        >>> fp2 = "SHA256: abc123"
        >>> compare_fingerprints(fp1, fp2)
        True
    """
    # Normalize: remove spaces, lowercase
    norm1 = fp1.replace(" ", "").lower()
    norm2 = fp2.replace(" ", "").lower()
    return norm1 == norm2
