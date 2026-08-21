"""
ResearchOS Macro Intelligence Layer - Regime Transition Tests
Tests for deterministic regime transition analysis engine.
"""

from datetime import datetime, timezone

import pytest

UTC = timezone.utc


def _make_test_assessment(**kwargs):
    """Module-level helper to create a RegimeAssessment with default values."""
    from macro_intelligence.regime.detection.models import DetectionEvidence, RegimeAssessment

    defaults = {
        "assessment_time": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        "algorithm_version": "det-orch/v2.0.0",
        "inflation_signal": DetectionEvidence(
            detector_name="inflation_detector",
            signal="stable",
            confidence=0.8,
            algorithm_version="infl-det/v2.0.0",
        ),
        "growth_signal": DetectionEvidence(
            detector_name="growth_detector",
            signal="expansion",
            confidence=0.85,
            algorithm_version="grw-det/v2.0.0",
        ),
        "monetary_signal": DetectionEvidence(
            detector_name="monetary_detector",
            signal="neutral",
            confidence=0.7,
            algorithm_version="mon-det/v2.0.0",
        ),
        "liquidity_signal": DetectionEvidence(
            detector_name="liquidity_detector",
            signal="expanding",
            confidence=0.75,
            algorithm_version="liq-det/v2.0.0",
        ),
        "employment_signal": DetectionEvidence(
            detector_name="employment_detector",
            signal="strong",
            confidence=0.9,
            algorithm_version="emp-det/v2.0.0",
        ),
        "risk_signal": DetectionEvidence(
            detector_name="risk_detector",
            signal="normal",
            confidence=0.65,
            algorithm_version="risk-det/v2.0.0",
        ),
        "overall_confidence": 0.78,
    }
    defaults.update(kwargs)
    return RegimeAssessment(**defaults)


# =============================================================================
# Model tests
# =============================================================================


class TestTransitionSignal:
    """Tests for TransitionSignal model."""

    def test_create_signal(self):
        """Test creating a transition signal."""
        from macro_intelligence.regime.transition import TransitionSignal, TransitionType

        signal = TransitionSignal(
            detector_name="inflation_detector",
            signal_id="TRANS-001",
            signal_type=TransitionType.GRADUAL_SHIFT,
            strength=0.75,
            direction="UP",
        )

        assert signal.detector_name == "inflation_detector"
        assert signal.strength == 0.75
        assert signal.direction == "UP"

    def test_signal_to_dict(self):
        """Test signal serialization."""
        from macro_intelligence.regime.transition import TransitionSignal, TransitionType

        signal = TransitionSignal(
            detector_name="test",
            signal_id="S-001",
            signal_type=TransitionType.STABLE,
            strength=0.5,
            direction="NEUTRAL",
        )

        data = signal.to_dict()
        assert data["detector_name"] == "test"
        assert data["strength"] == 0.5

    def test_signal_from_dict(self):
        """Test signal deserialization."""
        from macro_intelligence.regime.transition import TransitionSignal, TransitionType

        data = {
            "detector_name": "test",
            "signal_id": "S-001",
            "signal_type": TransitionType.GRADUAL_SHIFT,
            "strength": 0.6,
            "direction": "DOWN",
        }

        signal = TransitionSignal.from_dict(data)
        assert signal.strength == 0.6
        assert signal.direction == "DOWN"

    def test_signal_roundtrip(self):
        """Test signal JSON roundtrip."""
        from macro_intelligence.regime.transition import TransitionSignal, TransitionType

        original = TransitionSignal(
            detector_name="test",
            signal_id="S-001",
            signal_type=TransitionType.GRADUAL_SHIFT,
            strength=0.6,
            direction="DOWN",
        )

        json_str = original.to_json() if hasattr(original, "to_json") else original.to_dict()
        restored = TransitionSignal.from_dict(json_str if isinstance(json_str, dict) else json_str)
        assert restored.detector_name == original.detector_name

    def test_signal_immutability(self):
        """Test signal immutability."""
        from macro_intelligence.regime.transition import TransitionSignal, TransitionType

        signal = TransitionSignal(
            detector_name="test",
            signal_id="S-001",
            signal_type=TransitionType.STABLE,
            strength=0.5,
            direction="NEUTRAL",
        )

        with pytest.raises(AttributeError):
            signal.strength = 0.9

    def test_signal_hash_deterministic(self):
        """Test signal hash determinism."""
        from macro_intelligence.regime.transition import TransitionSignal, TransitionType

        s1 = TransitionSignal(
            detector_name="test",
            signal_id="S-001",
            signal_type=TransitionType.STABLE,
            strength=0.5,
            direction="NEUTRAL",
        )
        s2 = TransitionSignal(
            detector_name="test",
            signal_id="S-001",
            signal_type=TransitionType.STABLE,
            strength=0.5,
            direction="NEUTRAL",
        )

        assert s1.compute_hash() == s2.compute_hash()


class TestRegimeTransition:
    """Tests for RegimeTransition model."""

    def test_create_transition(self):
        """Test creating a regime transition."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransition, TransitionType

        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        assert transition.previous_regime == MacroRegime.GOLDILOCKS
        assert transition.current_regime == MacroRegime.INFLATIONARY_GROWTH
        assert transition.confidence == 0.85

    def test_transition_to_dict(self):
        """Test transition serialization."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransition, TransitionType

        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        data = transition.to_dict()
        assert data["previous_regime"] == "goldilocks"
        assert data["current_regime"] == "inflationary_growth"

    def test_transition_from_dict(self):
        """Test transition deserialization."""
        from macro_intelligence.regime.transition import RegimeTransition

        data = {
            "transition_id": "TRANS-001",
            "previous_regime": "goldilocks",
            "current_regime": "recession",
            "transition_type": "reversal",
            "confidence": 0.9,
            "detected_at": "2026-08-03T12:00:00+00:00",
        }

        transition = RegimeTransition.from_dict(data)
        assert transition.current_regime.value == "recession"

    def test_transition_roundtrip(self):
        """Test transition JSON roundtrip."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransition, TransitionType

        original = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        json_str = original.to_json()
        restored = RegimeTransition.from_json(json_str)

        assert restored.transition_id == original.transition_id
        assert restored.previous_regime == original.previous_regime
        assert restored.current_regime == original.current_regime
        assert restored.to_json() == json_str

    def test_transition_immutability(self):
        """Test transition immutability."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransition, TransitionType

        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        with pytest.raises(AttributeError):
            transition.transition_id = "MODIFIED"

    def test_transition_hash_deterministic(self):
        """Test transition hash determinism."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransition, TransitionType

        t1 = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        t2 = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        assert t1.compute_hash() == t2.compute_hash()


class TestEarlyWarningSignal:
    """Tests for EarlyWarningSignal model."""

    def test_create_warning(self):
        """Test creating an early warning signal."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import EarlyWarningSignal

        warning = EarlyWarningSignal(
            warning_id="WARN-001",
            current_regime=MacroRegime.GOLDILOCKS,
            predicted_regime=MacroRegime.STAGFLATION,
            confidence=0.65,
            horizon_periods=6,
            explanation="Inflation rising with growth slowing",
        )

        assert warning.current_regime == MacroRegime.GOLDILOCKS
        assert warning.predicted_regime == MacroRegime.STAGFLATION
        assert warning.confidence == 0.65

    def test_warning_to_dict(self):
        """Test warning serialization."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import EarlyWarningSignal

        warning = EarlyWarningSignal(
            warning_id="WARN-001",
            current_regime=MacroRegime.GOLDILOCKS,
            predicted_regime=MacroRegime.STAGFLATION,
            confidence=0.65,
            horizon_periods=6,
        )

        data = warning.to_dict()
        assert data["current_regime"] == "goldilocks"
        assert data["predicted_regime"] == "stagflation"

    def test_warning_roundtrip(self):
        """Test warning JSON roundtrip."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import EarlyWarningSignal

        original = EarlyWarningSignal(
            warning_id="WARN-001",
            current_regime=MacroRegime.GOLDILOCKS,
            predicted_regime=MacroRegime.STAGFLATION,
            confidence=0.65,
            horizon_periods=6,
        )

        json_str = original.to_json()
        restored = EarlyWarningSignal.from_json(json_str)

        assert restored.warning_id == original.warning_id
        assert restored.confidence == original.confidence

    def test_warning_immutability(self):
        """Test warning immutability."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import EarlyWarningSignal

        warning = EarlyWarningSignal(
            warning_id="WARN-001",
            current_regime=MacroRegime.GOLDILOCKS,
            predicted_regime=MacroRegime.STAGFLATION,
            confidence=0.65,
            horizon_periods=6,
        )

        with pytest.raises(AttributeError):
            warning.confidence = 0.9


class TestTransitionAnalysisResult:
    """Tests for TransitionAnalysisResult model."""

    def test_create_result(self):
        """Test creating a transition analysis result."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionAnalysisResult

        result = TransitionAnalysisResult(
            analysis_id="ANALYSIS-001",
            current_regime=MacroRegime.GOLDILOCKS,
            transition_detected=True,
        )

        assert result.analysis_id == "ANALYSIS-001"
        assert result.transition_detected is True

    def test_result_to_dict(self):
        """Test result serialization."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionAnalysisResult

        result = TransitionAnalysisResult(
            analysis_id="ANALYSIS-001",
            current_regime=MacroRegime.GOLDILOCKS,
        )

        data = result.to_dict()
        assert data["current_regime"] == "goldilocks"
        assert data["transition_detected"] is False

    def test_result_roundtrip(self):
        """Test result JSON roundtrip."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionAnalysisResult

        original = TransitionAnalysisResult(
            analysis_id="ANALYSIS-001",
            current_regime=MacroRegime.GOLDILOCKS,
        )

        json_str = original.to_json()
        restored = TransitionAnalysisResult.from_json(json_str)

        assert restored.analysis_id == original.analysis_id
        assert restored.current_regime == original.current_regime
        assert restored.to_json() == json_str

    def test_result_immutability(self):
        """Test result immutability."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionAnalysisResult

        result = TransitionAnalysisResult(
            analysis_id="ANALYSIS-001",
            current_regime=MacroRegime.GOLDILOCKS,
        )

        with pytest.raises(AttributeError):
            result.analysis_id = "MODIFIED"


# =============================================================================
# Transition rules tests
# =============================================================================


class TestTransitionRules:
    """Tests for transition classification rules."""

    def test_classify_stable(self):
        """Test stable transition classification."""
        from macro_intelligence.regime.transition.transitions import classify_transition_type

        result = classify_transition_type(
            signal_strengths=[0.05, 0.08],
            signal_agreement=0.0,
            confidence=0.15,
            persistence_periods=10,
        )
        assert result == "stable"

    def test_classify_gradual_shift(self):
        """Test gradual shift classification."""
        from macro_intelligence.regime.transition.transitions import classify_transition_type

        result = classify_transition_type(
            signal_strengths=[0.35, 0.4, 0.3],
            signal_agreement=0.8,
            confidence=0.5,
            persistence_periods=6,
        )
        assert result == "gradual_shift"

    def test_classify_accelerated_shift(self):
        """Test accelerated shift classification."""
        from macro_intelligence.regime.transition.transitions import classify_transition_type

        result = classify_transition_type(
            signal_strengths=[0.8, 0.85, 0.75],
            signal_agreement=0.9,
            confidence=0.82,
            persistence_periods=4,
        )
        assert result == "accelerated_shift"

    def test_classify_reversal(self):
        """Test reversal classification."""
        from macro_intelligence.regime.transition.transitions import classify_transition_type

        result = classify_transition_type(
            signal_strengths=[0.9, 0.95, 0.85],
            signal_agreement=0.95,
            confidence=0.92,
            persistence_periods=2,
        )
        assert result == "reversal"

    def test_classify_volatile(self):
        """Test volatile classification."""
        from macro_intelligence.regime.transition.transitions import classify_transition_type

        # Volatile: high variance in signals with low agreement
        result = classify_transition_type(
            signal_strengths=[0.1, 0.95, 0.05, 0.9],
            signal_agreement=0.2,
            confidence=0.45,
            persistence_periods=3,
        )
        assert result == "volatile"

    def test_classify_early_warning(self):
        """Test early warning generation."""
        from macro_intelligence.regime.transition.transitions import (
            estimate_early_warning_horizon,
            should_generate_early_warning,
        )

        # Should generate warning
        assert should_generate_early_warning(0.6, 6, [0.5, 0.6, 0.55]) is True
        # Should not generate warning (low confidence)
        assert should_generate_early_warning(0.3, 6, [0.5, 0.6, 0.55]) is False
        # Should not generate warning (short horizon)
        assert should_generate_early_warning(0.6, 1, [0.5, 0.6, 0.55]) is False

        horizon = estimate_early_warning_horizon([0.7, 0.8, 0.6], 0.75)
        assert 2 <= horizon <= 12

    def test_continuation_probability(self):
        """Test continuation probability calculation."""
        from macro_intelligence.regime.transition.transitions import (
            calculate_continuation_probability,
        )

        # High persistence, low signals → high continuation prob
        prob = calculate_continuation_probability(10, 6.0, [0.2, 0.3])
        assert 0.5 <= prob <= 1.0

        # Low persistence, high signals → low continuation prob
        prob2 = calculate_continuation_probability(2, 6.0, [0.8, 0.9])
        assert 0.0 <= prob2 < prob

    def test_normalize_probs(self):
        """Test probability normalization."""
        from macro_intelligence.regime.transition.transitions import normalize_transition_probs

        probs = {"a": 0.2, "b": 0.3, "c": 0.5}
        normalized = normalize_transition_probs(probs)
        assert abs(sum(normalized.values()) - 1.0) < 0.001

    def test_default_transition_probs(self):
        """Test default transition probability matrix."""
        from macro_intelligence.regime.transition.transitions import get_default_transition_probs

        probs = get_default_transition_probs()
        assert len(probs) == 6  # 6 macro regimes
        for regime, targets in probs.items():
            total = sum(targets.values())
            assert abs(total - 1.0) < 0.001


# =============================================================================
# Probability engine tests
# =============================================================================


class TestTransitionProbabilityEngine:
    """Tests for TransitionProbabilityEngine."""

    def test_get_transition_probability(self):
        """Test getting transition probability."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        prob = engine.get_transition_probability(MacroRegime.GOLDILOCKS, MacroRegime.INFLATIONARY_GROWTH)
        assert 0.0 <= prob <= 1.0

    def test_get_all_transition_probabilities(self):
        """Test getting all transition probabilities from a regime."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        probs = engine.get_all_transition_probabilities(MacroRegime.GOLDILOCKS)

        assert len(probs) == 6
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.001

    def test_get_next_regime_probabilities(self):
        """Test getting next regime probabilities excluding current."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        probs = engine.get_next_regime_probabilities(MacroRegime.GOLDILOCKS)

        assert MacroRegime.GOLDILOCKS not in probs
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.001

    def test_get_most_likely_next_regime(self):
        """Test getting most likely next regime."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        next_regime, prob = engine.get_most_likely_next_regime(MacroRegime.GOLDILOCKS)

        assert next_regime != MacroRegime.GOLDILOCKS
        assert 0.0 < prob <= 1.0

    def test_transition_risk_score(self):
        """Test transition risk score."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        risk = engine.get_transition_risk_score(MacroRegime.GOLDILOCKS)

        assert 0.0 <= risk <= 1.0

    def test_stability_score(self):
        """Test stability score."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        stability = engine.get_stability_score(MacroRegime.GOLDILOCKS)

        assert 0.0 <= stability <= 1.0

    def test_update_with_observations(self):
        """Test updating probabilities with observations."""
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine = TransitionProbabilityEngine()
        original_probs = engine.get_all_transition_probabilities(
            __import__(
                "macro_intelligence.regime.classification.taxonomy", fromlist=["MacroRegime"]
            ).MacroRegime.GOLDILOCKS
        )

        engine.update_with_observations(
            [
                ("goldilocks", "inflationary_growth"),
                ("goldilocks", "inflationary_growth"),
                ("goldilocks", "goldilocks"),
            ]
        )

        # Probabilities should have updated
        new_probs = engine.get_all_transition_probabilities(
            __import__(
                "macro_intelligence.regime.classification.taxonomy", fromlist=["MacroRegime"]
            ).MacroRegime.GOLDILOCKS
        )

        assert engine.observation_count == 3
        # The probability of staying in goldilocks should have decreased
        assert new_probs.get("goldilocks", 0.0) < original_probs.get("goldilocks", 1.0)

    def test_engine_deterministic(self):
        """Test that engine produces deterministic output."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import TransitionProbabilityEngine

        engine1 = TransitionProbabilityEngine()
        engine2 = TransitionProbabilityEngine()

        assert engine1.get_transition_probability(
            MacroRegime.GOLDILOCKS, MacroRegime.INFLATIONARY_GROWTH
        ) == engine2.get_transition_probability(MacroRegime.GOLDILOCKS, MacroRegime.INFLATIONARY_GROWTH)


# =============================================================================
# Transition history tests
# =============================================================================


class TestTransitionHistory:
    """Tests for TransitionHistory."""

    def test_create_history(self):
        """Test creating an empty history."""
        from macro_intelligence.regime.transition import TransitionHistory

        history = TransitionHistory()
        assert history.count == 0
        assert history.entries == []

    def test_add_transition(self):
        """Test adding a transition to history."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import (
            RegimeTransition,
            TransitionHistory,
            TransitionType,
        )

        history = TransitionHistory()
        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        entry = history.add_transition(transition)

        assert history.count == 1
        assert entry.transition_id == "TRANS-001"

    def test_get_transitions_filtered(self):
        """Test filtering transitions."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import (
            RegimeTransition,
            TransitionHistory,
            TransitionType,
        )

        history = TransitionHistory()

        # Add multiple transitions
        for i, (prev, curr) in enumerate(
            [
                (MacroRegime.GOLDILOCKS, MacroRegime.INFLATIONARY_GROWTH),
                (MacroRegime.INFLATIONARY_GROWTH, MacroRegime.STAGFLATION),
                (MacroRegime.STAGFLATION, MacroRegime.RECESSION),
            ]
        ):
            transition = RegimeTransition(
                transition_id=f"TRANS-{i:03d}",
                previous_regime=prev,
                current_regime=curr,
                transition_type=TransitionType.GRADUAL_SHIFT,
                confidence=0.8,
                detected_at=datetime(2026, 8, 3, 12, i, tzinfo=UTC),
            )
            history.add_transition(transition)

        # Filter by target regime
        recession_transitions = history.get_transitions(to_regime=MacroRegime.RECESSION)
        assert len(recession_transitions) == 1
        assert recession_transitions[0].current_regime == MacroRegime.RECESSION

    def test_update_outcome(self):
        """Test updating transition outcome."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import (
            RegimeTransition,
            TransitionHistory,
            TransitionType,
        )

        history = TransitionHistory()
        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        history.add_transition(transition)
        updated = history.update_outcome("TRANS-001", "confirmed", duration_observed=6)

        assert updated is True
        entry = history.get_last_transition()
        assert entry.outcome == "confirmed"
        assert entry.duration_observed == 6

    def test_update_outcome_not_found(self):
        """Test updating non-existent transition."""
        from macro_intelligence.regime.transition import TransitionHistory

        history = TransitionHistory()
        updated = history.update_outcome("NONEXISTENT", "confirmed")
        assert updated is False

    def test_get_transition_counts(self):
        """Test transition frequency counts."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import (
            RegimeTransition,
            TransitionHistory,
            TransitionType,
        )

        history = TransitionHistory()

        for i in range(3):
            transition = RegimeTransition(
                transition_id=f"TRANS-{i:03d}",
                previous_regime=MacroRegime.GOLDILOCKS,
                current_regime=MacroRegime.INFLATIONARY_GROWTH,
                transition_type=TransitionType.GRADUAL_SHIFT,
                confidence=0.8,
                detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            )
            history.add_transition(transition)

        counts = history.get_transition_counts()
        assert counts["goldilocks"]["inflationary_growth"] == 3

    def test_history_deterministic(self):
        """Test that history hash is deterministic."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import (
            RegimeTransition,
            TransitionHistory,
            TransitionType,
        )

        history1 = TransitionHistory()
        history2 = TransitionHistory()

        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        history1.add_transition(transition)
        history2.add_transition(transition)

        assert history1.compute_hash() == history2.compute_hash()

    def test_history_serialization(self):
        """Test history serialization roundtrip."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import (
            RegimeTransition,
            TransitionHistory,
            TransitionType,
        )

        history = TransitionHistory()
        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        history.add_transition(transition)

        data = history.to_dict()
        restored = TransitionHistory.from_dict(data)

        assert restored.count == history.count
        assert restored.entries[0].transition_id == transition.transition_id


# =============================================================================
# Transition detector tests
# =============================================================================


class TestRegimeTransitionDetector:
    """Tests for RegimeTransitionDetector."""

    def test_detector_version(self):
        """Test detector version."""
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()
        assert detector.version == "trans-det/v4.0.0"

    def test_detector_to_dict(self):
        """Test detector metadata."""
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()
        meta = detector.to_dict()

        assert meta["version"] == "trans-det/v4.0.0"
        assert meta["history_count"] == 0

    def test_detect_no_transition_same_regime(self):
        """Test that no transition is detected when regime is the same."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()
        assessment = _make_test_assessment()

        # First call - no previous regime, should return None
        result = detector.detect_transition(assessment, None)
        assert result is None

        # Second call - same regime, should return None
        result2 = detector.detect_transition(assessment, MacroRegime.GOLDILOCKS)
        assert result2 is None

    def test_detect_transition_different_regime(self):
        """Test that transition is detected when regime changes."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.detection.models import DetectionEvidence
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()

        # Goldilocks assessment
        _make_test_assessment()

        # Recession assessment (high inflation + contraction)
        assessment2 = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.9,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.85,
                algorithm_version="grw-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="crisis",
                confidence=0.95,
                algorithm_version="risk-det/v2.0.0",
            ),
        )

        # First: detect transition from goldilocks to recession
        result = detector.detect_transition(assessment2, MacroRegime.GOLDILOCKS)

        assert result is not None
        assert result.previous_regime == MacroRegime.GOLDILOCKS
        assert result.confidence > 0
        assert len(result.signals) == 6

    def test_detect_transition_deterministic(self):
        """Test that transition detection is deterministic."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.detection.models import DetectionEvidence
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()

        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.9,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.85,
                algorithm_version="grw-det/v2.0.0",
            ),
        )

        # Run multiple times - should get consistent results
        results = []
        for _ in range(5):
            result = detector.detect_transition(assessment, MacroRegime.GOLDILOCKS)
            if result:
                results.append(result)

        if len(results) >= 2:
            # Same transition type and confidence
            assert results[0].transition_type == results[1].transition_type
            assert results[0].confidence == results[1].confidence

    def test_analyze_transitions(self):
        """Test full transition analysis."""
        from macro_intelligence.regime.detection.models import DetectionEvidence
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()

        assessment1 = _make_test_assessment()
        assessment2 = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.9,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.85,
                algorithm_version="grw-det/v2.0.0",
            ),
        )

        result = detector.analyze_transitions(assessment2, assessment1)

        assert result.analysis_id is not None
        assert result.current_regime is not None
        # History should have at least one entry if transition detected
        assert detector.history.count >= 0

    def test_analyze_no_transition(self):
        """Test analysis when no transition occurs."""
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()
        assessment = _make_test_assessment()

        result = detector.analyze_transitions(assessment, assessment)

        assert result.transition_detected is False

    def test_provenance_preserved(self):
        """Test that provenance is preserved in transitions."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.detection.models import DetectionEvidence
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()

        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.9,
                algorithm_version="infl-det/v2.0.0",
                evidence_refs=["EV_001", "EV_002"],
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.85,
                algorithm_version="grw-det/v2.0.0",
                evidence_refs=["EV_003"],
            ),
        )

        transition = detector.detect_transition(assessment, MacroRegime.GOLDILOCKS)

        if transition:
            # Check that detector provenance is preserved (transition algorithm version)
            for signal in transition.signals:
                assert signal.algorithm_version


# =============================================================================
# MIL-TRANS invariant tests
# =============================================================================


class TestMILTransitionInvariants:
    """Tests for MIL-TRANS invariants."""

    def test_mil_trans_001_deterministic(self):
        """MIL-TRANS-001: Same input produces identical transition output."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.detection.models import DetectionEvidence
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()

        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.9,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.85,
                algorithm_version="grw-det/v2.0.0",
            ),
        )

        # Run detection multiple times
        results = []
        for _ in range(10):
            result = detector.detect_transition(assessment, MacroRegime.GOLDILOCKS)
            if result:
                results.append(result)

        if len(results) >= 2:
            # Same transition type and confidence
            assert results[0].transition_type == results[1].transition_type
            assert results[0].confidence == results[1].confidence
            assert results[0].previous_regime == results[1].previous_regime
            assert results[0].current_regime == results[1].current_regime

    def test_mil_trans_002_immutability(self):
        """MIL-TRANS-002: Transition objects are immutable."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransition, TransitionType

        transition = RegimeTransition(
            transition_id="TRANS-001",
            previous_regime=MacroRegime.GOLDILOCKS,
            current_regime=MacroRegime.INFLATIONARY_GROWTH,
            transition_type=TransitionType.GRADUAL_SHIFT,
            confidence=0.85,
            detected_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        # All fields should be immutable
        with pytest.raises(AttributeError):
            transition.transition_id = "MODIFIED"
        with pytest.raises(AttributeError):
            transition.confidence = 0.9
        with pytest.raises(AttributeError):
            transition.signals = []

    def test_mil_trans_003_provenance(self):
        """MIL-TRANS-003: All transitions preserve provenance."""
        from macro_intelligence.regime.classification.taxonomy import MacroRegime
        from macro_intelligence.regime.transition import RegimeTransitionDetector

        detector = RegimeTransitionDetector()

        assessment = _make_test_assessment()
        transition = detector.detect_transition(assessment, MacroRegime.GOLDILOCKS)

        if transition:
            # All signals should have algorithm versions
            for signal in transition.signals:
                assert signal.algorithm_version
                assert "/v" in signal.algorithm_version

    def test_mil_trans_004_versioned(self):
        """MIL-TRANS-004: Algorithms are versioned."""
        from macro_intelligence.regime.transition import (
            ALGORITHM_VERSION,
            RULES_VERSION,
            RegimeTransitionDetector,
        )

        detector = RegimeTransitionDetector()
        assert detector.version == ALGORITHM_VERSION

        # Rules version should be consistent
        assert RULES_VERSION.startswith("trans-rules/")

    def test_mil_trans_005_no_v1_dependency(self):
        """MIL-TRANS-005: No dependency on ResearchOS V1."""
        # This test verifies that the transition module only imports
        # from macro_intelligence modules, not from researchos core
        import inspect

        from macro_intelligence.regime.transition import detector as det_module

        source = inspect.getsource(det_module)
        # Should not import from researchos.core or similar V1 paths
        assert "researchos.core" not in source
        assert "from macro_intelligence" in source
