"""
ResearchOS Macro Intelligence Layer - Test Configuration
"""

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

# UTC timezone for all tests
UTC = timezone.utc


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Create temporary test data directory."""
    test_dir = tmp_path / "macro_test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_series_id() -> str:
    """Sample series ID."""
    return "SER_20260803_001"


@pytest.fixture
def sample_evidence_id() -> str:
    """Sample evidence ID."""
    return "EV_20260803_001"


@pytest.fixture
def sample_event_id() -> str:
    """Sample event ID."""
    return "EVNT_20260803_001"


@pytest.fixture
def sample_timestamp() -> datetime:
    """Sample timestamp."""
    return datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_date() -> date:
    """Sample date."""
    return date(2026, 8, 3)


@pytest.fixture
def sample_provenance():
    """Sample provenance chain."""
    from macro_intelligence.contracts.evidence import ProvenanceChain

    return ProvenanceChain(
        original_source="FRED",
        ingestion_pipeline=["adapter", "validator"],
        transformation_log=[],
        verification_checks=[],
    )
