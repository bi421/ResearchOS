from __future__ import annotations

from researchos.market_memory.probability_calibration import ProbabilityCalibrator
from researchos.objects.evidence import Evidence, EvidenceRegistry


def _registry() -> EvidenceRegistry:
    evidence = [
        Evidence(
            observation_id=f"obs-{i}",
            hypothesis_id="hypothesis-1",
            interpretation=f"sample-{i}",
            direction="Supporting" if i % 2 else "Contradicting",
            source_reliability=confidence,
            id=f"evidence-{i}",
        )
        for i, confidence in enumerate(
            (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.55, 0.65, 0.80, 0.90, 0.95, 0.99)
        )
    ]
    return EvidenceRegistry("research-1", evidence=evidence)


def test_isotonic_predicts_unseen_out_of_sample_confidence() -> None:
    registry = _registry()
    outcomes = {
        f"evidence-{i}": i >= 6
        for i in range(12)
    }

    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(registry, outcomes)

    low = calibrator.predict_probability(0.07)
    middle = calibrator.predict_probability(0.72)
    high = calibrator.predict_probability(0.98)

    assert 0.0 <= low <= middle <= high <= 1.0
    assert low < high


def test_isotonic_prediction_does_not_require_oos_evidence_id() -> None:
    registry = _registry()
    outcomes = {f"evidence-{i}": i >= 6 for i in range(12)}

    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(registry, outcomes)

    assert calibrator.predict_probability(0.72) == calibrator.predict_probability(0.72)
