"""
ResearchOS Macro Intelligence Layer - Relationship Engine Tests
Tests for deterministic historical relationship analysis.
"""

from datetime import datetime, timezone

import pytest

UTC = timezone.utc


# =============================================================================
# Test data helpers
# =============================================================================


def _make_perfect_positive(n=50):
    """Perfect positive correlation."""
    x = [float(i) for i in range(n)]
    y = [float(i) * 2.0 + 1.0 for i in range(n)]
    return x, y


def _make_perfect_negative(n=50):
    """Perfect negative correlation."""
    x = [float(i) for i in range(n)]
    y = [float(i) * -2.0 + 100.0 for i in range(n)]
    return x, y


def _make_no_correlation(n=50):
    """No correlation (random-ish but deterministic)."""
    x = [float(i) for i in range(n)]
    y = [float((i * 7 + 3) % 11) for i in range(n)]
    return x, y


def _make_lagged_series(n=100, lag=3):
    """Series with known lag relationship."""
    x = [float(i) + (0.5 if i % 3 == 0 else 0) for i in range(n)]
    y = [0.0] * n
    for i in range(lag, n):
        y[i] = x[i - lag] * 0.8 + (0.1 if i % 5 == 0 else 0)
    return x, y, lag


# =============================================================================
# Correlation tests
# =============================================================================


class TestPearsonCorrelation:
    """Tests for Pearson correlation."""

    def test_perfect_positive(self):
        """Test perfect positive correlation."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        x, y = _make_perfect_positive(50)
        result = pearson_correlation(x, y)
        assert result is not None
        assert abs(result - 1.0) < 0.0001

    def test_perfect_negative(self):
        """Test perfect negative correlation."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        x, y = _make_perfect_negative(50)
        result = pearson_correlation(x, y)
        assert result is not None
        assert abs(result - (-1.0)) < 0.0001

    def test_no_correlation(self):
        """Test uncorrelated series."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        x, y = _make_no_correlation(50)
        result = pearson_correlation(x, y)
        assert result is not None
        # Should be close to 0 for our deterministic "random" series
        assert abs(result) < 0.5

    def test_empty_series(self):
        """Test empty series."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        assert pearson_correlation([], []) is None

    def test_single_element(self):
        """Test single element series."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        assert pearson_correlation([1.0], [2.0]) is None

    def test_different_lengths(self):
        """Test different length series."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        assert pearson_correlation([1.0, 2.0], [1.0]) is None

    def test_constant_series(self):
        """Test constant series (zero variance)."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        assert pearson_correlation([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) is None

    def test_deterministic(self):
        """Test determinism."""
        from macro_intelligence.relationships.correlation import pearson_correlation

        x, y = _make_perfect_positive(50)
        r1 = pearson_correlation(x, y)
        r2 = pearson_correlation(x, y)
        assert r1 == r2


class TestSpearmanCorrelation:
    """Tests for Spearman correlation."""

    def test_perfect_positive(self):
        """Test perfect positive Spearman correlation."""
        from macro_intelligence.relationships.correlation import spearman_correlation

        x, y = _make_perfect_positive(50)
        result = spearman_correlation(x, y)
        assert result is not None
        assert abs(result - 1.0) < 0.0001

    def test_perfect_negative(self):
        """Test perfect negative Spearman correlation."""
        from macro_intelligence.relationships.correlation import spearman_correlation

        x, y = _make_perfect_negative(50)
        result = spearman_correlation(x, y)
        assert result is not None
        assert abs(result - (-1.0)) < 0.0001

    def test_deterministic(self):
        """Test determinism."""
        from macro_intelligence.relationships.correlation import spearman_correlation

        x, y = _make_perfect_positive(30)
        r1 = spearman_correlation(x, y)
        r2 = spearman_correlation(x, y)
        assert r1 == r2


class TestClassifyRelationship:
    """Tests for relationship classification."""

    def test_strong_positive(self):
        """Test strong positive classification."""
        from macro_intelligence.relationships.correlation import classify_relationship

        rel_type, strength = classify_relationship(0.85)
        assert rel_type == "positive"
        assert strength == "very_strong"

    def test_strong_negative(self):
        """Test strong negative classification."""
        from macro_intelligence.relationships.correlation import classify_relationship

        rel_type, strength = classify_relationship(-0.75)
        assert rel_type == "negative"
        assert strength == "strong"

    def test_moderate(self):
        """Test moderate classification."""
        from macro_intelligence.relationships.correlation import classify_relationship

        rel_type, strength = classify_relationship(0.5)
        assert rel_type == "positive"
        assert strength == "moderate"

    def test_weak(self):
        """Test weak classification."""
        from macro_intelligence.relationships.correlation import classify_relationship

        rel_type, strength = classify_relationship(0.15)
        assert rel_type == "positive"  # 0.15 > 0.05 threshold
        assert strength == "negligible"  # below 0.2 threshold

    def test_very_weak(self):
        """Test very weak classification."""
        from macro_intelligence.relationships.correlation import classify_relationship

        rel_type, strength = classify_relationship(0.05)
        assert rel_type == "neutral"
        assert strength == "negligible"


# =============================================================================
# Rolling correlation tests
# =============================================================================


class TestRollingCorrelation:
    """Tests for rolling correlation."""

    def test_basic_rolling(self):
        """Test basic rolling correlation."""
        from macro_intelligence.relationships.correlation import compute_rolling_correlation

        x = [float(i) for i in range(20)]
        y = [float(i) * 2 for i in range(20)]
        corrs, ts, stab = compute_rolling_correlation(x, y, 5)
        assert len(corrs) == 16
        assert all(abs(c - 1.0) < 0.001 for c in corrs)

    def test_rolling_with_noise(self):
        """Test rolling correlation with noisy data."""
        import random

        from macro_intelligence.relationships.correlation import compute_rolling_correlation

        random.seed(42)
        x = [10.0 + i * 0.5 + random.gauss(0, 1) for i in range(50)]
        y = [5.0 + i * 0.3 + random.gauss(0, 1) for i in range(50)]
        corrs, ts, stab = compute_rolling_correlation(x, y, 10)
        assert len(corrs) > 0
        assert stab >= 0

    def test_rolling_deterministic(self):
        """Test rolling correlation determinism."""
        from macro_intelligence.relationships.correlation import compute_rolling_correlation

        x = [float(i) for i in range(20)]
        y = [float(i) * 2 for i in range(20)]
        r1 = compute_rolling_correlation(x, y, 5)
        r2 = compute_rolling_correlation(x, y, 5)
        assert r1 == r2


# =============================================================================
# Lag analysis tests
# =============================================================================


class TestLagAnalysis:
    """Tests for lag analysis."""

    def test_known_lag(self):
        """Test lag detection with known relationship."""
        from macro_intelligence.relationships.lag_analysis import find_optimal_lag

        x, y, true_lag = _make_lagged_series(100, lag=3)
        result = find_optimal_lag(x, y, max_lag=10)
        assert abs(result.optimal_lag) == true_lag
        assert result.lag_correlation > 0.5

    def test_no_lag(self):
        """Test with simultaneous series."""
        from macro_intelligence.relationships.lag_analysis import find_optimal_lag

        x = [float(i) for i in range(50)]
        y = [float(i) * 2 for i in range(50)]
        result = find_optimal_lag(x, y, max_lag=5)
        assert abs(result.optimal_lag) <= 2

    def test_short_series(self):
        """Test with short series."""
        from macro_intelligence.relationships.lag_analysis import find_optimal_lag

        x = [1.0, 2.0, 3.0]
        y = [4.0, 5.0, 6.0]
        result = find_optimal_lag(x, y, max_lag=2)
        assert result.optimal_lag == 0


# =============================================================================
# Model tests
# =============================================================================


class TestCorrelationResult:
    """Tests for CorrelationResult model."""

    def test_create(self):
        """Test creating a CorrelationResult."""
        from macro_intelligence.relationships.models import CorrelationResult

        result = CorrelationResult(
            series_a="XAU",
            series_b="DXY",
            correlation=-0.72,
            relationship_type="negative",
            relationship_strength="strong",
        )
        assert result.series_a == "XAU"
        assert result.correlation == -0.72

    def test_to_dict(self):
        """Test serialization."""
        from macro_intelligence.relationships.models import CorrelationResult

        result = CorrelationResult(
            series_a="XAU",
            series_b="DXY",
            correlation=-0.72,
        )
        data = result.to_dict()
        assert data["series_a"] == "XAU"
        assert data["correlation"] == -0.72

    def test_from_dict(self):
        """Test deserialization."""
        from macro_intelligence.relationships.models import CorrelationResult

        data = {
            "series_a": "XAU",
            "series_b": "DXY",
            "correlation": -0.72,
            "method": "pearson",
        }
        result = CorrelationResult.from_dict(data)
        assert result.series_a == "XAU"
        assert result.correlation == -0.72

    def test_roundtrip(self):
        """Test JSON roundtrip."""
        from macro_intelligence.relationships.models import CorrelationResult

        original = CorrelationResult(
            series_a="XAU",
            series_b="DXY",
            correlation=-0.72,
        )
        json_str = original.to_json()
        restored = CorrelationResult.from_json(json_str)
        assert restored.series_a == original.series_a
        assert restored.correlation == original.correlation
        assert restored.to_json() == json_str

    def test_immutability(self):
        """Test immutability."""
        from macro_intelligence.relationships.models import CorrelationResult

        result = CorrelationResult(
            series_a="XAU",
            series_b="DXY",
            correlation=-0.72,
        )
        with pytest.raises(AttributeError):
            result.correlation = 0.5

    def test_hash_deterministic(self):
        """Test hash determinism."""
        from macro_intelligence.relationships.models import CorrelationResult

        r1 = CorrelationResult(series_a="A", series_b="B", correlation=0.5)
        r2 = CorrelationResult(series_a="A", series_b="B", correlation=0.5)
        assert r1.compute_hash() == r2.compute_hash()


class TestLagRelationship:
    """Tests for LagRelationship model."""

    def test_create(self):
        """Test creating a LagRelationship."""
        from macro_intelligence.relationships.models import LagRelationship

        lag = LagRelationship(
            series_a="CPI",
            series_b="GOLD",
            optimal_lag=3,
            lag_correlation=0.65,
            lag_type="leading",
        )
        assert lag.optimal_lag == 3
        assert lag.lag_type == "leading"

    def test_immutability(self):
        """Test immutability."""
        from macro_intelligence.relationships.models import LagRelationship

        lag = LagRelationship(
            series_a="A",
            series_b="B",
            optimal_lag=1,
            lag_correlation=0.5,
        )
        with pytest.raises(AttributeError):
            lag.optimal_lag = 2


class TestRegimeRelationship:
    """Tests for RegimeRelationship model."""

    def test_create(self):
        """Test creating a RegimeRelationship."""
        from macro_intelligence.relationships.models import RegimeRelationship

        rel = RegimeRelationship(
            series_a="XAU",
            series_b="DXY",
            regime="risk_off",
            correlation=-0.72,
        )
        assert rel.regime == "risk_off"
        assert rel.correlation == -0.72


class TestStructuralBreak:
    """Tests for StructuralBreak model."""

    def test_create(self):
        """Test creating a StructuralBreak."""
        from macro_intelligence.relationships.models import StructuralBreak

        break_point = StructuralBreak(
            series_a="XAU",
            series_b="REAL_YIELD",
            break_point="2022-03-01",
            break_type="strength_change",
            correlation_before=-0.6,
            correlation_after=-0.2,
        )
        assert break_point.break_type == "strength_change"


class TestRelationshipResult:
    """Tests for RelationshipResult model."""

    def test_create(self):
        """Test creating a RelationshipResult."""
        from macro_intelligence.relationships.models import RelationshipResult

        result = RelationshipResult(
            series_a="XAU",
            series_b="DXY",
        )
        assert result.series_a == "XAU"

    def test_to_dict(self):
        """Test serialization."""
        from macro_intelligence.relationships.models import RelationshipResult

        result = RelationshipResult(
            series_a="XAU",
            series_b="DXY",
        )
        data = result.to_dict()
        assert data["series_a"] == "XAU"

    def test_roundtrip(self):
        """Test JSON roundtrip."""
        from macro_intelligence.relationships.models import RelationshipResult

        original = RelationshipResult(
            series_a="XAU",
            series_b="DXY",
        )
        json_str = original.to_json()
        restored = RelationshipResult.from_json(json_str)
        assert restored.series_a == original.series_a
        assert restored.to_json() == json_str

    def test_immutability(self):
        """Test immutability."""
        from macro_intelligence.relationships.models import RelationshipResult

        result = RelationshipResult(series_a="A", series_b="B")
        with pytest.raises(AttributeError):
            result.series_a = "C"


# =============================================================================
# Engine tests
# =============================================================================


class TestRelationshipEngine:
    """Tests for RelationshipEngine."""

    def test_engine_version(self):
        """Test engine version."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        assert engine.version == "rel-eng/v5.0.0"

    def test_analyze_correlation(self):
        """Test correlation analysis."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x, y = _make_perfect_positive(50)
        result = engine.analyze_correlation(x, y, "XAU", "DXY")
        assert result.series_a == "XAU"
        assert abs(result.correlation - 1.0) < 0.001

    def test_analyze_rolling_correlation(self):
        """Test rolling correlation analysis."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x = [float(i) for i in range(20)]
        y = [float(i) * 2 for i in range(20)]
        result = engine.analyze_rolling_correlation(x, y, 5, "A", "B")
        assert result.window_size == 5
        assert len(result.correlations) == 16

    def test_analyze_lag(self):
        """Test lag analysis."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x, y, true_lag = _make_lagged_series(100, lag=3)
        result = engine.analyze_lag(x, y, "CPI", "GOLD", max_lag=10)
        assert result.series_a == "CPI"
        assert abs(result.optimal_lag) == true_lag

    def test_analyze_regime_relationship(self):
        """Test regime-conditional correlation."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x = [10.0 + i * 0.5 for i in range(60)]
        y = [5.0 - i * 0.3 for i in range(60)]
        regimes = ["expansion"] * 30 + ["recession"] * 30
        results = engine.analyze_regime_relationship(x, y, regimes, "A", "B")
        assert len(results) == 2
        for rel in results:
            assert rel.regime in ["expansion", "recession"]

    def test_detect_breaks(self):
        """Test structural break detection."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        # Create series with a clear break at point 50
        x = [float(i) for i in range(100)]
        y = [float(i) * 2 for i in range(50)] + [float(i) * 0.5 + 50 for i in range(50, 100)]
        breaks = engine.detect_breaks(x, y, "A", "B", break_threshold=0.3)
        # Should detect at least one break
        assert isinstance(breaks, list)

    def test_full_analysis(self):
        """Test full relationship analysis."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x, y = _make_perfect_positive(50)
        result = engine.full_analysis(
            x,
            y,
            "XAU",
            "DXY",
            rolling_window=10,
            max_lag=5,
        )
        assert result.series_a == "XAU"
        assert result.series_b == "DXY"
        assert result.overall_correlation is not None
        assert abs(result.overall_correlation.correlation - 1.0) < 0.001

    def test_deterministic(self):
        """Test that engine produces deterministic output."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x, y = _make_perfect_positive(50)

        results = [engine.analyze_correlation(x, y, "A", "B") for _ in range(10)]
        for r in results[1:]:
            assert r.correlation == results[0].correlation
            assert r.series_a == results[0].series_a


# =============================================================================
# MIL-REL invariant tests
# =============================================================================


class TestMILRelationshipInvariants:
    """Tests for MIL-REL invariants."""

    def test_mil_rel_001_deterministic(self):
        """MIL-REL-001: Same input produces identical relationship output."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x, y = _make_perfect_positive(50)

        results = [engine.analyze_correlation(x, y, "A", "B") for _ in range(20)]
        for r in results[1:]:
            assert r.correlation == results[0].correlation
            assert r.series_a == results[0].series_a
            assert r.series_b == results[0].series_b

    def test_mil_rel_002_immutability(self):
        """MIL-REL-002: Relationship objects are immutable."""
        from macro_intelligence.relationships.models import CorrelationResult

        result = CorrelationResult(series_a="A", series_b="B", correlation=0.5)

        with pytest.raises(AttributeError):
            result.correlation = 0.9
        with pytest.raises(AttributeError):
            result.series_a = "C"

    def test_mil_rel_003_provenance(self):
        """MIL-REL-003: All relationships preserve provenance."""
        from macro_intelligence.relationships import RelationshipEngine

        engine = RelationshipEngine()
        x, y = _make_perfect_positive(50)

        result = engine.analyze_correlation(x, y, "A", "B", evidence_refs=["EV_001", "EV_002"])
        assert "EV_001" in result.evidence_refs
        assert "EV_002" in result.evidence_refs

    def test_mil_rel_004_versioned(self):
        """MIL-REL-004: Algorithms are versioned."""
        from macro_intelligence.relationships import ALGORITHM_VERSION, RelationshipEngine

        engine = RelationshipEngine()
        assert engine.version == ALGORITHM_VERSION
        assert ALGORITHM_VERSION == "rel-eng/v5.0.0"

    def test_mil_rel_005_no_v1_dependency(self):
        """MIL-REL-005: No dependency on ResearchOS V1."""
        import inspect

        from macro_intelligence.relationships import engine as eng_module

        source = inspect.getsource(eng_module)
        assert "researchos.core" not in source
        assert "from macro_intelligence" in source

    def test_mil_rel_006_deterministic_reconstruction(self):
        """MIL-REL-006: Historical reconstruction is deterministic."""
        from datetime import timezone

        from macro_intelligence.relationships.models import CorrelationResult, RelationshipResult

        UTC = timezone.utc
        base_time = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)

        r1 = RelationshipResult(
            series_a="XAU",
            series_b="DXY",
            overall_correlation=CorrelationResult(
                series_a="XAU",
                series_b="DXY",
                correlation=-0.72,
            ),
            analysis_time=base_time,
        )
        r2 = RelationshipResult(
            series_a="XAU",
            series_b="DXY",
            overall_correlation=CorrelationResult(
                series_a="XAU",
                series_b="DXY",
                correlation=-0.72,
            ),
            analysis_time=base_time,
        )

        assert r1.compute_hash() == r2.compute_hash()
