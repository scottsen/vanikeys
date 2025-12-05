"""
Token service - VaniToken economy management.

Business logic for:
- Token purchases (Stripe integration)
- Token spending (gacha pulls)
- Token refunds (failed pulls)
- Balance management
- Transaction history
"""

from typing import Optional, List
from datetime import datetime

from ..domain import (
    TokenBalance,
    TokenTransaction,
    TokenPurchase,
    TransactionType,
    PaymentStatus,
)


class TokenService:
    """
    Service for managing VaniToken economy.

    Responsibilities:
    - Process token purchases via Stripe
    - Deduct tokens for pulls
    - Refund tokens for failed pulls
    - Track transaction history
    - Manage token balances

    Dependencies:
    - TokenBalanceRepository (data access)
    - TokenTransactionRepository (data access)
    - TokenPurchaseRepository (data access)
    - StripeClient (payment processing)
    """

    # Token bundle pricing (tokens, USD, bonus)
    BUNDLES = {
        "starter": {"tokens": 100, "usd": 5.0, "bonus": 0},
        "basic": {"tokens": 500, "usd": 20.0, "bonus": 100},  # 20% bonus
        "pro": {"tokens": 2000, "usd": 70.0, "bonus": 600},   # 30% bonus
        "whale": {"tokens": 10000, "usd": 300.0, "bonus": 4000},  # 40% bonus
    }

    def __init__(
        self,
        balance_repo=None,
        transaction_repo=None,
        purchase_repo=None,
        stripe_client=None,
    ):
        """
        Initialize service.

        Args:
            balance_repo: TokenBalanceRepository instance
            transaction_repo: TokenTransactionRepository instance
            purchase_repo: TokenPurchaseRepository instance
            stripe_client: StripeClient for payment processing
        """
        self.balance_repo = balance_repo
        self.transaction_repo = transaction_repo
        self.purchase_repo = purchase_repo
        self.stripe_client = stripe_client

    async def get_balance(self, user_id: str) -> TokenBalance:
        """
        Get user's token balance.

        Creates balance record if it doesn't exist.

        Args:
            user_id: User ID

        Returns:
            TokenBalance instance
        """
        balance = await self.balance_repo.get_by_user_id(user_id)
        if not balance:
            # Create new balance
            balance = TokenBalance(user_id=user_id)
            balance = await self.balance_repo.create(balance)
        return balance

    async def can_afford(self, user_id: str, cost: int) -> bool:
        """
        Check if user can afford a cost.

        Args:
            user_id: User ID
            cost: Token cost

        Returns:
            True if user has sufficient balance
        """
        balance = await self.get_balance(user_id)
        return balance.can_afford(cost)

    async def purchase_tokens(
        self,
        user_id: str,
        bundle_name: str,
        stripe_payment_id: str,
        stripe_customer_id: Optional[str] = None,
    ) -> TokenPurchase:
        """
        Purchase tokens via Stripe.

        Flow:
        1. Validate bundle
        2. Create purchase record
        3. Process Stripe payment
        4. Deliver tokens (create transaction)
        5. Update purchase status

        Args:
            user_id: User ID
            bundle_name: Bundle name (e.g., "basic", "pro")
            stripe_payment_id: Stripe payment intent ID
            stripe_customer_id: Stripe customer ID (optional)

        Returns:
            TokenPurchase instance

        Raises:
            ValueError: If bundle is invalid
            RuntimeError: If payment fails
        """
        # Validate bundle
        if bundle_name not in self.BUNDLES:
            raise ValueError(f"Invalid bundle: {bundle_name}")

        bundle = self.BUNDLES[bundle_name]

        # Create purchase record
        purchase = TokenPurchase(
            user_id=user_id,
            tokens=bundle["tokens"],
            bonus_tokens=bundle["bonus"],
            usd_amount=bundle["usd"],
            bundle_name=bundle_name,
            stripe_payment_id=stripe_payment_id,
            stripe_customer_id=stripe_customer_id,
            status=PaymentStatus.PENDING,
        )
        purchase = await self.purchase_repo.create(purchase)

        try:
            # Process Stripe payment (implementation depends on Stripe SDK)
            # For now, assume payment succeeds
            # TODO: Integrate actual Stripe payment processing
            payment_success = True

            if not payment_success:
                raise RuntimeError("Stripe payment failed")

            # Deliver tokens
            total_tokens = purchase.total_tokens
            transaction = await self.add_tokens(
                user_id=user_id,
                amount=total_tokens,
                description=f"Purchased {bundle_name} bundle ({total_tokens} tokens)",
                purchase_id=purchase.id,
            )

            # Update purchase
            purchase.status = PaymentStatus.COMPLETED
            purchase.tokens_delivered = True
            purchase.transaction_id = transaction.id
            purchase.completed_at = datetime.utcnow().isoformat()
            await self.purchase_repo.update(purchase)

            return purchase

        except Exception as e:
            # Payment failed
            purchase.status = PaymentStatus.FAILED
            purchase.error_message = str(e)
            await self.purchase_repo.update(purchase)
            raise

    async def add_tokens(
        self,
        user_id: str,
        amount: int,
        description: str,
        purchase_id: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Add tokens to user's balance.

        Args:
            user_id: User ID
            amount: Tokens to add
            description: Transaction description
            purchase_id: Related purchase ID (optional)

        Returns:
            TokenTransaction instance
        """
        # Get current balance
        balance = await self.get_balance(user_id)

        # Create transaction
        transaction_type = (
            TransactionType.PURCHASE
            if purchase_id
            else TransactionType.ADMIN_GRANT
        )
        transaction = TokenTransaction(
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            description=description,
            purchase_id=purchase_id,
            balance_before=balance.balance,
            balance_after=balance.balance + amount,
        )
        transaction = await self.transaction_repo.create(transaction)

        # Update balance
        balance.balance += amount
        balance.lifetime_purchased += amount
        await self.balance_repo.update(balance)

        return transaction

    async def spend_tokens(
        self,
        user_id: str,
        amount: int,
        description: str,
        pull_id: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Spend tokens from user's balance.

        Args:
            user_id: User ID
            amount: Tokens to spend
            description: Transaction description
            pull_id: Related pull ID (optional)

        Returns:
            TokenTransaction instance

        Raises:
            ValueError: If user has insufficient balance
        """
        # Get current balance
        balance = await self.get_balance(user_id)

        # Check sufficient balance
        if not balance.can_afford(amount):
            raise ValueError(
                f"Insufficient balance. Need {amount}, have {balance.balance}"
            )

        # Create transaction
        transaction = TokenTransaction(
            user_id=user_id,
            type=TransactionType.SPEND,
            amount=-amount,  # Negative for debit
            description=description,
            pull_id=pull_id,
            balance_before=balance.balance,
            balance_after=balance.balance - amount,
        )
        transaction = await self.transaction_repo.create(transaction)

        # Update balance
        balance.balance -= amount
        balance.lifetime_spent += amount
        await self.balance_repo.update(balance)

        return transaction

    async def refund_tokens(
        self,
        user_id: str,
        amount: int,
        description: str,
        pull_id: Optional[str] = None,
    ) -> TokenTransaction:
        """
        Refund tokens to user's balance.

        Used for failed pulls or cancelled operations.

        Args:
            user_id: User ID
            amount: Tokens to refund
            description: Transaction description
            pull_id: Related pull ID (optional)

        Returns:
            TokenTransaction instance
        """
        # Get current balance
        balance = await self.get_balance(user_id)

        # Create transaction
        transaction = TokenTransaction(
            user_id=user_id,
            type=TransactionType.REFUND,
            amount=amount,  # Positive for credit
            description=description,
            pull_id=pull_id,
            balance_before=balance.balance,
            balance_after=balance.balance + amount,
        )
        transaction = await self.transaction_repo.create(transaction)

        # Update balance (don't count refund as "purchased")
        balance.balance += amount
        await self.balance_repo.update(balance)

        return transaction

    async def grant_bonus_tokens(
        self,
        user_id: str,
        amount: int,
        reason: str,
    ) -> TokenTransaction:
        """
        Grant bonus tokens (admin action or promotion).

        Args:
            user_id: User ID
            amount: Tokens to grant
            reason: Reason for bonus

        Returns:
            TokenTransaction instance
        """
        # Get current balance
        balance = await self.get_balance(user_id)

        # Create transaction
        transaction = TokenTransaction(
            user_id=user_id,
            type=TransactionType.BONUS,
            amount=amount,
            description=f"Bonus: {reason}",
            balance_before=balance.balance,
            balance_after=balance.balance + amount,
        )
        transaction = await self.transaction_repo.create(transaction)

        # Update balance
        balance.balance += amount
        # Don't count bonus as "purchased"
        await self.balance_repo.update(balance)

        return transaction

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TokenTransaction]:
        """
        Get user's transaction history.

        Args:
            user_id: User ID
            limit: Maximum number of transactions to return
            offset: Offset for pagination

        Returns:
            List of TokenTransaction instances
        """
        return await self.transaction_repo.get_by_user_id(
            user_id, limit=limit, offset=offset
        )

    async def get_purchase_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TokenPurchase]:
        """
        Get user's purchase history.

        Args:
            user_id: User ID
            limit: Maximum number of purchases to return
            offset: Offset for pagination

        Returns:
            List of TokenPurchase instances
        """
        return await self.purchase_repo.get_by_user_id(
            user_id, limit=limit, offset=offset
        )

    @classmethod
    def get_bundle_info(cls, bundle_name: str) -> dict:
        """
        Get information about a token bundle.

        Args:
            bundle_name: Bundle name

        Returns:
            Bundle info dictionary

        Raises:
            ValueError: If bundle doesn't exist
        """
        if bundle_name not in cls.BUNDLES:
            raise ValueError(f"Invalid bundle: {bundle_name}")
        return cls.BUNDLES[bundle_name]

    @classmethod
    def list_bundles(cls) -> dict:
        """
        List all available token bundles.

        Returns:
            Dictionary of bundle info
        """
        return cls.BUNDLES.copy()
