"""Base classes for key generators."""

from abc import ABC, abstractmethod
from typing import Any

from vanikeys.core.types import KeyPair, KeyType


class KeyGenerator(ABC):
    """Abstract base class for all key generators."""

    @property
    @abstractmethod
    def key_type(self) -> KeyType:
        """The type of keys this generator produces."""
        pass

    @abstractmethod
    def generate(self) -> KeyPair:
        """
        Generate a new cryptographic key pair.

        Returns:
            A KeyPair with private key, public key, address, and metadata
        """
        pass

    @abstractmethod
    def get_searchable_string(self, keypair: KeyPair) -> str:
        """
        Extract the string representation to pattern match against.

        For Bitcoin/Ethereum: the base58 address
        For DIDs: the full DID string
        For SSH keys: the fingerprint or public key encoding

        Args:
            keypair: The key pair to extract searchable string from

        Returns:
            The string to match patterns against
        """
        pass

    @abstractmethod
    def export(self, keypair: KeyPair, format_type: str = "pem") -> str:
        """
        Export the key pair in a specified format.

        Args:
            keypair: The key pair to export
            format_type: Output format (pem, json, hex, etc.)

        Returns:
            Formatted key string
        """
        pass

    @abstractmethod
    def benchmark(self, iterations: int = 1000) -> float:
        """
        Benchmark key generation rate.

        Args:
            iterations: Number of keys to generate for benchmark

        Returns:
            Keys generated per second
        """
        pass

    def generate_batch(self, count: int) -> list[KeyPair]:
        """
        Generate multiple key pairs.

        Default implementation calls generate() repeatedly.
        Subclasses can override for optimized batch generation.

        Args:
            count: Number of key pairs to generate

        Returns:
            List of generated key pairs
        """
        return [self.generate() for _ in range(count)]
