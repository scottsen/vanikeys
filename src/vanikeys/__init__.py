"""
VaniKeys: Vanity cryptographic key generation with pattern matching.

Generate cryptographic key pairs with customized public key patterns.
"""

__version__ = "0.1.0"
__author__ = "TIA"

from vanikeys.core.engine import VanityEngine
from vanikeys.core.difficulty import DifficultyEstimate
from vanikeys.core.types import KeyPair

__all__ = [
    "VanityEngine",
    "DifficultyEstimate",
    "KeyPair",
]
