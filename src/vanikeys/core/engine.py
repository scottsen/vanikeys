"""Core vanity key generation engine."""

import multiprocessing as mp
import time
from typing import Optional

from vanikeys.core.types import KeyPair, GenerationConfig, GenerationMetrics
from vanikeys.generators.base import KeyGenerator
from vanikeys.matchers.base import PatternMatcher


class VanityEngine:
    """
    Core engine for vanity key generation.

    Coordinates key generation, pattern matching, and multi-worker execution.
    """

    def __init__(self, generator: KeyGenerator, matcher: PatternMatcher):
        """
        Initialize vanity engine.

        Args:
            generator: Key generator to use
            matcher: Pattern matcher to apply
        """
        self.generator = generator
        self.matcher = matcher

    def generate(
        self,
        config: Optional[GenerationConfig] = None,
        verbose: bool = True
    ) -> tuple[KeyPair, GenerationMetrics]:
        """
        Generate a vanity key matching the pattern.

        Args:
            config: Generation configuration (workers, timeouts, etc.)
            verbose: Print progress updates

        Returns:
            Tuple of (matched KeyPair, generation metrics)

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If max_attempts exceeded
        """
        if config is None:
            # Simple single-threaded generation
            return self._generate_single_threaded(verbose)

        if config.num_workers == 1:
            return self._generate_single_threaded(verbose, config)
        else:
            return self._generate_multi_threaded(config, verbose)

    def _generate_single_threaded(
        self,
        verbose: bool = True,
        config: Optional[GenerationConfig] = None
    ) -> tuple[KeyPair, GenerationMetrics]:
        """Generate vanity key in single thread."""
        attempts = 0
        start_time = time.perf_counter()

        max_attempts = config.max_attempts if config else None
        timeout = config.timeout_seconds if config else None

        last_update = start_time
        update_interval = 1.0  # Update every second

        while True:
            # Check termination conditions
            if timeout and (time.perf_counter() - start_time) > timeout:
                raise TimeoutError(f"Timeout exceeded after {attempts:,} attempts")

            if max_attempts and attempts >= max_attempts:
                raise RuntimeError(f"Max attempts ({max_attempts:,}) exceeded")

            # Generate and test key
            keypair = self.generator.generate()
            attempts += 1

            searchable = self.generator.get_searchable_string(keypair)
            if self.matcher.matches(searchable):
                # Found a match!
                elapsed = time.perf_counter() - start_time
                metrics = GenerationMetrics(
                    attempts=attempts,
                    elapsed_seconds=elapsed,
                    keys_per_second=attempts / elapsed if elapsed > 0 else 0,
                    workers_used=1,
                    success=True
                )
                return keypair, metrics

            # Print progress update
            if verbose:
                current_time = time.perf_counter()
                if current_time - last_update >= update_interval:
                    elapsed = current_time - start_time
                    rate = attempts / elapsed if elapsed > 0 else 0
                    print(
                        f"\rAttempts: {attempts:,} | "
                        f"Rate: {rate:,.0f} keys/sec | "
                        f"Time: {elapsed:.1f}s",
                        end="",
                        flush=True
                    )
                    last_update = current_time

    def _generate_multi_threaded(
        self,
        config: GenerationConfig,
        verbose: bool = True
    ) -> tuple[KeyPair, GenerationMetrics]:
        """
        Generate vanity key using multiple workers.

        Uses multiprocessing to parallelize key generation across CPU cores.
        """
        num_workers = config.num_workers
        result_queue = mp.Queue()
        stop_event = mp.Event()

        # Start workers
        workers = []
        for worker_id in range(num_workers):
            p = mp.Process(
                target=_worker_process,
                args=(
                    self.generator,
                    self.matcher,
                    worker_id,
                    result_queue,
                    stop_event,
                    config.max_attempts,
                    config.timeout_seconds,
                )
            )
            p.start()
            workers.append(p)

        start_time = time.perf_counter()
        result = None

        try:
            # Wait for first result
            if config.timeout_seconds:
                timeout = config.timeout_seconds
            else:
                timeout = None

            result = result_queue.get(timeout=timeout)

            # Signal all workers to stop
            stop_event.set()

            # Create metrics
            elapsed = time.perf_counter() - start_time
            metrics = GenerationMetrics(
                attempts=result["attempts"],
                elapsed_seconds=elapsed,
                keys_per_second=result["attempts"] / elapsed if elapsed > 0 else 0,
                workers_used=num_workers,
                success=True
            )

            return result["keypair"], metrics

        except Exception as e:
            # Error occurred, stop all workers
            stop_event.set()
            raise e

        finally:
            # Clean up workers
            for p in workers:
                p.join(timeout=1.0)
                if p.is_alive():
                    p.terminate()


def _worker_process(
    generator: KeyGenerator,
    matcher: PatternMatcher,
    worker_id: int,
    result_queue: mp.Queue,
    stop_event: mp.Event,
    max_attempts: Optional[int],
    timeout_seconds: Optional[float],
) -> None:
    """
    Worker process for parallel key generation.

    Each worker generates keys until it finds a match or is signaled to stop.
    """
    attempts = 0
    start_time = time.perf_counter()

    while not stop_event.is_set():
        # Check termination conditions
        if timeout_seconds and (time.perf_counter() - start_time) > timeout_seconds:
            return

        if max_attempts and attempts >= max_attempts:
            return

        # Generate and test key
        keypair = generator.generate()
        attempts += 1

        searchable = generator.get_searchable_string(keypair)
        if matcher.matches(searchable):
            # Found a match! Put result in queue
            result_queue.put({
                "keypair": keypair,
                "attempts": attempts,
                "worker_id": worker_id,
            })
            return


if __name__ == "__main__":
    # Quick test
    from vanikeys.generators.ed25519 import Ed25519DIDGenerator
    from vanikeys.matchers.simple import ContainsMatcher

    print("Testing VanityEngine with DID generation...")
    print("Looking for DID containing 'ABC' (case-insensitive)\n")

    generator = Ed25519DIDGenerator()
    matcher = ContainsMatcher("ABC", case_sensitive=False)

    engine = VanityEngine(generator, matcher)

    keypair, metrics = engine.generate()

    print(f"\n\n✅ Found matching key!")
    print(f"DID: {keypair.address}")
    print(f"\nMetrics:")
    print(f"  Attempts: {metrics.attempts:,}")
    print(f"  Time: {metrics.elapsed_seconds:.2f}s")
    print(f"  Rate: {metrics.formatted_rate}")
