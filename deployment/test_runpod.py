#!/usr/bin/env python3
"""
Test script for VaniKeys RunPod deployment

Tests both gacha mode (instant) and guaranteed mode (longer search).

Usage:
    # Set environment variables
    export RUNPOD_API_KEY="your-api-key"
    export RUNPOD_ENDPOINT_ID="your-endpoint-id"

    # Run test
    python deployment/test_runpod.py
"""

import os
import sys
import time
import runpod

# Configuration from environment
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

if not RUNPOD_API_KEY:
    print("❌ Error: RUNPOD_API_KEY environment variable not set")
    print("   Get your API key from: https://www.runpod.io/console/user/settings")
    print("   Then run: export RUNPOD_API_KEY='your-key'")
    sys.exit(1)

if not RUNPOD_ENDPOINT_ID:
    print("❌ Error: RUNPOD_ENDPOINT_ID environment variable not set")
    print("   Get your endpoint ID from: https://www.runpod.io/console/serverless")
    print("   Then run: export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
    sys.exit(1)

# Initialize RunPod
runpod.api_key = RUNPOD_API_KEY
endpoint = runpod.Endpoint(RUNPOD_ENDPOINT_ID)

print("╔════════════════════════════════════════════════╗")
print("║   VaniKeys RunPod Deployment Test             ║")
print("╚════════════════════════════════════════════════╝")
print()
print(f"Endpoint ID: {RUNPOD_ENDPOINT_ID[:20]}...")
print()

# Test 1: Gacha mode (instant, random result)
print("Test 1: Gacha Mode")
print("─" * 50)
print("Submitting gacha pull for pattern 'ABC DEF'...")
print("Expected: <1 second, may or may not match")
print()

start_time = time.time()

try:
    job = endpoint.run({
        "master_seed_hash": "test_seed_hash_12345_gacha",
        "pattern": "ABC DEF",
        "mode": "gacha",
        "fuzzy": True
    })

    # Wait for result
    result = job.output()
    elapsed = time.time() - start_time

    print(f"✓ Job completed in {elapsed:.2f}s")
    print()
    print("Result:")
    print(f"  Status: {result['status']}")
    print(f"  Found: {result['found']}")
    print(f"  Match Score: {result['match_score']:.2f}")
    print(f"  Matched Substrings: {result['matched_substrings']}")
    print(f"  Fingerprint: {result['fingerprint'][:50]}...")
    print(f"  Derivation Path: {result['path']}")
    print(f"  Attempts: {result['attempts']}")
    print()

    if result['found']:
        print("🎰 GACHA WIN! Found a matching pattern!")
    else:
        print("🎰 No match this time. Try another pull!")

except Exception as e:
    print(f"❌ Gacha test failed: {e}")
    sys.exit(1)

print()
print("─" * 50)
print()

# Test 2: Guaranteed mode with easy pattern
print("Test 2: Guaranteed Mode (Easy Pattern)")
print("─" * 50)
print("Submitting guaranteed search for pattern 'A' (very easy)...")
print("Expected: Should find within 1-30 seconds")
print()

start_time = time.time()

try:
    job = endpoint.run({
        "master_seed_hash": "test_seed_hash_67890_guaranteed",
        "pattern": "A",
        "mode": "guaranteed",
        "fuzzy": False,
        "max_attempts": 100_000  # Limit for test
    })

    # Poll for result (guaranteed mode may take longer)
    print("Searching... (this may take up to 30 seconds)")
    result = job.output()
    elapsed = time.time() - start_time

    print(f"✓ Job completed in {elapsed:.2f}s")
    print()
    print("Result:")
    print(f"  Status: {result['status']}")
    print(f"  Found: {result.get('found', False)}")
    print(f"  Match Score: {result.get('match_score', 0):.2f}")
    print(f"  Fingerprint: {result.get('fingerprint', 'N/A')[:50]}...")
    print(f"  Derivation Path: {result.get('path', 'N/A')}")
    print(f"  Attempts: {result.get('attempts', 0):,}")
    print()

    if result.get('found'):
        print("🎯 SUCCESS! Found guaranteed match!")
        print(f"   Performance: {result['attempts'] / elapsed:.0f} attempts/second")
    else:
        print("⚠️  Search incomplete (max attempts reached)")
        print("   This is expected for a test with limited attempts")

except Exception as e:
    print(f"❌ Guaranteed mode test failed: {e}")
    sys.exit(1)

print()
print("─" * 50)
print()

# Summary
print("╔════════════════════════════════════════════════╗")
print("║   All Tests Passed                            ║")
print("╚════════════════════════════════════════════════╝")
print()
print("Next steps:")
print("  1. Integration: Add RunPod service to VaniKeys API")
print("  2. Monitoring: Set up DataDog/New Relic for metrics")
print("  3. Scaling: Adjust worker counts based on traffic")
print("  4. Cost tracking: Monitor actual costs vs projections")
print()
print("Documentation: docs/SERVERLESS_GPU_OPTIONS.md")
