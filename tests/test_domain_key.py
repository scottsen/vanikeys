"""
Tests for VanityKey domain model.

Validates key creation, properties, and serialization.
"""

import pytest
from vanikeys.domain.key import VanityKey


class TestVanityKeyCreation:
    """Test vanity key creation."""

    def test_create_basic_key(self):
        """Can create basic vanity key."""
        key = VanityKey(
            did="did:key:z6MkGOBEAWESOME123",
            public_key="abcd1234",
            private_key="secret5678",
            matched_pattern="GO BE AWE SOME",
            generation_time=0.5,
            attempts=50000
        )
        assert key.did == "did:key:z6MkGOBEAWESOME123"
        assert key.public_key == "abcd1234"
        assert key.private_key == "secret5678"
        assert key.matched_pattern == "GO BE AWE SOME"
        assert key.generation_time == 0.5
        assert key.attempts == 50000

    def test_create_key_without_private_key(self):
        """Can create key without private key (public display)."""
        key = VanityKey(
            did="did:key:z6MkALICE123",
            public_key="pub123",
            private_key=None,
            matched_pattern="ALICE"
        )
        assert key.private_key is None
        assert key.public_key == "pub123"

    def test_create_key_with_match_positions(self):
        """Can create key with match positions."""
        key = VanityKey(
            did="did:key:z6MkGOBEAWESOME",
            public_key="pub",
            private_key="priv",
            matched_pattern="GO BE AWE",
            match_positions=[(10, 12), (15, 17), (20, 23)]
        )
        assert len(key.match_positions) == 3
        assert key.match_positions[0] == (10, 12)

    def test_create_key_with_metadata(self):
        """Can create key with full metadata."""
        key = VanityKey(
            did="did:key:z6MkTEST",
            public_key="pub",
            private_key="priv",
            matched_pattern="TEST",
            generation_time=2.5,
            attempts=100000,
            worker_id="worker_gpu_01",
            id="key_abc123",
            pull_id="pull_xyz789",
            created_at="2025-12-03T10:00:00Z"
        )
        assert key.worker_id == "worker_gpu_01"
        assert key.id == "key_abc123"
        assert key.pull_id == "pull_xyz789"
        assert key.created_at == "2025-12-03T10:00:00Z"


class TestVanityKeyProperties:
    """Test vanity key property methods."""

    def test_did_suffix(self):
        """did_suffix extracts readable portion."""
        key = VanityKey(
            did="did:key:z6MkGOBEAWESOME123",
            public_key="pub",
            private_key="priv",
            matched_pattern="GO BE AWE SOME"
        )
        assert key.did_suffix == "GOBEAWESOME123"

    def test_did_suffix_non_standard_did(self):
        """did_suffix returns full DID for non-standard format."""
        key = VanityKey(
            did="did:example:123",
            public_key="pub",
            private_key="priv",
            matched_pattern="TEST"
        )
        assert key.did_suffix == "did:example:123"

    def test_is_match_quality_excellent_true(self):
        """is_match_quality_excellent returns True for long patterns."""
        key = VanityKey(
            did="did:key:z6MkGOBEAWESOME",
            public_key="pub",
            private_key="priv",
            matched_pattern="GO BE AWE SOME"  # 14 chars without spaces
        )
        assert key.is_match_quality_excellent is True

    def test_is_match_quality_excellent_false(self):
        """is_match_quality_excellent returns False for short patterns."""
        key = VanityKey(
            did="did:key:z6MkABC",
            public_key="pub",
            private_key="priv",
            matched_pattern="ABC"  # 3 chars
        )
        assert key.is_match_quality_excellent is False

    def test_abbreviated_did_short(self):
        """abbreviated_did returns full DID for short DIDs."""
        key = VanityKey(
            did="did:key:z6MkABC123",
            public_key="pub",
            private_key="priv",
            matched_pattern="ABC"
        )
        assert key.abbreviated_did == "did:key:z6MkABC123"

    def test_abbreviated_did_long(self):
        """abbreviated_did truncates long DIDs."""
        long_did = "did:key:z6Mk" + "X" * 50
        key = VanityKey(
            did=long_did,
            public_key="pub",
            private_key="priv",
            matched_pattern="TEST"
        )
        abbreviated = key.abbreviated_did
        assert abbreviated.startswith("did:key:z6MkXXXX")
        assert "..." in abbreviated
        assert len(abbreviated) < len(long_did)


class TestVanityKeySerialization:
    """Test vanity key serialization."""

    def test_to_dict_without_private_key(self):
        """to_dict() excludes private key by default."""
        key = VanityKey(
            did="did:key:z6MkALICE",
            public_key="pub123",
            private_key="secret456",
            matched_pattern="ALICE"
        )
        data = key.to_dict(include_private_key=False)

        assert "private_key" not in data
        assert data["public_key"] == "pub123"
        assert data["did"] == "did:key:z6MkALICE"

    def test_to_dict_with_private_key(self):
        """to_dict() includes private key when requested."""
        key = VanityKey(
            did="did:key:z6MkALICE",
            public_key="pub123",
            private_key="secret456",
            matched_pattern="ALICE"
        )
        data = key.to_dict(include_private_key=True)

        assert data["private_key"] == "secret456"
        assert data["public_key"] == "pub123"

    def test_to_dict_all_fields(self):
        """to_dict() includes all fields."""
        key = VanityKey(
            did="did:key:z6MkTEST",
            public_key="pub",
            private_key="priv",
            matched_pattern="TEST",
            match_positions=[(5, 9)],
            generation_time=1.5,
            attempts=75000,
            worker_id="worker_01",
            id="key_123",
            pull_id="pull_456",
            created_at="2025-12-03T11:00:00Z"
        )
        data = key.to_dict(include_private_key=True)

        assert data["id"] == "key_123"
        assert data["did"] == "did:key:z6MkTEST"
        assert data["public_key"] == "pub"
        assert data["private_key"] == "priv"
        assert data["matched_pattern"] == "TEST"
        assert data["match_positions"] == [(5, 9)]
        assert data["generation_time"] == 1.5
        assert data["attempts"] == 75000
        assert data["worker_id"] == "worker_01"
        assert data["pull_id"] == "pull_456"
        assert data["created_at"] == "2025-12-03T11:00:00Z"

    def test_from_dict_basic(self):
        """from_dict() creates key from dictionary."""
        data = {
            "did": "did:key:z6MkBOB",
            "public_key": "pub789",
            "matched_pattern": "BOB"
        }
        key = VanityKey.from_dict(data)

        assert key.did == "did:key:z6MkBOB"
        assert key.public_key == "pub789"
        assert key.matched_pattern == "BOB"
        assert key.private_key is None  # Not in dict

    def test_from_dict_with_private_key(self):
        """from_dict() restores private key."""
        data = {
            "did": "did:key:z6MkCHARLIE",
            "public_key": "pub",
            "private_key": "secret",
            "matched_pattern": "CHARLIE"
        }
        key = VanityKey.from_dict(data)

        assert key.private_key == "secret"

    def test_from_dict_with_optional_fields(self):
        """from_dict() handles optional fields with defaults."""
        data = {
            "did": "did:key:z6MkDAVE",
            "public_key": "pub",
            "matched_pattern": "DAVE"
        }
        key = VanityKey.from_dict(data)

        assert key.generation_time == 0.0
        assert key.attempts == 0
        assert key.worker_id is None
        assert key.match_positions is None

    def test_from_dict_all_fields(self):
        """from_dict() restores all fields."""
        data = {
            "did": "did:key:z6MkEVE",
            "public_key": "pub",
            "private_key": "priv",
            "matched_pattern": "EVE",
            "match_positions": [(10, 13)],
            "generation_time": 3.0,
            "attempts": 150000,
            "worker_id": "worker_02",
            "id": "key_789",
            "pull_id": "pull_012",
            "created_at": "2025-12-03T12:00:00Z"
        }
        key = VanityKey.from_dict(data)

        assert key.did == "did:key:z6MkEVE"
        assert key.public_key == "pub"
        assert key.private_key == "priv"
        assert key.matched_pattern == "EVE"
        assert key.match_positions == [(10, 13)]
        assert key.generation_time == 3.0
        assert key.attempts == 150000
        assert key.worker_id == "worker_02"
        assert key.id == "key_789"
        assert key.pull_id == "pull_012"
        assert key.created_at == "2025-12-03T12:00:00Z"

    def test_roundtrip_serialization(self):
        """Key survives to_dict() -> from_dict() roundtrip."""
        original = VanityKey(
            did="did:key:z6MkFRANK",
            public_key="pub123",
            private_key="secret456",
            matched_pattern="FRANK",
            match_positions=[(8, 13)],
            generation_time=2.2,
            attempts=90000,
            worker_id="worker_03",
            id="key_xyz",
            pull_id="pull_abc",
            created_at="2025-12-03T13:00:00Z"
        )

        data = original.to_dict(include_private_key=True)
        restored = VanityKey.from_dict(data)

        assert restored.did == original.did
        assert restored.public_key == original.public_key
        assert restored.private_key == original.private_key
        assert restored.matched_pattern == original.matched_pattern
        assert restored.match_positions == original.match_positions
        assert restored.generation_time == original.generation_time
        assert restored.attempts == original.attempts
        assert restored.worker_id == original.worker_id
        assert restored.id == original.id
        assert restored.pull_id == original.pull_id
        assert restored.created_at == original.created_at


class TestRealWorldKeys:
    """Test realistic vanity key scenarios."""

    def test_simple_vanity_key(self):
        """Simple 3-char vanity key (common)."""
        key = VanityKey(
            did="did:key:z6MkDEV123xxxxx",
            public_key="abc123",
            private_key="secret",
            matched_pattern="DEV",
            generation_time=0.1,
            attempts=5000
        )
        assert key.matched_pattern == "DEV"
        assert key.is_match_quality_excellent is False

    def test_complex_multi_substring_key(self):
        """Complex multi-substring vanity key (rare)."""
        key = VanityKey(
            did="did:key:z6MkGOBEAWESOME789",
            public_key="xyz789",
            private_key="topsecret",
            matched_pattern="GO BE AWE SOME",
            match_positions=[(10, 12), (15, 17), (20, 23), (28, 32)],
            generation_time=45.5,
            attempts=5000000,
            worker_id="gpu_worker_1"
        )
        assert key.is_match_quality_excellent is True
        assert len(key.match_positions) == 4
        assert key.attempts == 5000000

    def test_guaranteed_mode_key(self):
        """Key generated in guaranteed mode (long generation time)."""
        key = VanityKey(
            did="did:key:z6MkACMEDEVTEAM",
            public_key="team123",
            private_key="teamkey",
            matched_pattern="ACME DEV TEAM",
            generation_time=120.0,  # 2 minutes
            attempts=12000000,
            worker_id="guaranteed_worker_gpu_02"
        )
        assert key.generation_time == 120.0
        assert key.is_match_quality_excellent is True

    def test_public_display_key(self):
        """Key for public display (no private key)."""
        key = VanityKey(
            did="did:key:z6MkPUBLICKEY",
            public_key="publiconly",
            private_key=None,
            matched_pattern="PUBLIC"
        )
        data = key.to_dict(include_private_key=False)
        assert "private_key" not in data
        assert data["public_key"] == "publiconly"


class TestKeyGenerationMetrics:
    """Test generation metrics and performance tracking."""

    def test_fast_generation(self):
        """Fast generation (easy pattern)."""
        key = VanityKey(
            did="did:key:z6MkA",
            public_key="pub",
            private_key="priv",
            matched_pattern="A",
            generation_time=0.001,
            attempts=10
        )
        assert key.generation_time < 0.01
        assert key.attempts < 100

    def test_slow_generation(self):
        """Slow generation (hard pattern)."""
        key = VanityKey(
            did="did:key:z6MkVERYLONGPATTERN",
            public_key="pub",
            private_key="priv",
            matched_pattern="VERYLONGPATTERN",
            generation_time=300.0,  # 5 minutes
            attempts=50000000
        )
        assert key.generation_time > 100
        assert key.attempts > 10000000

    def test_worker_tracking(self):
        """Worker ID tracks which compute node generated key."""
        key = VanityKey(
            did="did:key:z6MkWORKER",
            public_key="pub",
            private_key="priv",
            matched_pattern="WORKER",
            worker_id="runpod_gpu_v100_instance_42"
        )
        assert "gpu" in key.worker_id
        assert "instance_42" in key.worker_id
