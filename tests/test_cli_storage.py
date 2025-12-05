"""
Tests for CLI secure seed storage.
"""

import os
import json
import tempfile
from pathlib import Path

import pytest

from vanikeys.cli.storage import SeedStorage
from vanikeys.crypto.derivation import generate_master_seed, seed_to_root_keypair, public_key_to_bytes


class TestSeedStorage:
    """Tests for SeedStorage class."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Return a subdirectory that doesn't exist yet
            yield Path(tmpdir) / "vanikeys"

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create storage instance with temp directory."""
        return SeedStorage(temp_storage_dir)

    def test_initialize_creates_directory(self, storage):
        """Test that initialize creates storage directory."""
        assert not storage.storage_dir.exists()

        storage.initialize()

        assert storage.storage_dir.exists()
        assert storage.storage_dir.is_dir()
        # Check permissions (should be 0700)
        stat = storage.storage_dir.stat()
        assert oct(stat.st_mode)[-3:] == "700"

    def test_exists_returns_false_when_no_seed(self, storage):
        """Test exists() returns False when seed file doesn't exist."""
        assert not storage.exists()

    def test_save_and_load_seed(self, storage):
        """Test saving and loading seed with encryption."""
        # Generate test data
        seed = generate_master_seed()
        password = "test_password_123"
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        # Save seed
        storage.save_seed(seed, password, root_public_key_bytes)

        # Check file exists
        assert storage.exists()
        assert storage.seed_file.exists()

        # Check file permissions (should be 0600)
        stat = storage.seed_file.stat()
        assert oct(stat.st_mode)[-3:] == "600"

        # Load seed
        loaded_seed, loaded_public_key = storage.load_seed(password)

        # Verify data matches
        assert loaded_seed == seed
        assert loaded_public_key == root_public_key_bytes

    def test_load_seed_with_wrong_password(self, storage):
        """Test that wrong password fails to decrypt."""
        seed = generate_master_seed()
        password = "correct_password"
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        storage.save_seed(seed, password, root_public_key_bytes)

        # Try to load with wrong password
        with pytest.raises(ValueError, match="Incorrect password"):
            storage.load_seed("wrong_password")

    def test_save_seed_invalid_length(self, storage):
        """Test that invalid seed length is rejected."""
        invalid_seed = b"too_short"
        password = "test_password"
        root_public_key_bytes = os.urandom(32)

        with pytest.raises(ValueError, match="32 bytes"):
            storage.save_seed(invalid_seed, password, root_public_key_bytes)

    def test_load_seed_file_not_found(self, storage):
        """Test that loading non-existent seed raises error."""
        with pytest.raises(FileNotFoundError):
            storage.load_seed("any_password")

    def test_get_root_public_key_without_password(self, storage):
        """Test getting root public key without decrypting seed."""
        seed = generate_master_seed()
        password = "test_password"
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        storage.save_seed(seed, password, root_public_key_bytes)

        # Get public key without password
        loaded_public_key = storage.get_root_public_key()

        assert loaded_public_key == root_public_key_bytes

    def test_save_and_load_config(self, storage):
        """Test saving and loading configuration."""
        config = {
            "version": "0.2.0",
            "api_url": "https://api.vanikeys.dev",
            "some_setting": True,
        }

        storage.save_config(config)

        loaded_config = storage.load_config()

        assert loaded_config == config

    def test_load_config_when_missing(self, storage):
        """Test loading config when file doesn't exist returns empty dict."""
        config = storage.load_config()

        assert config == {}

    def test_atomic_write_on_save(self, storage):
        """Test that save_seed uses atomic write (temp file + rename)."""
        seed = generate_master_seed()
        password = "test_password"
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        storage.save_seed(seed, password, root_public_key_bytes)

        # Verify no temp file left behind
        temp_file = storage.seed_file.with_suffix(".tmp")
        assert not temp_file.exists()

        # Verify seed file exists
        assert storage.seed_file.exists()

    def test_seed_file_format_version(self, storage):
        """Test that seed file contains version field."""
        seed = generate_master_seed()
        password = "test_password"
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        storage.save_seed(seed, password, root_public_key_bytes)

        # Read raw file
        with open(storage.seed_file) as f:
            data = json.load(f)

        assert "version" in data
        assert data["version"] == 1

    def test_deterministic_encryption(self, storage):
        """Test that same seed+password produces different encrypted output (due to random salt)."""
        seed = generate_master_seed()
        password = "test_password"
        _, root_public_key = seed_to_root_keypair(seed)
        root_public_key_bytes = public_key_to_bytes(root_public_key)

        # Save twice
        storage.save_seed(seed, password, root_public_key_bytes)

        with open(storage.seed_file) as f:
            data1 = json.load(f)

        storage.save_seed(seed, password, root_public_key_bytes)

        with open(storage.seed_file) as f:
            data2 = json.load(f)

        # Salts should be different (random)
        assert data1["salt"] != data2["salt"]

        # But both should decrypt to same seed
        loaded_seed1, _ = storage.load_seed(password)
        assert loaded_seed1 == seed
