"""
ResearchOS Macro Intelligence Layer - Contracts Tests
"""

from datetime import date, datetime, timezone

import pytest

UTC = timezone.utc


class TestNormalizedSeries:
    """Tests for NormalizedSeries contract."""

    def test_create_series(self):
        """Test creating a NormalizedSeries."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        series = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
            available_time=datetime(2026, 8, 12, 8, 35, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
            quality_score=0.95,
        )

        assert series.series_id == "SER_20260803_001"
        assert series.value == 4.25
        assert series.quality_score == 0.95

    def test_series_immutability(self):
        """Test that NormalizedSeries is immutable."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        series = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        # Should raise AttributeError because frozen=True
        with pytest.raises(AttributeError):
            series.value = 5.0

    def test_series_to_dict(self):
        """Test series serialization."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        series = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        data = series.to_dict()

        assert data["series_id"] == "SER_20260803_001"
        assert data["value"] == 4.25
        assert data["unit"] == "percent"

    def test_series_from_dict(self):
        """Test series deserialization."""
        from macro_intelligence.contracts.series import NormalizedSeries

        data = {
            "series_id": "SER_20260803_001",
            "source": "fred",
            "timestamp": "2026-08-03T12:00:00+00:00",
            "observation_period": "2026-08-01",
            "release_time": None,
            "available_time": "2026-08-03T12:00:00+00:00",
            "value": 4.25,
            "unit": "percent",
            "frequency": "daily",
            "quality_score": 0.95,
        }

        series = NormalizedSeries.from_dict(data)

        assert series.series_id == "SER_20260803_001"
        assert series.value == 4.25

    def test_series_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        original = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        json_str = original.to_json()
        restored = NormalizedSeries.from_json(json_str)

        assert restored.series_id == original.series_id
        assert restored.value == original.value
        assert restored.to_json() == json_str  # Deterministic

    def test_series_hash_deterministic(self):
        """Test that hash is deterministic for same data."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        # Create two identical series
        series1 = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        series2 = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        # Hashes should be identical for same data
        assert series1.compute_hash() == series2.compute_hash()

    def test_series_validate(self):
        """Test series validation."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        # Valid series
        series = NormalizedSeries(
            series_id="SER_20260803_001",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        is_valid, errors = series.validate()
        assert is_valid
        assert len(errors) == 0

    def test_series_validate_invalid_id(self):
        """Test series validation with invalid ID."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        from macro_intelligence.contracts.series import NormalizedSeries

        series = NormalizedSeries(
            series_id="INVALID_ID",
            source="fred",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            observation_period=date(2026, 8, 1),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            unit="percent",
            frequency=FrequencyEnum.DAILY,
        )

        is_valid, errors = series.validate()
        assert not is_valid
        assert any("series_id" in e for e in errors)


class TestEvidenceObject:
    """Tests for EvidenceObject contract."""

    def test_create_evidence(self):
        """Test creating an EvidenceObject."""
        from macro_intelligence.contracts.evidence import EvidenceObject, ProvenanceChain

        evidence = EvidenceObject(
            evidence_id="EV_20260803_001",
            source="fred",
            source_quality_score=0.95,
            series_reference="US10Y",
            observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            release_time=datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
            available_time=datetime(2026, 8, 12, 8, 35, tzinfo=UTC),
            value=4.25,
            forecast=None,
            previous=None,
            revision=None,
            confidence=0.95,
            quality_score=0.95,
            provenance=ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter", "validator"],
                transformation_log=[],
                verification_checks=[],
            ),
        )

        assert evidence.evidence_id == "EV_20260803_001"
        assert evidence.value == 4.25
        assert evidence.confidence == 0.95

    def test_evidence_immutability(self):
        """Test that EvidenceObject is immutable."""
        from macro_intelligence.contracts.evidence import EvidenceObject, ProvenanceChain

        evidence = EvidenceObject(
            evidence_id="EV_20260803_001",
            source="fred",
            source_quality_score=0.95,
            series_reference="US10Y",
            observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            forecast=None,
            previous=None,
            revision=None,
            confidence=0.95,
            quality_score=0.95,
            provenance=ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter"],
                transformation_log=[],
                verification_checks=[],
            ),
        )

        with pytest.raises(AttributeError):
            evidence.value = 5.0

    def test_evidence_json_roundtrip(self):
        """Test evidence JSON serialization roundtrip."""
        from macro_intelligence.contracts.evidence import EvidenceObject, ProvenanceChain

        original = EvidenceObject(
            evidence_id="EV_20260803_001",
            source="fred",
            source_quality_score=0.95,
            series_reference="US10Y",
            observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            forecast=None,
            previous=None,
            revision=None,
            confidence=0.95,
            quality_score=0.95,
            provenance=ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter"],
                transformation_log=[],
                verification_checks=[],
            ),
        )

        json_str = original.to_json()
        restored = EvidenceObject.from_json(json_str)

        assert restored.evidence_id == original.evidence_id
        assert restored.value == original.value
        assert restored.to_json() == json_str

    def test_evidence_hash_deterministic(self):
        """Test that evidence hash is deterministic."""
        from macro_intelligence.contracts.evidence import EvidenceObject, ProvenanceChain

        evidence1 = EvidenceObject(
            evidence_id="EV_20260803_001",
            source="fred",
            source_quality_score=0.95,
            series_reference="US10Y",
            observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            forecast=None,
            previous=None,
            revision=None,
            confidence=0.95,
            quality_score=0.95,
            provenance=ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter"],
                transformation_log=[],
                verification_checks=[],
            ),
        )

        evidence2 = EvidenceObject(
            evidence_id="EV_20260803_001",
            source="fred",
            source_quality_score=0.95,
            series_reference="US10Y",
            observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            forecast=None,
            previous=None,
            revision=None,
            confidence=0.95,
            quality_score=0.95,
            provenance=ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter"],
                transformation_log=[],
                verification_checks=[],
            ),
        )

        assert evidence1.compute_hash() == evidence2.compute_hash()

    def test_evidence_validate(self):
        """Test evidence validation."""
        from macro_intelligence.contracts.evidence import EvidenceObject, ProvenanceChain

        evidence = EvidenceObject(
            evidence_id="EV_20260803_001",
            source="fred",
            source_quality_score=0.95,
            series_reference="US10Y",
            observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            release_time=None,
            available_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            forecast=None,
            previous=None,
            revision=None,
            confidence=0.95,
            quality_score=0.95,
            provenance=ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter"],
                transformation_log=[],
                verification_checks=[],
            ),
        )

        is_valid, errors = evidence.validate()
        assert is_valid
        assert len(errors) == 0


class TestMacroEvent:
    """Tests for MacroEvent contract."""

    def test_create_event(self):
        """Test creating a MacroEvent."""
        from macro_intelligence.contracts.enums import EventCategory, ImportanceLevel
        from macro_intelligence.contracts.event import MacroEvent, MarketRelevance

        event = MacroEvent(
            event_id="EVNT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            source="BLS",
            description="CPI release",
            classification="DATA_CPI",
            importance=ImportanceLevel.HIGH,
            related_series=["CPI_YOY", "CPI_CORE_YOY"],
            market_relevance=MarketRelevance(
                volatility_impact=8.0,
                liquidity_impact=-2.0,
                affected_instruments=["TLT", "SPY"],
                correlation_score=0.72,
            ),
        )

        assert event.event_id == "EVNT_20260803_001"
        assert event.importance == ImportanceLevel.HIGH

    def test_event_immutability(self):
        """Test that MacroEvent is immutable."""
        from macro_intelligence.contracts.enums import EventCategory, ImportanceLevel
        from macro_intelligence.contracts.event import MacroEvent, MarketRelevance

        event = MacroEvent(
            event_id="EVNT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            source="BLS",
            description="CPI release",
            classification="DATA_CPI",
            importance=ImportanceLevel.HIGH,
            related_series=["CPI_YOY"],
            market_relevance=MarketRelevance(
                volatility_impact=8.0,
                liquidity_impact=-2.0,
                affected_instruments=[],
                correlation_score=0.72,
            ),
        )

        with pytest.raises(AttributeError):
            event.description = "Modified"

    def test_event_json_roundtrip(self):
        """Test event JSON serialization roundtrip."""
        from macro_intelligence.contracts.enums import EventCategory, ImportanceLevel
        from macro_intelligence.contracts.event import MacroEvent, MarketRelevance

        original = MacroEvent(
            event_id="EVNT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            source="BLS",
            description="CPI release",
            classification="DATA_CPI",
            importance=ImportanceLevel.HIGH,
            related_series=["CPI_YOY"],
            market_relevance=MarketRelevance(
                volatility_impact=8.0,
                liquidity_impact=-2.0,
                affected_instruments=[],
                correlation_score=0.72,
            ),
        )

        json_str = original.to_json()
        restored = MacroEvent.from_json(json_str)

        assert restored.event_id == original.event_id
        assert restored.to_json() == json_str

    def test_event_hash_deterministic(self):
        """Test that event hash is deterministic."""
        from macro_intelligence.contracts.enums import EventCategory, ImportanceLevel
        from macro_intelligence.contracts.event import MacroEvent, MarketRelevance

        event1 = MacroEvent(
            event_id="EVNT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            source="BLS",
            description="CPI release",
            classification="DATA_CPI",
            importance=ImportanceLevel.HIGH,
            related_series=["CPI_YOY"],
            market_relevance=MarketRelevance(
                volatility_impact=8.0,
                liquidity_impact=-2.0,
                affected_instruments=[],
                correlation_score=0.72,
            ),
        )

        event2 = MacroEvent(
            event_id="EVNT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            source="BLS",
            description="CPI release",
            classification="DATA_CPI",
            importance=ImportanceLevel.HIGH,
            related_series=["CPI_YOY"],
            market_relevance=MarketRelevance(
                volatility_impact=8.0,
                liquidity_impact=-2.0,
                affected_instruments=[],
                correlation_score=0.72,
            ),
        )

        assert event1.compute_hash() == event2.compute_hash()


class TestRegistry:
    """Tests for series registry."""

    def test_get_series_metadata(self):
        """Test getting series metadata."""
        from macro_intelligence.contracts.registry import get_series_metadata

        metadata = get_series_metadata("US10Y")
        assert metadata is not None
        assert metadata["name"] == "US Treasury 10-Year Yield"

    def test_is_supported_series(self):
        """Test series support check."""
        from macro_intelligence.contracts.registry import is_supported_series

        assert is_supported_series("US10Y") is True
        assert is_supported_series("INVALID") is False

    def test_get_all_series_ids(self):
        """Test getting all series IDs."""
        from macro_intelligence.contracts.registry import get_all_series_ids

        series_ids = get_all_series_ids()
        assert "US10Y" in series_ids
        assert "CPI_YOY" in series_ids
        assert len(series_ids) > 0

    def test_series_ranges(self):
        """Test series ranges."""
        from macro_intelligence.contracts.registry import SERIES_RANGES

        assert "US10Y" in SERIES_RANGES
        assert SERIES_RANGES["US10Y"] == (-5.0, 20.0)


class TestEnums:
    """Tests for enums."""

    def test_frequency_enum(self):
        """Test FrequencyEnum."""
        from macro_intelligence.contracts.enums import FrequencyEnum

        assert FrequencyEnum.DAILY.value == "daily"
        assert FrequencyEnum.MONTHLY.value == "monthly"

    def test_importance_enum(self):
        """Test ImportanceLevel enum."""
        from macro_intelligence.contracts.enums import ImportanceLevel

        assert ImportanceLevel.HIGH.value == "high"

    def test_event_category_enum(self):
        """Test EventCategory enum."""
        from macro_intelligence.contracts.enums import EventCategory

        assert EventCategory.FOMC_MEETING.value == "fomc_meeting"
