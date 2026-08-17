"""
ResearchOS Macro Intelligence Layer - Feature Engineering Tests
"""

from datetime import datetime, timezone

import pytest

UTC = timezone.utc


class TestFeatureDefinition:
    """Tests for FeatureDefinition."""

    def test_create_feature_definition(self):
        """Test creating a feature definition."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
            parameters={"window": 30},
            description="30-day rolling mean of CPI",
            unit="percent",
        )

        assert definition.feature_id == "FEAT_TREND_001"
        assert definition.category == FeatureCategory.INFLATION
        assert definition.method == CalculationMethod.ROLLING

    def test_feature_definition_immutability(self):
        """Test that feature definition is immutable."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        with pytest.raises(AttributeError):
            definition.feature_name = "Modified"

    def test_feature_definition_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        original = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
            parameters={"window": 30},
            description="30-day rolling mean of CPI",
            unit="percent",
        )

        json_str = original.to_json()
        restored = FeatureDefinition.from_json(json_str)

        assert restored.feature_id == original.feature_id
        assert restored.to_json() == json_str

    def test_feature_definition_hash_deterministic(self):
        """Test that hash is deterministic."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        def1 = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        def2 = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        assert def1.compute_hash() == def2.compute_hash()

    def test_feature_definition_validate(self):
        """Test feature definition validation."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        is_valid, errors = definition.validate()
        assert is_valid
        assert len(errors) == 0

    def test_feature_definition_validate_invalid_id(self):
        """Test feature definition validation with invalid ID."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        definition = FeatureDefinition(
            feature_id="INVALID",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        is_valid, errors = definition.validate()
        assert not is_valid
        assert any("feature_id" in e for e in errors)

    def test_feature_definition_requires_history(self):
        """Test history requirement detection."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        # Rolling calculation requires history
        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        assert definition.requires_history() is True

        # Point calculation doesn't require history
        definition_point = FeatureDefinition(
            feature_id="FEAT_POINT_001",
            feature_name="CPI Point",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.POINT,
        )

        assert definition_point.requires_history() is False


class TestFeatureValue:
    """Tests for FeatureValue."""

    def test_create_feature_value(self):
        """Test creating a feature value."""
        from macro_intelligence.features.definitions import FeatureValue

        value = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            quality_score=0.95,
        )

        assert value.feature_id == "FEAT_TREND_001"
        assert value.value == 4.25
        assert value.quality_score == 0.95

    def test_feature_value_immutability(self):
        """Test that feature value is immutable."""
        from macro_intelligence.features.definitions import FeatureValue

        value = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            quality_score=0.95,
        )

        with pytest.raises(AttributeError):
            value.value = 5.0

    def test_feature_value_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.features.definitions import FeatureValue

        original = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            quality_score=0.95,
        )

        json_str = original.to_json()
        restored = FeatureValue.from_json(json_str)

        assert restored.feature_id == original.feature_id
        assert restored.value == original.value
        assert restored.to_json() == json_str

    def test_feature_value_hash_deterministic(self):
        """Test that hash is deterministic."""
        from macro_intelligence.features.definitions import FeatureValue

        val1 = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            quality_score=0.95,
        )

        val2 = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            quality_score=0.95,
        )

        assert val1.compute_hash() == val2.compute_hash()


class TestFeatureVector:
    """Tests for FeatureVector."""

    def test_create_feature_vector(self):
        """Test creating a feature vector."""
        from macro_intelligence.features.definitions import FeatureVector

        vector = FeatureVector(
            vector_id="VEC_20260803_120000",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        assert vector.vector_id == "VEC_20260803_120000"
        assert len(vector.features) == 0

    def test_add_feature(self):
        """Test adding a feature to vector."""
        from macro_intelligence.features.definitions import FeatureValue, FeatureVector

        vector = FeatureVector(
            vector_id="VEC_20260803_120000",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        feature = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
        )

        new_vector = vector.add_feature(feature)

        assert len(new_vector.features) == 1
        assert "FEAT_TREND_001" in new_vector.features
        assert len(vector.features) == 0  # Original unchanged

    def test_get_feature(self):
        """Test getting a feature from vector."""
        from macro_intelligence.features.definitions import FeatureValue, FeatureVector

        vector = FeatureVector(
            vector_id="VEC_20260803_120000",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        feature = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
        )

        vector = vector.add_feature(feature)

        retrieved = vector.get_feature("FEAT_TREND_001")
        assert retrieved is not None
        assert retrieved.value == 4.25

    def test_feature_vector_immutability(self):
        """Test that feature vector is immutable."""
        from macro_intelligence.features.definitions import FeatureValue, FeatureVector

        vector = FeatureVector(
            vector_id="VEC_20260803_120000",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        feature = FeatureValue(
            feature_id="FEAT_TREND_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
        )

        vector = vector.add_feature(feature)

        with pytest.raises(AttributeError):
            vector.features["FEAT_TREND_001"].value = 5.0


class TestFeatureRegistry:
    """Tests for FeatureRegistry."""

    def test_register_feature(self):
        """Test registering a feature."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )
        from macro_intelligence.features.registry import FeatureRegistry

        registry = FeatureRegistry()

        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        registry.register(definition, description="30-day rolling mean", unit="percent")

        retrieved = registry.get("FEAT_TREND_001")
        assert retrieved is not None
        assert retrieved.feature_id == "FEAT_TREND_001"

    def test_get_by_category(self):
        """Test getting features by category."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )
        from macro_intelligence.features.registry import FeatureRegistry

        registry = FeatureRegistry()

        # Register features in different categories
        for i in range(3):
            definition = FeatureDefinition(
                feature_id=f"FEAT_TREND_{i:03d}",
                feature_name=f"Trend {i}",
                category=FeatureCategory.INFLATION,
                feature_type=FeatureType.SCALAR,
                method=CalculationMethod.ROLLING,
            )
            registry.register(definition)

        # Get inflation features
        inflation_features = registry.get_by_category(FeatureCategory.INFLATION)
        assert len(inflation_features) == 3

    def test_get_dependency_graph(self):
        """Test getting dependency graph."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )
        from macro_intelligence.features.registry import FeatureRegistry

        registry = FeatureRegistry()

        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
            required_evidence=["EVD_CPI_001"],
            prerequisite_features=["FEAT_RAW_001"],
        )

        registry.register(definition)

        graph = registry.get_dependency_graph()
        assert "FEAT_TREND_001" in graph
        assert "EVD_CPI_001" in graph["FEAT_TREND_001"]
        assert "FEAT_RAW_001" in graph["FEAT_TREND_001"]

    def test_increment_calculation_count(self):
        """Test incrementing calculation count."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )
        from macro_intelligence.features.registry import FeatureRegistry

        registry = FeatureRegistry()

        definition = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
        )

        registry.register(definition)

        # Increment count
        registry.increment_calculation_count("FEAT_TREND_001")
        registry.increment_calculation_count("FEAT_TREND_001")

        # Check metadata
        metadata = registry.get_metadata("FEAT_TREND_001")
        assert metadata.calculation_count == 2

    def test_get_statistics(self):
        """Test getting registry statistics."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )
        from macro_intelligence.features.registry import FeatureRegistry

        registry = FeatureRegistry()

        # Register some features
        for i in range(3):
            definition = FeatureDefinition(
                feature_id=f"FEAT_TREND_{i:03d}",
                feature_name=f"Trend {i}",
                category=FeatureCategory.INFLATION,
                feature_type=FeatureType.SCALAR,
                method=CalculationMethod.ROLLING,
            )
            registry.register(definition)

        stats = registry.get_statistics()

        assert stats["total_features"] == 3
        assert stats["features_by_category"]["inflation"] == 3


class TestMILFeatInvariants:
    """Tests for MIL-FEAT invariants."""

    def test_mil_feat_001_deterministic(self):
        """MIL-FEAT-001: Features are deterministic functions of evidence."""
        from macro_intelligence.features.definitions import FeatureDefinition
        from macro_intelligence.features.enums import (
            CalculationMethod,
            FeatureCategory,
            FeatureType,
        )

        # Create two identical definitions
        def1 = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
            parameters={"window": 30},
        )

        def2 = FeatureDefinition(
            feature_id="FEAT_TREND_001",
            feature_name="CPI Trend",
            category=FeatureCategory.INFLATION,
            feature_type=FeatureType.SCALAR,
            method=CalculationMethod.ROLLING,
            parameters={"window": 30},
        )

        # Hashes should be identical
        assert def1.compute_hash() == def2.compute_hash()

    def test_mil_feat_002_immutable_vector(self):
        """MIL-FEAT-002: Feature vectors are immutable."""
        from macro_intelligence.features.definitions import FeatureValue, FeatureVector

        vector = FeatureVector(
            vector_id="VEC_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        feature = FeatureValue(
            feature_id="FEAT_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
        )

        vector = vector.add_feature(feature)

        # Should not be able to modify
        with pytest.raises(AttributeError):
            vector.features["FEAT_001"].value = 5.0

    def test_mil_feat_005_reproducible(self):
        """MIL-FEAT-005: Feature vectors are reproducible."""
        from macro_intelligence.features.definitions import FeatureValue, FeatureVector

        # Create two identical vectors
        vector1 = FeatureVector(
            vector_id="VEC_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        vector2 = FeatureVector(
            vector_id="VEC_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        # Add same feature to both
        feature = FeatureValue(
            feature_id="FEAT_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
        )

        vector1 = vector1.add_feature(feature)
        vector2 = vector2.add_feature(feature)

        # Hashes should be identical
        assert vector1.compute_hash() == vector2.compute_hash()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
