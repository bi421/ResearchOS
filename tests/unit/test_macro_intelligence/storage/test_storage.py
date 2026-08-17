"""
ResearchOS Macro Intelligence Layer - Storage Tests
"""

from pathlib import Path


class TestParquetStore:
    """Tests for ParquetStore."""

    def test_init_creates_directories(self, tmp_path: Path):
        """Test that initialization creates directories."""
        from macro_intelligence.storage.skeleton import ParquetStore

        store = ParquetStore(root_path=str(tmp_path / "parquet"))

        assert store.root_path.exists()
        assert (store.root_path / "v1").exists()

    def test_health_returns_dict(self, tmp_path: Path):
        """Test health method returns dict."""
        from macro_intelligence.storage.skeleton import ParquetStore

        store = ParquetStore(root_path=str(tmp_path / "parquet"))
        health = store.get_health()

        assert isinstance(health, dict)
        assert health["status"] == "healthy"
        assert health["type"] == "parquet"


class TestJsonStore:
    """Tests for JsonStore."""

    def test_init_creates_directories(self, tmp_path: Path):
        """Test that initialization creates directories."""
        from macro_intelligence.storage.skeleton import JsonStore

        store = JsonStore(root_path=str(tmp_path / "json"))

        assert store.root_path.exists()
        assert (store.root_path / "events").exists()
        assert (store.root_path / "evidence").exists()
        assert (store.root_path / "knowledge").exists()
        assert (store.root_path / "reactions").exists()

    def test_health_returns_dict(self, tmp_path: Path):
        """Test health method returns dict."""
        from macro_intelligence.storage.skeleton import JsonStore

        store = JsonStore(root_path=str(tmp_path / "json"))
        health = store.get_health()

        assert isinstance(health, dict)
        assert health["status"] == "healthy"
        assert health["type"] == "json"


class TestStorageIntegrity:
    """Tests for storage integrity."""

    def test_parquet_integrity(self, tmp_path: Path):
        """Test ParquetStore integrity check."""
        from macro_intelligence.storage.skeleton import ParquetStore

        store = ParquetStore(root_path=str(tmp_path / "parquet"))
        assert store.verify_integrity() is True

    def test_json_integrity(self, tmp_path: Path):
        """Test JsonStore integrity check."""
        from macro_intelligence.storage.skeleton import JsonStore

        store = JsonStore(root_path=str(tmp_path / "json"))
        assert store.verify_integrity() is True
