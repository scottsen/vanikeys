"""Ed25519 key generation for Solana, DIDs, SSH, etc."""

import base58
import json
import time
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from vanikeys.core.types import KeyPair, KeyType
from vanikeys.generators.base import KeyGenerator


class Ed25519Generator(KeyGenerator):
    """
    Ed25519 elliptic curve key generator.

    Ed25519 is used by:
    - Solana blockchain
    - DIDs (did:key with Ed25519)
    - SSH (Ed25519 keys)
    - Various other modern cryptographic systems

    Performance: ~300K keys/sec on modern CPU (M1/Intel i7)
    Note: Cannot use offset optimization (requires full SHA512 hash per key)
    """

    def __init__(self, encoding: str = "base58"):
        """
        Initialize Ed25519 generator.

        Args:
            encoding: How to encode public key for searchable string
                     Options: base58, hex, base64
        """
        self.encoding = encoding

    @property
    def key_type(self) -> KeyType:
        """Return Ed25519 key type."""
        return KeyType.ED25519

    def generate(self) -> KeyPair:
        """Generate a new Ed25519 key pair."""
        # Generate private key
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Extract raw bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # Encode public key as address
        if self.encoding == "base58":
            address = base58.b58encode(public_bytes).decode('ascii')
        elif self.encoding == "hex":
            address = public_bytes.hex()
        elif self.encoding == "base64":
            import base64
            address = base64.b64encode(public_bytes).decode('ascii')
        else:
            raise ValueError(f"Unknown encoding: {self.encoding}")

        return KeyPair(
            private_key=private_bytes,
            public_key=public_bytes,
            address=address,
            key_type=KeyType.ED25519,
            metadata={
                "curve": "ed25519",
                "encoding": self.encoding,
                "public_key_length": len(public_bytes),
                "private_key_length": len(private_bytes),
            }
        )

    def get_searchable_string(self, keypair: KeyPair) -> str:
        """
        Extract the searchable string from a key pair.

        For Ed25519, this is the encoded public key (address).
        """
        return keypair.address

    def export(self, keypair: KeyPair, format_type: str = "pem") -> str:
        """
        Export Ed25519 key pair in various formats.

        Args:
            keypair: The key pair to export
            format_type: Output format (pem, json, hex, raw)

        Returns:
            Formatted key string
        """
        if format_type == "pem":
            # Recreate key objects for PEM export
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(keypair.private_key)

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            return f"{private_pem}\n{public_pem}"

        elif format_type == "json":
            return json.dumps({
                "key_type": "ed25519",
                "private_key": keypair.private_key.hex(),
                "public_key": keypair.public_key.hex(),
                "address": keypair.address,
                "encoding": self.encoding,
            }, indent=2)

        elif format_type == "hex":
            return (
                f"Private: {keypair.private_key.hex()}\n"
                f"Public:  {keypair.public_key.hex()}\n"
                f"Address: {keypair.address}"
            )

        elif format_type == "raw":
            # Base58 encoded (Solana style)
            private_b58 = base58.b58encode(keypair.private_key).decode('ascii')
            public_b58 = keypair.address  # Already base58 if that's the encoding
            return f"Private: {private_b58}\nPublic:  {public_b58}"

        else:
            raise ValueError(f"Unknown format: {format_type}")

    def benchmark(self, iterations: int = 1000) -> float:
        """
        Benchmark Ed25519 key generation rate.

        Args:
            iterations: Number of keys to generate

        Returns:
            Keys per second
        """
        start = time.perf_counter()

        for _ in range(iterations):
            self.generate()

        elapsed = time.perf_counter() - start
        return iterations / elapsed


class Ed25519DIDGenerator(Ed25519Generator):
    """
    Ed25519 generator specifically for DID creation.

    Generates did:key style DIDs using Ed25519 keys.
    """

    def __init__(self):
        """Initialize DID generator with multibase encoding."""
        super().__init__(encoding="base58")

    @property
    def key_type(self) -> KeyType:
        """Return DID key type."""
        return KeyType.DID_KEY

    def generate(self) -> KeyPair:
        """Generate Ed25519 key pair and create DID."""
        # Generate base key pair
        keypair = super().generate()

        # Create did:key identifier
        # Format: did:key:z<multibase-multicodec-encoded-public-key>
        # For Ed25519: multicodec prefix is 0xed01
        # Multibase z = base58btc

        # Add multicodec prefix for Ed25519 public key (0xed01)
        multicodec_pubkey = b'\xed\x01' + keypair.public_key

        # Encode with base58btc (multibase 'z')
        did = f"did:key:z{base58.b58encode(multicodec_pubkey).decode('ascii')}"

        # Update address to be the full DID
        return KeyPair(
            private_key=keypair.private_key,
            public_key=keypair.public_key,
            address=did,
            key_type=KeyType.DID_KEY,
            metadata={
                **keypair.metadata,
                "did_method": "key",
                "multicodec": "ed25519-pub",
                "multibase": "base58btc",
            }
        )

    def export(self, keypair: KeyPair, format_type: str = "did_document") -> str:
        """
        Export DID key with optional DID document.

        Args:
            keypair: The key pair with DID address
            format_type: Output format (did, did_document, json, pem)
        """
        if format_type == "did":
            return keypair.address

        elif format_type == "did_document":
            # Create minimal DID document
            doc = {
                "@context": [
                    "https://www.w3.org/ns/did/v1",
                    "https://w3id.org/security/suites/ed25519-2020/v1"
                ],
                "id": keypair.address,
                "verificationMethod": [{
                    "id": f"{keypair.address}#{keypair.address.split(':')[-1]}",
                    "type": "Ed25519VerificationKey2020",
                    "controller": keypair.address,
                    "publicKeyMultibase": keypair.address.split(':')[-1]
                }],
                "authentication": [
                    f"{keypair.address}#{keypair.address.split(':')[-1]}"
                ],
                "assertionMethod": [
                    f"{keypair.address}#{keypair.address.split(':')[-1]}"
                ]
            }
            return json.dumps(doc, indent=2)

        else:
            # Fall back to parent class export
            return super().export(keypair, format_type)


if __name__ == "__main__":
    # Quick test
    print("Testing Ed25519 generation...")

    gen = Ed25519Generator(encoding="base58")
    keypair = gen.generate()

    print(f"\nGenerated Ed25519 key:")
    print(f"Address: {keypair.address}")
    print(f"Public key: {keypair.public_key.hex()[:32]}...")

    # Benchmark
    rate = gen.benchmark(iterations=100)
    print(f"\nBenchmark: {rate:,.0f} keys/sec")

    # Test DID generation
    print("\n" + "=" * 60)
    print("Testing DID generation...")

    did_gen = Ed25519DIDGenerator()
    did_keypair = did_gen.generate()

    print(f"\nGenerated DID:")
    print(f"{did_keypair.address}")
    print(f"\nDID Document:")
    print(did_gen.export(did_keypair, "did_document"))
