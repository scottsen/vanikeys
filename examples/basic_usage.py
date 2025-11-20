#!/usr/bin/env python3
"""
Basic VaniKeys usage examples.

Demonstrates programmatic use of VaniKeys library.
"""

from vanikeys.generators.ed25519 import Ed25519Generator, Ed25519DIDGenerator
from vanikeys.matchers.simple import PrefixMatcher, ContainsMatcher
from vanikeys.core.engine import VanityEngine
from vanikeys.core.difficulty import DifficultyCalculator
from vanikeys.core.types import PatternConfig, PatternMatchType


def example_1_simple_vanity():
    """Generate Ed25519 key with pattern in base58 address."""
    print("=" * 60)
    print("Example 1: Simple Ed25519 Vanity Key")
    print("=" * 60)

    # Create generator and matcher
    generator = Ed25519Generator(encoding="base58")
    matcher = ContainsMatcher("ABC", case_sensitive=False)

    # Create engine
    engine = VanityEngine(generator, matcher)

    # Generate!
    print("\nGenerating Ed25519 key containing 'ABC'...")
    keypair, metrics = engine.generate(verbose=True)

    print(f"\n\n✅ Success!")
    print(f"Address: {keypair.address}")
    print(f"Attempts: {metrics.attempts:,}")
    print(f"Time: {metrics.elapsed_seconds:.2f}s")
    print(f"Rate: {metrics.formatted_rate}")


def example_2_did_vanity():
    """Generate vanity DID (Decentralized Identifier)."""
    print("\n\n" + "=" * 60)
    print("Example 2: Vanity DID Generation")
    print("=" * 60)

    # Create DID generator
    generator = Ed25519DIDGenerator()
    matcher = ContainsMatcher("LAB", case_sensitive=False)

    # Create engine
    engine = VanityEngine(generator, matcher)

    # Generate!
    print("\nGenerating DID containing 'LAB'...")
    keypair, metrics = engine.generate(verbose=True)

    print(f"\n\n✅ Success!")
    print(f"DID: {keypair.address}")
    print(f"Attempts: {metrics.attempts:,}")

    # Export as DID document
    print("\nDID Document:")
    doc = generator.export(keypair, "did_document")
    print(doc)


def example_3_difficulty_estimation():
    """Estimate difficulty before generating."""
    print("\n\n" + "=" * 60)
    print("Example 3: Difficulty Estimation")
    print("=" * 60)

    calc = DifficultyCalculator("base58")

    patterns = ["AB", "ABC", "ABCD", "ABCDE"]

    print("\nDifficulty estimates for contains matching:\n")
    print(f"{'Pattern':<10} {'Attempts':>15} {'Difficulty':>12} {'Est. Time (300K/s)':>20}")
    print("-" * 70)

    for pattern in patterns:
        config = PatternConfig(
            pattern=pattern,
            match_type=PatternMatchType.CONTAINS,
            case_sensitive=False
        )
        difficulty = calc.calculate(config)
        est_time = difficulty.estimated_time(300_000)

        print(
            f"{pattern:<10} {difficulty.average_attempts:>15,} "
            f"{difficulty.difficulty_rating.upper():>12} {str(est_time):>20}"
        )


def example_4_prefix_matching():
    """Generate key with prefix pattern (hardest)."""
    print("\n\n" + "=" * 60)
    print("Example 4: Prefix Matching")
    print("=" * 60)

    # Prefix matching is hardest - use short pattern
    generator = Ed25519Generator(encoding="base58")
    matcher = PrefixMatcher("AA", case_sensitive=False)

    engine = VanityEngine(generator, matcher)

    print("\nGenerating key starting with 'AA'...")
    keypair, metrics = engine.generate(verbose=True)

    print(f"\n\n✅ Success!")
    print(f"Address: {keypair.address}")
    print(f"Attempts: {metrics.attempts:,}")


def example_5_export_formats():
    """Demonstrate different export formats."""
    print("\n\n" + "=" * 60)
    print("Example 5: Export Formats")
    print("=" * 60)

    # Generate a key
    generator = Ed25519Generator(encoding="base58")
    keypair = generator.generate()

    print("\n--- PEM Format ---")
    print(generator.export(keypair, "pem"))

    print("\n--- JSON Format ---")
    print(generator.export(keypair, "json"))

    print("\n--- Hex Format ---")
    print(generator.export(keypair, "hex"))


if __name__ == "__main__":
    # Run examples
    example_1_simple_vanity()
    example_2_did_vanity()
    example_3_difficulty_estimation()
    example_4_prefix_matching()
    example_5_export_formats()

    print("\n\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
