"""
Domain models for VaniToken economy (token balances, transactions, purchases).

VaniTokens are the in-app currency used for gacha pulls.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    """Type of token transaction."""
    PURCHASE = "purchase"      # User bought tokens with USD
    SPEND = "spend"           # User spent tokens on a pull
    REFUND = "refund"         # Refund for failed pull
    ADMIN_GRANT = "admin"     # Admin granted tokens
    BONUS = "bonus"           # Bonus tokens (first purchase, etc.)


class PaymentStatus(Enum):
    """Payment status for purchases."""
    PENDING = "pending"       # Payment initiated
    COMPLETED = "completed"   # Payment successful
    FAILED = "failed"         # Payment failed
    REFUNDED = "refunded"     # Payment refunded


@dataclass
class TokenBalance:
    """
    User's VaniToken balance.

    Simple model tracking current balance and lifetime stats.
    """

    user_id: str
    balance: int = 0                    # Current token balance
    lifetime_purchased: int = 0         # Total tokens ever purchased
    lifetime_spent: int = 0             # Total tokens ever spent
    lifetime_usd_spent: float = 0.0     # Total USD spent on tokens

    # Database fields
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def can_afford(self, cost: int) -> bool:
        """Can the user afford this cost?"""
        return self.balance >= cost

    @property
    def total_pulls(self) -> int:
        """Estimate total pulls (assuming avg 100 tokens per pull)."""
        return self.lifetime_spent // 100

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": self.balance,
            "lifetime_purchased": self.lifetime_purchased,
            "lifetime_spent": self.lifetime_spent,
            "lifetime_usd_spent": self.lifetime_usd_spent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenBalance":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            balance=data.get("balance", 0),
            lifetime_purchased=data.get("lifetime_purchased", 0),
            lifetime_spent=data.get("lifetime_spent", 0),
            lifetime_usd_spent=data.get("lifetime_usd_spent", 0.0),
            id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class TokenTransaction:
    """
    A single token transaction (purchase, spend, refund, etc.).

    This is the immutable audit log of all token movements.
    """

    user_id: str
    type: TransactionType
    amount: int  # Positive for credits, negative for debits

    # Context
    description: str  # Human-readable description
    pull_id: Optional[str] = None  # If related to a pull
    purchase_id: Optional[str] = None  # If related to a purchase

    # Balance tracking
    balance_before: int = 0
    balance_after: int = 0

    # Database fields
    id: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def is_credit(self) -> bool:
        """Does this transaction add tokens?"""
        return self.amount > 0

    @property
    def is_debit(self) -> bool:
        """Does this transaction remove tokens?"""
        return self.amount < 0

    @property
    def amount_display(self) -> str:
        """Human-readable amount with sign."""
        if self.is_credit:
            return f"+{self.amount}"
        return str(self.amount)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "amount": self.amount,
            "description": self.description,
            "pull_id": self.pull_id,
            "purchase_id": self.purchase_id,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenTransaction":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            type=TransactionType(data["type"]),
            amount=data["amount"],
            description=data["description"],
            pull_id=data.get("pull_id"),
            purchase_id=data.get("purchase_id"),
            balance_before=data.get("balance_before", 0),
            balance_after=data.get("balance_after", 0),
            id=data.get("id"),
            created_at=data.get("created_at"),
        )


@dataclass
class TokenPurchase:
    """
    A token purchase transaction (user buying tokens with USD via Stripe).

    This tracks the payment flow and token delivery.
    """

    user_id: str
    tokens: int           # How many tokens purchased
    usd_amount: float     # How much USD paid
    bonus_tokens: int = 0  # Bonus tokens from bundle

    # Payment provider (Stripe)
    stripe_payment_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    # Status
    status: PaymentStatus = PaymentStatus.PENDING

    # Fulfillment
    tokens_delivered: bool = False
    transaction_id: Optional[str] = None  # TokenTransaction.id

    # Metadata
    bundle_name: Optional[str] = None  # e.g., "500 Token Bundle (+20% bonus)"
    error_message: Optional[str] = None

    # Database fields
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        """Total tokens including bonus."""
        return self.tokens + self.bonus_tokens

    @property
    def is_complete(self) -> bool:
        """Is the purchase complete and tokens delivered?"""
        return self.status == PaymentStatus.COMPLETED and self.tokens_delivered

    @property
    def effective_price_per_token(self) -> float:
        """Price per token after bonus (cents)."""
        if self.total_tokens == 0:
            return 0.0
        return (self.usd_amount * 100) / self.total_tokens

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tokens": self.tokens,
            "usd_amount": self.usd_amount,
            "bonus_tokens": self.bonus_tokens,
            "stripe_payment_id": self.stripe_payment_id,
            "stripe_customer_id": self.stripe_customer_id,
            "status": self.status.value,
            "tokens_delivered": self.tokens_delivered,
            "transaction_id": self.transaction_id,
            "bundle_name": self.bundle_name,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenPurchase":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            tokens=data["tokens"],
            usd_amount=data["usd_amount"],
            bonus_tokens=data.get("bonus_tokens", 0),
            stripe_payment_id=data.get("stripe_payment_id"),
            stripe_customer_id=data.get("stripe_customer_id"),
            status=PaymentStatus(data["status"]),
            tokens_delivered=data.get("tokens_delivered", False),
            transaction_id=data.get("transaction_id"),
            bundle_name=data.get("bundle_name"),
            error_message=data.get("error_message"),
            id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            completed_at=data.get("completed_at"),
        )
