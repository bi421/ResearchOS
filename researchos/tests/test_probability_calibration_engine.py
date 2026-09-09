from __future__ import annotations

import pytest

from researchos.market_memory.probability_calibration import ProbabilityCalibrator
from researchos.objects.evidence import Evidence, EvidenceRegistry


def _registry() -> EvidenceRegistry:
    registry = EvidenceRegistry(research_id="CALIBRATION_TEST")
    outcomes = [False, False, True, False, True, True, False, True, True, True, False, True]
    confidences = [0.10, 0.20, 0.25, 0.35, 0.40, 0.50, 0.55, 0.65, 0.70, 0.80, 0.85, 0.95]
    for index, (confidence, outcome) in enumerate(zip(confidences, outcomes)):
        evidence = Evidence(
            observation_id=f"OBS-{index}",
            hypothesis_id="HYP-1",
            interpretation="calibration test",
            direction="Supporting" if outcome else "Contradicting",
            source_reliability=confidence,
            recency=1.0,
            relevance=1.0,
            consensus=1.0,
            structural_importance=1.0,
            quality_factor=1.0,
            uncertainty=0.0,
        )
        registry.add_evidence(evidence)
    registry._test_outcomes = {e.id: outcome for e, outcome in zip(registry.evidence, outcomes)}
    return registry


def test_isotonic_uses_ground_truth_and_is_monotone() -> None:
    registry = _registry()
    outcomes = registry._test_outcomes
    calibrator = ProbabilityCalibrator("isotonic")
    before = [e.confidence for e in registry.evidence]

    calibrator.fit(registry, outcomes)
    report = calibrator.calibrate(registry)

    ordered = sorted(report.calibrated_map.items(), key=lambda item: registry.evidence_ids.index(item[0]))
    probabilities = [probability for _, probability in ordered]
    assert all(0.0 <= p <= 1.0 for p in probabilities)
    assert all(a <= b for a, b in zip(probabilities, probabilities[1:]))
    assert report.total_samples == 12
    assert report.expected_calibration_error >= 0.0
    assert [e.confidence for e in registry.evidence] == before


def test_calibration_is_deterministic() -> None:
    registry = _registry()
    outcomes = registry._test_outcomes

    first = ProbabilityCalibrator("isotonic")
    second = ProbabilityCalibrator("isotonic")
    first.fit(registry, outcomes)
    second.fit(registry, outcomes)

    assert first.calibrate(registry) == second.calibrate(registry)


def test_platt_returns_bounded_probabilities() -> None:
    registry = _registry()
    calibrator = ProbabilityCalibrator("platt")
    calibrator.fit(registry, registry._test_outcomes)
    report = calibrator.calibrate(registry)

    assert report.total_samples == 12
    assert all(0.0 <= p <= 1.0 for p in report.calibrated_map.values())


def test_fit_requires_both_outcome_classes() -> None:
    registry = _registry()
    outcomes = {eid: True for eid in registry.evidence_ids}
    with pytest.raises(ValueError, match="both outcome classes"):
        ProbabilityCalibrator().fit(registry, outcomes)


def test_unknown_probability_is_not_silently_defaulted() -> None:
    registry = _registry()
    calibrator = ProbabilityCalibrator()
    calibrator.fit(registry, registry._test_outcomes)
    report = calibrator.calibrate(registry)
    with pytest.raises(KeyError):
        report.get_calibrated_probability("unknown")
