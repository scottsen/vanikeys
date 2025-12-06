"""
RunPod Serverless Handler for VaniKeys

This handler receives vanity key search requests and uses GPU acceleration
to find matching SSH key fingerprints.

Environment variables:
- RUNPOD_API_KEY: RunPod API key (set in RunPod dashboard)
"""

import runpod
import sys
import os
import random
import traceback
from typing import Dict, Any

# Add VaniKeys to path
sys.path.insert(0, '/workspace/vanikeys/src')

from vanikeys.crypto import (
    generate_master_seed,
    seed_to_root_keypair,
    derive_child_keypair,
    compute_ssh_fingerprint,
)
from vanikeys.matchers import MultiSubstringMatcher


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler for VaniKeys vanity key generation.

    Input format:
    {
        "master_seed_hash": "sha256_hash_of_user_seed",  # SHA256 of user's master seed
        "pattern": "GO BE AWE SOME",                      # Space-separated substrings
        "mode": "gacha",                                  # "gacha" or "guaranteed"
        "fuzzy": true,                                    # Enable fuzzy matching (0→O, 1→I)
        "max_attempts": 1000000000                        # For guaranteed mode
    }

    Output format (gacha mode):
    {
        "status": "success",
        "found": true/false,
        "path": 12345,                      # Derivation path index
        "fingerprint": "SHA256:...",        # Full SSH fingerprint
        "match_score": 0.75,                # 0.0-1.0 (1.0 = exact match)
        "matched_substrings": ["GO", "BE"], # Which substrings matched
        "attempts": 1
    }

    Output format (guaranteed mode - success):
    {
        "status": "success",
        "found": true,
        "path": 4567890,
        "fingerprint": "SHA256:...",
        "match_score": 1.0,
        "matched_substrings": ["GO", "BE", "AWE", "SOME"],
        "attempts": 4567891
    }

    Output format (error):
    {
        "status": "error",
        "error": "Error message"
    }
    """
    try:
        # Extract parameters
        pattern = job['input']['pattern']
        mode = job['input'].get('mode', 'gacha')
        fuzzy = job['input'].get('fuzzy', False)
        seed_hash = job['input']['master_seed_hash']

        print(f"[VaniKeys] Starting search - Pattern: '{pattern}', Mode: {mode}, Fuzzy: {fuzzy}")

        # Parse pattern into substrings
        substrings = pattern.upper().split()
        print(f"[VaniKeys] Parsed substrings: {substrings}")

        # Create matcher
        matcher = MultiSubstringMatcher(
            substrings=substrings,
            fuzzy=fuzzy,
            case_insensitive=True
        )

        # Set max attempts
        max_attempts = job['input'].get('max_attempts', 1 if mode == 'gacha' else 10_000_000_000)

        # Start search from random offset for each job (for gacha mode variety)
        start_path = random.randint(0, 2**31) if mode == 'gacha' else 0
        attempts = 0

        print(f"[VaniKeys] Starting search at path {start_path}")

        while attempts < max_attempts:
            path = start_path + attempts

            # Generate key at this derivation path
            # Note: seed_hash is a placeholder - in production this needs the actual
            # user master seed hash via the zero-knowledge protocol
            try:
                seed_bytes = seed_hash.encode().ljust(32, b'\x00')[:32]  # Ensure 32 bytes
                priv_key, pub_key = derive_child_keypair(seed_bytes, path)
            except Exception as e:
                return {
                    'status': 'error',
                    'error': f"Key derivation failed at path {path}: {str(e)}"
                }

            # Compute SSH fingerprint
            fingerprint = compute_ssh_fingerprint(pub_key)
            # Extract the base64 part after SHA256:
            fingerprint_b64 = fingerprint.split(':')[1]

            # Check if it matches pattern
            match_result = matcher.match(fingerprint_b64)

            attempts += 1

            # Gacha mode: return after 1 attempt (instant pull)
            if mode == 'gacha':
                result = {
                    'status': 'success',
                    'found': match_result.score > 0,
                    'path': path,
                    'fingerprint': fingerprint,
                    'match_score': match_result.score,
                    'matched_substrings': match_result.matched_substrings,
                    'attempts': attempts
                }
                print(f"[VaniKeys] Gacha result - Found: {result['found']}, Score: {result['match_score']:.2f}")
                return result

            # Guaranteed mode: continue until exact match
            if match_result.score == 1.0:
                result = {
                    'status': 'success',
                    'found': True,
                    'path': path,
                    'fingerprint': fingerprint,
                    'match_score': 1.0,
                    'matched_substrings': match_result.matched_substrings,
                    'attempts': attempts
                }
                print(f"[VaniKeys] Guaranteed mode - FOUND at path {path} after {attempts:,} attempts!")
                return result

            # Progress updates every 100K attempts
            if attempts % 100_000 == 0:
                print(f"[VaniKeys] Progress: {attempts:,} attempts, best score: {match_result.score:.2f}")

        # Max attempts reached without exact match
        result = {
            'status': 'incomplete',
            'attempts': attempts,
            'message': f'Max attempts ({max_attempts:,}) reached without exact match'
        }
        print(f"[VaniKeys] Search incomplete - {attempts:,} attempts exhausted")
        return result

    except KeyError as e:
        error_msg = f"Missing required parameter: {str(e)}"
        print(f"[VaniKeys ERROR] {error_msg}")
        return {
            'status': 'error',
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
        print(f"[VaniKeys ERROR] {error_msg}")
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


# Start RunPod serverless
print("[VaniKeys] Initializing RunPod serverless handler...")
runpod.serverless.start({"handler": handler})
print("[VaniKeys] Handler ready!")
