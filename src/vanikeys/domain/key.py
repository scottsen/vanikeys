"""
Domain model for generated vanity keys.

Represents a cryptographic key (Ed25519) and its DID representation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VanityKey:
    """
    A generated vanity key with its cryptographic components.

    Example:
        VanityKey(
            did="did:key:z6MkGO1BEAWESOMEkey123...",
            public_key="public_key_bytes_hex",
            private_key="private_key_bytes_hex",
            matched_pattern="GO BE AWE SOME",
            generation_time=0.45,
            attempts=42000
        )
    """

    # DID and key material
    did: str                    # Full DID key (e.g., "did:key:z6Mk...")
    public_key: str             # Hex-encoded public key
    private_key: Optional[str]  # Hex-encoded private key (sensitive!)

    # Match information
    matched_pattern: str        # The pattern that was matched
    # For multi-substring: [(10, 12), (15, 17), ...]
    match_positions: Optional[list] = None

    # Generation metadata
    generation_time: float = 0.0  # Seconds taken to generate
    attempts: int = 0               # Number of keys tried before match
    worker_id: Optional[str] = None  # Which worker generated this

    # Database fields
    id: Optional[str] = None
    pull_id: Optional[str] = None  # Which pull this key belongs to
    created_at: Optional[str] = None

    @property
    def did_suffix(self) -> str:
        """
        Extract the human-readable suffix from the DID.

        Example: "did:key:z6MkGOBEAWESOME123..." -> "GOBEAWESOME123..."
        """
        if not self.did.startswith("did:key:z6Mk"):
            return self.did
        # Skip "did:key:z6Mk" prefix (12 chars)
        return self.did[12:]

    @property
    def is_match_quality_excellent(self) -> bool:
        """
        Is this a high-quality match?

        In gacha mode, this affects the rarity tier
        (common/uncommon/rare/epic/legendary).
        """
        # For now, simple heuristic: short patterns with exact matches
        return len(self.matched_pattern.replace(" ", "")) >= 8

    @property
    def abbreviated_did(self) -> str:
        """
        Short version for display: "did:key:z6Mk...SOME123"

        Shows the matched portion clearly.
        """
        if len(self.did) <= 30:
            return self.did
        return f"{self.did[:16]}...{self.did[-10:]}"

    def to_dict(self, include_private_key: bool = False) -> dict:
        """
        Convert to dictionary for serialization.

        Args:
            include_private_key: If False, omits private key (for public display)
        """
        data = {
            "id": self.id,
            "did": self.did,
            "public_key": self.public_key,
            "matched_pattern": self.matched_pattern,
            "match_positions": self.match_positions,
            "generation_time": self.generation_time,
            "attempts": self.attempts,
            "worker_id": self.worker_id,
            "pull_id": self.pull_id,
            "created_at": self.created_at,
        }

        if include_private_key:
            data["private_key"] = self.private_key

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "VanityKey":
        """Create from dictionary."""
        return cls(
            did=data["did"],
            public_key=data["public_key"],
            private_key=data.get("private_key"),
            matched_pattern=data["matched_pattern"],
            match_positions=data.get("match_positions"),
            generation_time=data.get("generation_time", 0.0),
            attempts=data.get("attempts", 0),
            worker_id=data.get("worker_id"),
            id=data.get("id"),
            pull_id=data.get("pull_id"),
            created_at=data.get("created_at"),
        )
