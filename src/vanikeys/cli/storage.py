"""
Secure seed storage for VaniKeys CLI.

Seeds are encrypted with a user-provided password using Fernet (symmetric encryption).
Storage location: ~/.vanikeys/seed.enc
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SeedStorage:
    """Manages secure storage of VaniKeys seeds."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize storage manager.

        Args:
            storage_dir: Directory for seed storage (default: ~/.vanikeys)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".vanikeys"

        self.storage_dir = storage_dir
        self.seed_file = storage_dir / "seed.enc"
        self.config_file = storage_dir / "config.json"

    def initialize(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Check if a seed file exists."""
        return self.seed_file.exists()

    def save_seed(self, seed: bytes, password: str, root_public_key: bytes) -> None:
        """Encrypt and save seed to disk.

        Args:
            seed: Raw 32-byte seed
            password: User password for encryption
            root_public_key: Root public key (stored for convenience)

        Raises:
            ValueError: If seed is invalid
            OSError: If file cannot be written
        """
        if len(seed) != 32:
            raise ValueError("Seed must be 32 bytes")

        self.initialize()

        # Derive encryption key from password using PBKDF2
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,  # OWASP recommendation 2023
        )
        key = kdf.derive(password.encode("utf-8"))

        # Encrypt seed with Fernet (AES-128-CBC + HMAC)
        fernet = Fernet(Fernet.generate_key())
        encrypted_seed = fernet.encrypt(seed)

        # Encrypt fernet key with derived key
        key_fernet = Fernet(self._key_to_fernet_key(key))
        fernet_keys = fernet._signing_key + fernet._encryption_key
        encrypted_fernet_key = key_fernet.encrypt(fernet_keys)

        # Store encrypted data
        data = {
            "version": 1,
            "salt": salt.hex(),
            "encrypted_fernet_key": encrypted_fernet_key.decode("utf-8"),
            "encrypted_seed": encrypted_seed.decode("utf-8"),
            "root_public_key": root_public_key.hex(),
            "kdf_iterations": 600_000,
        }

        # Write atomically (write to temp file, then rename)
        temp_file = self.seed_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # Set restrictive permissions before renaming
        os.chmod(temp_file, 0o600)
        temp_file.rename(self.seed_file)

    def load_seed(self, password: str) -> tuple[bytes, bytes]:
        """Decrypt and load seed from disk.

        Args:
            password: User password for decryption

        Returns:
            Tuple of (seed, root_public_key)

        Raises:
            FileNotFoundError: If seed file doesn't exist
            ValueError: If password is incorrect or data is corrupted
        """
        if not self.seed_file.exists():
            raise FileNotFoundError(f"Seed file not found: {self.seed_file}")

        with open(self.seed_file) as f:
            data = json.load(f)

        # Validate version
        if data.get("version") != 1:
            raise ValueError("Unsupported seed file version")

        # Extract stored data
        salt = bytes.fromhex(data["salt"])
        encrypted_fernet_key = data["encrypted_fernet_key"].encode("utf-8")
        encrypted_seed = data["encrypted_seed"].encode("utf-8")
        root_public_key = bytes.fromhex(data["root_public_key"])
        iterations = data.get("kdf_iterations", 600_000)

        # Derive encryption key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        key = kdf.derive(password.encode("utf-8"))

        try:
            # Decrypt fernet key
            key_fernet = Fernet(self._key_to_fernet_key(key))
            fernet_key = key_fernet.decrypt(encrypted_fernet_key)

            # Reconstruct Fernet cipher
            fernet = Fernet(self._reconstruct_fernet_key(fernet_key))

            # Decrypt seed
            seed = fernet.decrypt(encrypted_seed)

        except Exception as e:
            raise ValueError("Incorrect password or corrupted seed file") from e

        if len(seed) != 32:
            raise ValueError("Decrypted seed has invalid length")

        return seed, root_public_key

    def save_config(self, config: dict) -> None:
        """Save CLI configuration.

        Args:
            config: Configuration dictionary
        """
        self.initialize()
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def load_config(self) -> dict:
        """Load CLI configuration.

        Returns:
            Configuration dictionary (empty dict if not found)
        """
        if not self.config_file.exists():
            return {}

        with open(self.config_file) as f:
            return json.load(f)

    @staticmethod
    def _key_to_fernet_key(key: bytes) -> bytes:
        """Convert 32-byte key to Fernet-compatible format."""
        import base64
        return base64.urlsafe_b64encode(key)

    @staticmethod
    def _reconstruct_fernet_key(fernet_key: bytes) -> bytes:
        """Reconstruct Fernet key from decrypted key material."""
        import base64
        return base64.urlsafe_b64encode(fernet_key)

    def get_root_public_key(self) -> Optional[bytes]:
        """Get root public key without requiring password.

        Returns:
            Root public key bytes, or None if not initialized
        """
        if not self.seed_file.exists():
            return None

        with open(self.seed_file) as f:
            data = json.load(f)

        return bytes.fromhex(data["root_public_key"])
