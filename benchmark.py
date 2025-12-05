#!/usr/bin/env python3
"""
VaniKeys Performance Benchmark

Measures key generation and pattern matching performance.
Useful for validating performance claims in documentation.
"""

import time
from vanikeys.crypto.derivation import (
    generate_master_seed,
    seed_to_root_keypair,
    derive_child_keypair,
)
from vanikeys.crypto.fingerprint import compute_ssh_fingerprint
from vanikeys.crypto.matching import create_pattern_matcher


def benchmark_key_generation(iterations: int = 10000) -> dict:
    """
    Benchmark raw key generation speed.

    Args:
        iterations: Number of keys to generate

    Returns:
        Dict with performance metrics
    """
    seed = generate_master_seed()
    root_private, root_public = seed_to_root_keypair(seed)

    start = time.perf_counter()

    for i in range(iterations):
        child_private, child_public = derive_child_keypair(seed, i)
        fingerprint = compute_ssh_fingerprint(child_public)

    elapsed = time.perf_counter() - start
    keys_per_second = iterations / elapsed

    return {
        "iterations": iterations,
        "elapsed_seconds": elapsed,
        "keys_per_second": int(keys_per_second),
        "ms_per_key": (elapsed / iterations) * 1000,
    }


def benchmark_pattern_search(pattern: str, max_attempts: int = 100000) -> dict:
    """
    Benchmark pattern search (simple substring).

    Args:
        pattern: Pattern to search for
        max_attempts: Maximum keys to try

    Returns:
        Dict with search results
    """
    seed = generate_master_seed()
    matcher = create_pattern_matcher(pattern, case_sensitive=False)

    start = time.perf_counter()
    attempts = 0
    found_path = None

    for i in range(max_attempts):
        attempts += 1
        child_private, child_public = derive_child_keypair(seed, i)
        fingerprint = compute_ssh_fingerprint(child_public)

        if matcher(fingerprint):
            found_path = i
            break

    elapsed = time.perf_counter() - start

    return {
        "pattern": pattern,
        "found": found_path is not None,
        "found_path": found_path,
        "attempts": attempts,
        "elapsed_seconds": elapsed,
        "keys_per_second": int(attempts / elapsed) if elapsed > 0 else 0,
    }


def run_benchmarks():
    """Run all benchmarks and display results."""
    print("VaniKeys Performance Benchmark")
    print("=" * 60)
    print()

    # Raw key generation speed
    print("1. Raw Key Generation Speed")
    print("-" * 60)
    result = benchmark_key_generation(iterations=10000)
    print(f"   Generated {result['iterations']:,} keys")
    print(f"   Time: {result['elapsed_seconds']:.2f} seconds")
    print(f"   Speed: {result['keys_per_second']:,} keys/second")
    print(f"   Per-key: {result['ms_per_key']:.3f} ms")
    print()

    # Pattern searches (increasing difficulty)
    patterns = [
        ("a", "Very easy (1 char)"),
        ("lab", "Easy (3 chars)"),
        ("alice", "Medium (5 chars)"),
    ]

    print("2. Pattern Search Performance")
    print("-" * 60)

    for pattern, description in patterns:
        print(f"   Pattern: '{pattern}' - {description}")
        result = benchmark_pattern_search(pattern, max_attempts=100000)

        if result["found"]:
            print(f"      ✓ FOUND at path {result['found_path']}")
            print(f"      Attempts: {result['attempts']:,}")
            print(f"      Time: {result['elapsed_seconds']:.3f} seconds")
            print(f"      Speed: {result['keys_per_second']:,} keys/second")
        else:
            print(f"      ✗ NOT FOUND in {result['attempts']:,} attempts")
            print(f"      Time: {result['elapsed_seconds']:.3f} seconds")

        print()

    print("=" * 60)
    print("Benchmark complete!")
    print()
    print("Notes:")
    print("- Performance varies by CPU")
    print("- Ed25519 is fast even without GPU")
    print("- Patterns longer than 6 chars need much more time")
    print("- GPU acceleration (future) can provide 100x speedup")


if __name__ == "__main__":
    run_benchmarks()
