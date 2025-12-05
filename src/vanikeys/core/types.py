"""Core data types for VaniKeys."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class KeyType(Enum):
    """Supported key types."""
    ED25519 = "ed25519"
    SECP256K1 = "secp256k1"
    RSA = "rsa"
    DID_KEY = "did:key"


class PatternMatchType(Enum):
    """Pattern matching strategies."""
    PREFIX = "prefix"
    SUFFIX = "suffix"
    CONTAINS = "contains"
    REGEX = "regex"


class ExportFormat(Enum):
    """Key export formats."""
    PEM = "pem"
    JSON = "json"
    HEX = "hex"
    BASE58 = "base58"
    DID = "did"


@dataclass
class KeyPair:
    """Represents a generated cryptographic key pair."""

    private_key: bytes
    public_key: bytes
    address: str  # Human-readable representation (address, DID, fingerprint, etc.)
    key_type: KeyType
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate key pair after initialization."""
        if not self.private_key:
            raise ValueError("Private key cannot be empty")
        if not self.public_key:
            raise ValueError("Public key cannot be empty")
        if not self.address:
            raise ValueError("Address cannot be empty")


@dataclass
class PatternConfig:
    """Configuration for pattern matching."""

    pattern: str
    match_type: PatternMatchType
    case_sensitive: bool = True

    def __post_init__(self) -> None:
        """Validate pattern configuration."""
        if not self.pattern:
            raise ValueError("Pattern cannot be empty")

        # Normalize pattern if case-insensitive
        if not self.case_sensitive:
            self.pattern = self.pattern.upper()


@dataclass
class GenerationConfig:
    """Configuration for key generation."""

    key_type: KeyType
    pattern_config: PatternConfig
    num_workers: int = 1
    max_attempts: int | None = None  # None = unlimited
    timeout_seconds: float | None = None  # None = unlimited

    def __post_init__(self) -> None:
        """Validate generation configuration."""
        if self.num_workers < 1:
            raise ValueError("num_workers must be >= 1")
        if self.max_attempts is not None and self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1 or None")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0 or None")


@dataclass
class GenerationMetrics:
    """Metrics collected during key generation."""

    attempts: int
    elapsed_seconds: float
    keys_per_second: float
    workers_used: int
    success: bool

    @property
    def formatted_rate(self) -> str:
        """Human-readable key generation rate."""
        if self.keys_per_second >= 1_000_000:
            return f"{self.keys_per_second / 1_000_000:.2f} M keys/sec"
        elif self.keys_per_second >= 1_000:
            return f"{self.keys_per_second / 1_000:.2f} K keys/sec"
        else:
            return f"{self.keys_per_second:.2f} keys/sec"
