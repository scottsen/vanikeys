"""
Domain model for VaniPulls (gacha pulls and guaranteed jobs).

Represents a single pull attempt or guaranteed generation job.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class PullMode(Enum):
    """Type of pull."""
    GACHA = "gacha"           # Single random attempt
    GUARANTEED = "guaranteed"  # Grind until exact match


class PullStatus(Enum):
    """Status of pull/job."""
    PENDING = "pending"       # Queued, not started
    RUNNING = "running"       # Currently generating
    SUCCESS = "success"       # Match found!
    FAILED = "failed"         # Error occurred
    CANCELLED = "cancelled"   # User cancelled


class RarityTier(Enum):
    """
    Rarity tier for gacha pulls.

    Based on match quality:
    - COMMON: Basic match
    - UNCOMMON: Good match with some pattern
    - RARE: Excellent match, full pattern
    - EPIC: Rare pattern with fuzzy matches
    - LEGENDARY: Near-perfect match (e.g., all substrings exact)
    """
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Pull:
    """
    A single VaniPull (gacha) or guaranteed generation job.

    Examples:
        # Gacha pull
        Pull(
            user_id="user123",
            pattern_id="pattern456",
            mode=PullMode.GACHA,
            cost_tokens=100,
            status=PullStatus.SUCCESS,
            key_id="key789",
            rarity=RarityTier.RARE
        )

        # Guaranteed job
        Pull(
            user_id="user123",
            pattern_id="pattern456",
            mode=PullMode.GUARANTEED,
            cost_usd=45.0,
            status=PullStatus.RUNNING,
            progress=0.35  # 35% complete
        )
    """

    # Core pull data
    user_id: str
    pattern_id: str
    mode: PullMode

    # Status
    status: PullStatus = PullStatus.PENDING

    # Gacha mode
    cost_tokens: Optional[int] = None
    rarity: Optional[RarityTier] = None

    # Guaranteed mode
    cost_usd: Optional[float] = None
    progress: float = 0.0  # 0.0 to 1.0
    estimated_completion: Optional[str] = None  # ISO timestamp

    # Result
    key_id: Optional[str] = None  # Generated key (if success)
    keys: List[str] = field(default_factory=list)  # For multi-key results

    # Performance metadata
    generation_time: float = 0.0  # Total seconds
    attempts: int = 0              # Total keys tried
    worker_id: Optional[str] = None

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0

    # Database fields
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def is_gacha(self) -> bool:
        """Is this a gacha pull?"""
        return self.mode == PullMode.GACHA

    @property
    def is_guaranteed(self) -> bool:
        """Is this a guaranteed job?"""
        return self.mode == PullMode.GUARANTEED

    @property
    def is_complete(self) -> bool:
        """Is the pull finished (success, failed, or cancelled)?"""
        return self.status in [
            PullStatus.SUCCESS, PullStatus.FAILED, PullStatus.CANCELLED
        ]

    @property
    def is_running(self) -> bool:
        """Is the pull currently generating?"""
        return self.status in [PullStatus.PENDING, PullStatus.RUNNING]

    @property
    def cost_display(self) -> str:
        """Human-readable cost string."""
        if self.is_gacha and self.cost_tokens:
            return f"{self.cost_tokens} VaniTokens"
        if self.is_guaranteed and self.cost_usd:
            return f"${self.cost_usd:.2f}"
        return "Unknown"

    @property
    def rarity_emoji(self) -> str:
        """Emoji for rarity tier."""
        if not self.rarity:
            return "❓"
        return {
            RarityTier.COMMON: "⚪",
            RarityTier.UNCOMMON: "🟢",
            RarityTier.RARE: "🔵",
            RarityTier.EPIC: "🟣",
            RarityTier.LEGENDARY: "🟡",
        }.get(self.rarity, "❓")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pattern_id": self.pattern_id,
            "mode": self.mode.value,
            "status": self.status.value,
            "cost_tokens": self.cost_tokens,
            "cost_usd": self.cost_usd,
            "rarity": self.rarity.value if self.rarity else None,
            "progress": self.progress,
            "estimated_completion": self.estimated_completion,
            "key_id": self.key_id,
            "keys": self.keys,
            "generation_time": self.generation_time,
            "attempts": self.attempts,
            "worker_id": self.worker_id,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pull":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            pattern_id=data["pattern_id"],
            mode=PullMode(data["mode"]),
            status=PullStatus(data["status"]),
            cost_tokens=data.get("cost_tokens"),
            cost_usd=data.get("cost_usd"),
            rarity=RarityTier(data["rarity"]) if data.get("rarity") else None,
            progress=data.get("progress", 0.0),
            estimated_completion=data.get("estimated_completion"),
            key_id=data.get("key_id"),
            keys=data.get("keys", []),
            generation_time=data.get("generation_time", 0.0),
            attempts=data.get("attempts", 0),
            worker_id=data.get("worker_id"),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            completed_at=data.get("completed_at"),
        )
