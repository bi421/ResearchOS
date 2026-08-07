"""
ResearchOS Macro Intelligence Layer - Determinism & Hash Tests
Tests for MIL-DET-001 invariant: Deterministic hashes must depend only on semantic content.
"""

from datetime import date, datetime, timezone


UTC = timezone.utc


class TestNormalizedSeriesDeterminism:
    """Tests for NormalizedSeries deterministic hashing."""
    
    def _create_base_series(self) -> dict:
        """Create base series data for tests."""
        from macro_intelligence.contracts.enums import FrequencyEnum
        return {
            "series_id": "SER_20260803_001",
            "source": "fred",
            "timestamp": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "observation_period": date(2026, 8, 1),
            "release_time": datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
            "available_time": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "value": 4.25,
            "unit": "percent",
            "frequency": FrequencyEnum.DAILY,
            "quality_score": 0.95,
        }
    
    def test_identical_objects_same_hash(self):
        """Test that identical objects produce identical hashes."""
        from macro_intelligence.contracts.series import NormalizedSeries
        
        data = self._create_base_series()
        
        series1 = NormalizedSeries(**data)
        series2 = NormalizedSeries(**data)
        
        assert series1.compute_hash() == series2.compute_hash()
    
    def test_different_values_different_hash(self):
        """Test that different semantic values produce different hashes."""
        from macro_intelligence.contracts.series import NormalizedSeries
        
        data = self._create_base_series()
        
        series1 = NormalizedSeries(**data)
        data["value"] = 5.0
        series2 = NormalizedSeries(**data)
        
        assert series1.compute_hash() != series2.compute_hash()
    
    def test_different_timestamps_same_hash(self):
        """Test that different created_at timestamps don't affect hash."""
        from macro_intelligence.contracts.series import NormalizedSeries
        
        data = self._create_base_series()
        
        # Create two series with same semantic data but different created_at
        series1 = NormalizedSeries(**data, created_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC))
        series2 = NormalizedSeries(**data, created_at=datetime(2026, 8, 3, 12, 0, 1, tzinfo=UTC))
        
        # Hashes should be identical because created_at is not in hash
        assert series1.compute_hash() == series2.compute_hash()
    
    def test_serialization_deterministic(self):
        """Test that JSON serialization is deterministic."""
        from macro_intelligence.contracts.series import NormalizedSeries
        
        data = self._create_base_series()
        
        series = NormalizedSeries(**data)
        
        # Multiple serializations should produce identical output
        json1 = series.to_json()
        json2 = series.to_json()
        
        assert json1 == json2
    
    def test_roundtrip_preserves_data(self):
        """Test that deserialize(serialize(x)) == x for semantic fields."""
        from macro_intelligence.contracts.series import NormalizedSeries
        
        data = self._create_base_series()
        
        original = NormalizedSeries(**data)
        restored = NormalizedSeries.from_json(original.to_json())
        
        assert restored.series_id == original.series_id
        assert restored.value == original.value
        assert restored.to_json() == original.to_json()


class TestEvidenceObjectDeterminism:
    """Tests for EvidenceObject deterministic hashing."""
    
    def _create_base_evidence(self) -> dict:
        """Create base evidence data for tests."""
        from macro_intelligence.contracts.evidence import ProvenanceChain
        return {
            "evidence_id": "EV_20260803_001",
            "source": "fred",
            "source_quality_score": 0.95,
            "series_reference": "US10Y",
            "observation_time": datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            "release_time": datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
            "available_time": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "value": 4.25,
            "forecast": None,
            "previous": None,
            "revision": None,
            "confidence": 0.95,
            "quality_score": 0.95,
            "provenance": ProvenanceChain(
                original_source="FRED",
                ingestion_pipeline=["adapter", "validator"],
                transformation_log=[],
                verification_checks=[],
            ),
        }
    
    def test_identical_objects_same_hash(self):
        """Test that identical objects produce identical hashes."""
        from macro_intelligence.contracts.evidence import EvidenceObject
        
        data = self._create_base_evidence()
        
        evidence1 = EvidenceObject(**data)
        evidence2 = EvidenceObject(**data)
        
        assert evidence1.compute_hash() == evidence2.compute_hash()
    
    def test_different_values_different_hash(self):
        """Test that different semantic values produce different hashes."""
        from macro_intelligence.contracts.evidence import EvidenceObject
        
        data = self._create_base_evidence()
        
        evidence1 = EvidenceObject(**data)
        data["value"] = 5.0
        evidence2 = EvidenceObject(**data)
        
        assert evidence1.compute_hash() != evidence2.compute_hash()
    
    def test_different_created_at_same_hash(self):
        """Test that different created_at timestamps don't affect hash."""
        from macro_intelligence.contracts.evidence import EvidenceObject
        
        data = self._create_base_evidence()
        
        evidence1 = EvidenceObject(**data, created_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC))
        evidence2 = EvidenceObject(**data, created_at=datetime(2026, 8, 3, 12, 0, 1, tzinfo=UTC))
        
        assert evidence1.compute_hash() == evidence2.compute_hash()
    
    def test_serialization_deterministic(self):
        """Test that JSON serialization is deterministic."""
        from macro_intelligence.contracts.evidence import EvidenceObject
        
        data = self._create_base_evidence()
        
        evidence = EvidenceObject(**data)
        
        json1 = evidence.to_json()
        json2 = evidence.to_json()
        
        assert json1 == json2


class TestMacroEventDeterminism:
    """Tests for MacroEvent deterministic hashing."""
    
    def _create_base_event(self) -> dict:
        """Create base event data for tests."""
        from macro_intelligence.contracts.event import MarketRelevance
        from macro_intelligence.contracts.enums import EventCategory, ImportanceLevel
        return {
            "event_id": "EVNT_20260803_001",
            "event_type": EventCategory.DATA_RELEASE,
            "timestamp": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "source": "BLS",
            "description": "CPI release",
            "classification": "DATA_CPI",
            "importance": ImportanceLevel.HIGH,
            "related_series": ["CPI_YOY"],
            "market_relevance": MarketRelevance(
                volatility_impact=8.0,
                liquidity_impact=-2.0,
                affected_instruments=[],
                correlation_score=0.72,
            ),
        }
    
    def test_identical_objects_same_hash(self):
        """Test that identical objects produce identical hashes."""
        from macro_intelligence.contracts.event import MacroEvent
        
        data = self._create_base_event()
        
        event1 = MacroEvent(**data)
        event2 = MacroEvent(**data)
        
        assert event1.compute_hash() == event2.compute_hash()
    
    def test_different_values_different_hash(self):
        """Test that different semantic values produce different hashes."""
        from macro_intelligence.contracts.event import MacroEvent
        
        data = self._create_base_event()
        
        event1 = MacroEvent(**data)
        data["description"] = "Different description"
        event2 = MacroEvent(**data)
        
        assert event1.compute_hash() != event2.compute_hash()
    
    def test_different_created_at_same_hash(self):
        """Test that different created_at timestamps don't affect hash."""
        from macro_intelligence.contracts.event import MacroEvent
        
        data = self._create_base_event()
        
        event1 = MacroEvent(**data, created_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC))
        event2 = MacroEvent(**data, created_at=datetime(2026, 8, 3, 12, 0, 1, tzinfo=UTC))
        
        assert event1.compute_hash() == event2.compute_hash()


class TestKnowledgeObjectDeterminism:
    """Tests for KnowledgeObject deterministic hashing."""
    
    def _create_base_knowledge(self) -> dict:
        """Create base knowledge data for tests."""
        from macro_intelligence.contracts.knowledge import Pattern, StatisticalAnalysis
        from macro_intelligence.contracts.enums import PatternType
        return {
            "knowledge_id": "KN_20260803_001",
            "series_id": "US10Y",
            "date": date(2026, 8, 3),
            "evidence_refs": ["EV_20260803_001"],
            "patterns": [
                Pattern(
                    type=PatternType.TREND_ACCELERATION,
                    description="Trend accelerating",
                    confidence=0.85,
                )
            ],
            "statistics": StatisticalAnalysis(
                series_id="US10Y",
                mean=4.25,
                std=0.1,
                trend="UPWARD",
                volatility=0.5,
                observations=100,
            ),
            "confidence": 0.9,
            "explanation": "Yields trending upward",
        }
    
    def test_identical_objects_same_hash(self):
        """Test that identical objects produce identical hashes."""
        from macro_intelligence.contracts.knowledge import KnowledgeObject
        
        data = self._create_base_knowledge()
        
        knowledge1 = KnowledgeObject(**data)
        knowledge2 = KnowledgeObject(**data)
        
        assert knowledge1.compute_hash() == knowledge2.compute_hash()
    
    def test_different_values_different_hash(self):
        """Test that different semantic values produce different hashes."""
        from macro_intelligence.contracts.knowledge import KnowledgeObject
        
        data = self._create_base_knowledge()
        
        knowledge1 = KnowledgeObject(**data)
        data["confidence"] = 0.5
        knowledge2 = KnowledgeObject(**data)
        
        assert knowledge1.compute_hash() != knowledge2.compute_hash()
    
    def test_different_created_at_same_hash(self):
        """Test that different created_at timestamps don't affect hash."""
        from macro_intelligence.contracts.knowledge import KnowledgeObject
        
        data = self._create_base_knowledge()
        
        knowledge1 = KnowledgeObject(**data, created_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC))
        knowledge2 = KnowledgeObject(**data, created_at=datetime(2026, 8, 3, 12, 0, 1, tzinfo=UTC))
        
        assert knowledge1.compute_hash() == knowledge2.compute_hash()


class TestMILDET001Invariant:
    """Tests for MIL-DET-001 invariant enforcement."""
    
    def test_runtime_metadata_excluded_from_hash(self):
        """Verify that runtime metadata is excluded from hash computation."""
        from macro_intelligence.contracts.series import NormalizedSeries
        from macro_intelligence.contracts.enums import FrequencyEnum
        
        base_data = {
            "series_id": "SER_20260803_001",
            "source": "fred",
            "timestamp": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "observation_period": date(2026, 8, 1),
            "release_time": None,
            "available_time": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "value": 4.25,
            "unit": "percent",
            "frequency": FrequencyEnum.DAILY,
        }
        
        # Create multiple instances with different runtime metadata
        instances = []
        for i in range(5):
            instances.append(NormalizedSeries(
                **base_data,
                created_at=datetime(2026, 8, 3, 12, 0, i, tzinfo=UTC),
                version=f"v1.{i}",
            ))
        
        # All should have the same hash
        first_hash = instances[0].compute_hash()
        for instance in instances[1:]:
            assert instance.compute_hash() == first_hash, \
                f"Runtime metadata affected hash: {instance.created_at}"
    
    def test_semantic_changes_reflected_in_hash(self):
        """Verify that semantic changes are reflected in hash."""
        from macro_intelligence.contracts.series import NormalizedSeries
        from macro_intelligence.contracts.enums import FrequencyEnum
        
        base_data = {
            "series_id": "SER_20260803_001",
            "source": "fred",
            "timestamp": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "observation_period": date(2026, 8, 1),
            "release_time": None,
            "available_time": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "value": 4.25,
            "unit": "percent",
            "frequency": FrequencyEnum.DAILY,
        }
        
        series1 = NormalizedSeries(**base_data)
        
        # Change semantic value
        base_data["value"] = 5.0
        series2 = NormalizedSeries(**base_data)
        
        assert series1.compute_hash() != series2.compute_hash()
        
        # Change series_id
        base_data["series_id"] = "SER_20260803_002"
        series3 = NormalizedSeries(**base_data)
        
        assert series1.compute_hash() != series3.compute_hash()
        
        # Change source
        base_data["source"] = "bls"
        series4 = NormalizedSeries(**base_data)
        
        assert series1.compute_hash() != series4.compute_hash()
