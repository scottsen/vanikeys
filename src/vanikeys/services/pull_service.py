"""
Pull service - Orchestrates VaniPull gacha mechanics and guaranteed jobs.

Business logic for:
- Creating gacha pulls
- Submitting guaranteed jobs
- Determining rarity tiers
- Managing pull lifecycle
"""

from typing import Optional, List
import asyncio
from datetime import datetime

from ..domain import (
    Pattern,
    Pull,
    PullMode,
    PullStatus,
    RarityTier,
    VanityKey,
)
from ..core import ProbabilityCalculator


class PullService:
    """
    Service for managing VaniPulls (gacha and guaranteed).

    Responsibilities:
    - Create gacha pulls (instant single attempt)
    - Submit guaranteed jobs (grind until match)
    - Determine rarity tiers based on match quality
    - Update pull status and progress
    - Calculate costs

    Dependencies:
    - PullRepository (data access)
    - KeyRepository (data access)
    - TokenService (deduct tokens)
    - WorkerClient (submit GPU jobs)
    """

    def __init__(
        self,
        pull_repo=None,
        key_repo=None,
        token_service=None,
        worker_client=None,
    ):
        """
        Initialize service.

        Args:
            pull_repo: PullRepository instance
            key_repo: KeyRepository instance
            token_service: TokenService instance
            worker_client: WorkerClient for GPU job submission
        """
        self.pull_repo = pull_repo
        self.key_repo = key_repo
        self.token_service = token_service
        self.worker_client = worker_client
        self.prob_calculator = ProbabilityCalculator()

    async def create_gacha_pull(
        self,
        user_id: str,
        pattern: Pattern,
    ) -> Pull:
        """
        Create a gacha pull (single random attempt).

        Flow:
        1. Calculate cost
        2. Deduct tokens from user
        3. Create pull record
        4. Submit to GPU worker (RunPod Serverless)
        5. Return pull (status: pending)

        Args:
            user_id: User ID
            pattern: Pattern to match

        Returns:
            Created Pull instance

        Raises:
            ValueError: If user has insufficient tokens
            RuntimeError: If worker submission fails
        """
        # Calculate cost
        prob_result = self.prob_calculator.calculate(pattern)
        cost_tokens = prob_result["cost_tokens"]

        # Check user can afford
        can_afford = await self.token_service.can_afford(user_id, cost_tokens)
        if not can_afford:
            raise ValueError(f"Insufficient tokens. Need {cost_tokens}, user has less.")

        # Deduct tokens
        await self.token_service.spend_tokens(
            user_id=user_id,
            amount=cost_tokens,
            description=f"Gacha pull: {pattern.pattern_string}",
            pull_id=None,  # Will be set after pull is created
        )

        # Create pull record
        pull = Pull(
            user_id=user_id,
            pattern_id=pattern.id,
            mode=PullMode.GACHA,
            status=PullStatus.PENDING,
            cost_tokens=cost_tokens,
        )

        # Save to database
        pull = await self.pull_repo.create(pull)

        # Submit to GPU worker (async, non-blocking)
        await self._submit_gacha_job(pull, pattern)

        return pull

    async def create_guaranteed_job(
        self,
        user_id: str,
        pattern: Pattern,
    ) -> Pull:
        """
        Create a guaranteed job (grind until exact match).

        Flow:
        1. Calculate cost (USD)
        2. Process Stripe payment
        3. Create pull record
        4. Submit to Modal GPU (long-running)
        5. Return pull (status: pending)

        Args:
            user_id: User ID
            pattern: Pattern to match

        Returns:
            Created Pull instance

        Raises:
            ValueError: If payment fails
            RuntimeError: If worker submission fails
        """
        # Calculate cost
        prob_result = self.prob_calculator.calculate(pattern)
        cost_usd = prob_result["cost_guaranteed_usd"]

        # Process Stripe payment (implementation depends on Stripe integration)
        # For now, assume payment succeeds
        # TODO: Integrate Stripe payment processing

        # Create pull record
        pull = Pull(
            user_id=user_id,
            pattern_id=pattern.id,
            mode=PullMode.GUARANTEED,
            status=PullStatus.PENDING,
            cost_usd=cost_usd,
            progress=0.0,
        )

        # Save to database
        pull = await self.pull_repo.create(pull)

        # Submit to Modal GPU worker (long-running with checkpointing)
        await self._submit_guaranteed_job(pull, pattern)

        return pull

    async def _submit_gacha_job(self, pull: Pull, pattern: Pattern):
        """
        Submit gacha pull to RunPod Serverless GPU.

        Non-blocking: job runs async, webhook notifies on completion.

        Args:
            pull: Pull instance
            pattern: Pattern to match
        """
        if not self.worker_client:
            # For testing: simulate instant result
            await self._simulate_gacha_result(pull, pattern)
            return

        # Submit to RunPod Serverless
        job_id = await self.worker_client.submit_gacha(
            pull_id=pull.id,
            pattern=pattern,
            webhook_url=f"/api/webhooks/gacha/{pull.id}",
        )

        # Update pull with worker ID
        pull.worker_id = job_id
        pull.status = PullStatus.RUNNING
        await self.pull_repo.update(pull)

    async def _submit_guaranteed_job(self, pull: Pull, pattern: Pattern):
        """
        Submit guaranteed job to Modal GPU.

        Long-running job with progress updates and checkpointing.

        Args:
            pull: Pull instance
            pattern: Pattern to match
        """
        if not self.worker_client:
            # For testing: simulate instant result
            await self._simulate_guaranteed_result(pull, pattern)
            return

        # Submit to Modal GPU
        job_id = await self.worker_client.submit_guaranteed(
            pull_id=pull.id,
            pattern=pattern,
            progress_webhook_url=f"/api/webhooks/progress/{pull.id}",
            completion_webhook_url=f"/api/webhooks/guaranteed/{pull.id}",
        )

        # Update pull with worker ID
        pull.worker_id = job_id
        pull.status = PullStatus.RUNNING
        await self.pull_repo.update(pull)

    async def handle_gacha_result(
        self,
        pull_id: str,
        key: Optional[VanityKey],
        error: Optional[str] = None,
    ):
        """
        Handle gacha pull result from worker.

        Called by webhook when GPU worker completes.

        Args:
            pull_id: Pull ID
            key: Generated key (if successful)
            error: Error message (if failed)
        """
        pull = await self.pull_repo.get_by_id(pull_id)
        if not pull:
            raise ValueError(f"Pull not found: {pull_id}")

        if error:
            # Pull failed
            pull.status = PullStatus.FAILED
            pull.error_message = error
            pull.completed_at = datetime.utcnow().isoformat()
            await self.pull_repo.update(pull)

            # Refund tokens
            await self.token_service.refund_tokens(
                user_id=pull.user_id,
                amount=pull.cost_tokens,
                description=f"Refund for failed pull: {pull_id}",
                pull_id=pull.id,
            )
            return

        if not key:
            raise ValueError("Key is required for successful pull")

        # Save key
        key.pull_id = pull.id
        saved_key = await self.key_repo.create(key)

        # Determine rarity tier
        rarity = self._determine_rarity(key, pull)

        # Update pull
        pull.status = PullStatus.SUCCESS
        pull.key_id = saved_key.id
        pull.rarity = rarity
        pull.generation_time = key.generation_time
        pull.attempts = key.attempts
        pull.completed_at = datetime.utcnow().isoformat()
        await self.pull_repo.update(pull)

    async def handle_guaranteed_result(
        self,
        pull_id: str,
        key: Optional[VanityKey],
        error: Optional[str] = None,
    ):
        """
        Handle guaranteed job result from worker.

        Called by webhook when Modal GPU worker completes.

        Args:
            pull_id: Pull ID
            key: Generated key (guaranteed exact match)
            error: Error message (if failed)
        """
        pull = await self.pull_repo.get_by_id(pull_id)
        if not pull:
            raise ValueError(f"Pull not found: {pull_id}")

        if error:
            # Job failed
            pull.status = PullStatus.FAILED
            pull.error_message = error
            pull.completed_at = datetime.utcnow().isoformat()
            await self.pull_repo.update(pull)

            # TODO: Process Stripe refund
            return

        if not key:
            raise ValueError("Key is required for successful job")

        # Save key
        key.pull_id = pull.id
        saved_key = await self.key_repo.create(key)

        # Update pull
        pull.status = PullStatus.SUCCESS
        pull.key_id = saved_key.id
        pull.progress = 1.0
        pull.generation_time = key.generation_time
        pull.attempts = key.attempts
        pull.completed_at = datetime.utcnow().isoformat()
        await self.pull_repo.update(pull)

    async def update_guaranteed_progress(
        self,
        pull_id: str,
        progress: float,
        estimated_completion: Optional[str] = None,
    ):
        """
        Update guaranteed job progress.

        Called by webhook during job execution.

        Args:
            pull_id: Pull ID
            progress: Progress (0.0 to 1.0)
            estimated_completion: ISO timestamp of estimated completion
        """
        pull = await self.pull_repo.get_by_id(pull_id)
        if not pull:
            raise ValueError(f"Pull not found: {pull_id}")

        pull.progress = progress
        if estimated_completion:
            pull.estimated_completion = estimated_completion
        await self.pull_repo.update(pull)

    def _determine_rarity(self, key: VanityKey, pull: Pull) -> RarityTier:
        """
        Determine rarity tier based on match quality.

        Factors:
        - Pattern length
        - Match quality (exact vs fuzzy)
        - Number of substrings
        - Difficulty score

        Args:
            key: Generated key
            pull: Pull instance

        Returns:
            RarityTier
        """
        # Simple heuristic for now
        # TODO: Refine based on actual difficulty and match quality

        pattern_length = len(key.matched_pattern.replace(" ", ""))

        if pattern_length <= 3:
            return RarityTier.COMMON
        elif pattern_length <= 5:
            return RarityTier.UNCOMMON
        elif pattern_length <= 7:
            return RarityTier.RARE
        elif pattern_length <= 10:
            return RarityTier.EPIC
        else:
            return RarityTier.LEGENDARY

    async def _simulate_gacha_result(self, pull: Pull, pattern: Pattern):
        """
        Simulate gacha result for testing (no GPU worker).

        Generates a fake key after short delay.

        Args:
            pull: Pull instance
            pattern: Pattern to match
        """
        # Simulate short delay
        await asyncio.sleep(0.5)

        # Create fake key
        key = VanityKey(
            did=f"did:key:z6Mk{pattern.pattern_string.replace(' ', '')}xyzABC123",
            public_key="fake_public_key_hex",
            private_key="fake_private_key_hex",
            matched_pattern=pattern.pattern_string,
            generation_time=0.45,
            attempts=12000,
        )

        # Process result
        await self.handle_gacha_result(pull.id, key)

    async def _simulate_guaranteed_result(self, pull: Pull, pattern: Pattern):
        """
        Simulate guaranteed result for testing (no GPU worker).

        Args:
            pull: Pull instance
            pattern: Pattern to match
        """
        # Simulate longer delay with progress updates
        for progress in [0.2, 0.4, 0.6, 0.8]:
            await asyncio.sleep(0.5)
            await self.update_guaranteed_progress(pull.id, progress)

        # Create fake key
        key = VanityKey(
            did=f"did:key:z6Mk{pattern.pattern_string.replace(' ', '')}EXACT",
            public_key="fake_public_key_hex",
            private_key="fake_private_key_hex",
            matched_pattern=pattern.pattern_string,
            generation_time=2.1,
            attempts=54000,
        )

        # Process result
        await self.handle_guaranteed_result(pull.id, key)
