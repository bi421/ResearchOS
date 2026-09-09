"""Deterministic probability calibration for interpreted evidence.

Calibration is a statistical transformation of heuristic confidence into an
estimate derived from historical outcomes. It never mutates Evidence objects.
The implementation is dependency-free so the research result is reproducible
across environments.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from researchos.objects.evidence import EvidenceRegistry


@dataclass(frozen=True)
class CalibrationReport:
    """Immutable calibration result for the fitted evidence sample."""

    research_id: str
    calibration_method: str
    total_samples: int
    calibrated_map: Dict[str, float]
    expected_calibration_error: float

    def get_calibrated_probability(self, evidence_id: str) -> float:
        """Return a fitted probability; fail closed for unknown evidence."""
        if evidence_id not in self.calibrated_map:
            raise KeyError(f"Evidence {evidence_id!r} was not part of calibration")
        return self.calibrated_map[evidence_id]


def _clip_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _isotonic_fit(scores: List[float], labels: List[float]) -> List[float]:
    """Fit isotonic regression with deterministic pool-adjacent-violators."""
    order = sorted(range(len(scores)), key=lambda i: (scores[i], i))
    # Each block is [sum_y, count, start_position, end_position].
    blocks: List[List[float]] = []
    for position, i in enumerate(order):
        blocks.append([labels[i], 1.0, float(position), float(position)])
        while len(blocks) >= 2:
            left, right = blocks[-2], blocks[-1]
            if left[0] / left[1] <= right[0] / right[1]:
                break
            merged = [
                left[0] + right[0],
                left[1] + right[1],
                left[2],
                right[3],
            ]
            blocks[-2:] = [merged]

    fitted = [0.0] * len(scores)
    for block in blocks:
        value = _clip_probability(block[0] / block[1])
        start, end = int(block[2]), int(block[3]) + 1
        for position in range(start, end):
            fitted[order[position]] = value
    return fitted


def _platt_fit(scores: List[float], labels: List[float]) -> Tuple[float, float]:
    """Fit sigmoid(a*x+b) using deterministic Newton iterations."""
    import math

    a, b = 0.0, 0.0
    for _ in range(100):
        g_a = g_b = 0.0
        h_aa = h_ab = h_bb = 1e-9
        for x, y in zip(scores, labels):
            z = max(-35.0, min(35.0, a * x + b))
            p = 1.0 / (1.0 + math.exp(-z))
            w = max(p * (1.0 - p), 1e-9)
            error = p - y
            g_a += error * x
            g_b += error
            h_aa += w * x * x
            h_ab += w * x
            h_bb += w
        det = h_aa * h_bb - h_ab * h_ab
        if abs(det) < 1e-12:
            break
        da = (h_bb * g_a - h_ab * g_b) / det
        db = (-h_ab * g_a + h_aa * g_b) / det
        a -= da
        b -= db
        if abs(da) + abs(db) < 1e-10:
            break
    return a, b


class ProbabilityCalibrator:
    """Fit deterministic isotonic or Platt calibration from historical outcomes."""

    def __init__(self, method: str = "isotonic"):
        if method not in ("isotonic", "platt"):
            raise ValueError("Method must be 'isotonic' or 'platt'")
        self.method = method
        self._is_fitted = False
        self._fitted_ids: List[str] = []
        self._calibrated: Dict[str, float] = {}
        self._outcomes: Dict[str, bool] = {}
        self._ece = 0.0

    def fit(self, evidence_registry: EvidenceRegistry, ground_truth_outcomes: Dict[str, bool]) -> None:
        """Fit using evidence confidence and explicitly supplied historical outcomes."""
        matched = sorted(eid for eid in evidence_registry.evidence_ids if eid in ground_truth_outcomes)
        if len(matched) < 10:
            raise ValueError("Minimum 10 matched samples required for calibration")

        evidence_by_id = {e.id: e for e in evidence_registry.evidence}
        matched = [eid for eid in matched if eid in evidence_by_id]
        labels = [1.0 if ground_truth_outcomes[eid] else 0.0 for eid in matched]
        if len(matched) < 10 or len(set(labels)) < 2:
            raise ValueError("Calibration requires at least 10 existing samples and both outcome classes")
        scores = [_clip_probability(evidence_by_id[eid].confidence) for eid in matched]

        if self.method == "isotonic":
            calibrated = _isotonic_fit(scores, labels)
        else:
            import math
            a, b = _platt_fit(scores, labels)
            calibrated = [1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, a * x + b)))) for x in scores]

        self._fitted_ids = matched
        self._calibrated = {eid: round(_clip_probability(p), 6) for eid, p in zip(matched, calibrated)}
        self._outcomes = {eid: bool(ground_truth_outcomes[eid]) for eid in matched}
        self._ece = self._compute_ece()
        self._is_fitted = True

    def _compute_ece(self, num_bins: int = 10) -> float:
        if not self._fitted_ids:
            return 0.0
        total = len(self._fitted_ids)
        error = 0.0
        for bin_index in range(num_bins):
            members = [
                eid for eid in self._fitted_ids
                if min(int(self._calibrated[eid] * num_bins), num_bins - 1) == bin_index
            ]
            if not members:
                continue
            confidence = sum(self._calibrated[eid] for eid in members) / len(members)
            accuracy = sum(1.0 if self._outcomes[eid] else 0.0 for eid in members) / len(members)
            error += len(members) / total * abs(confidence - accuracy)
        return round(error, 6)

    def calibrate(self, evidence_registry: EvidenceRegistry) -> CalibrationReport:
        """Return fitted probabilities for evidence used during fitting."""
        if not self._is_fitted:
            raise RuntimeError("Calibrator must be fitted before calibrating")
        available = [eid for eid in self._fitted_ids if eid in evidence_registry.evidence_ids]
        return CalibrationReport(
            research_id=evidence_registry.research_id,
            calibration_method=self.method,
            total_samples=len(available),
            calibrated_map={eid: self._calibrated[eid] for eid in available},
            expected_calibration_error=self._ece,
        )

    def generate_report(self, report: CalibrationReport, registry: EvidenceRegistry) -> str:
        """Generate a report whose claims are limited to fitted evidence."""
        evidence_by_id = {e.id: e for e in registry.evidence}
        lines = [
            "=" * 80,
            " PROBABILITY CALIBRATION REPORT",
            "=" * 80,
            f"Research ID: {report.research_id}",
            f"Method: {report.calibration_method.upper()}",
            f"Fitted Samples: {report.total_samples}",
            f"Expected Calibration Error (ECE): {report.expected_calibration_error:.6f}",
            "",
            "CALIBRATED EVIDENCE MAPPING:",
            "-" * 80,
        ]
        for eid, probability in sorted(report.calibrated_map.items()):
            evidence = evidence_by_id.get(eid)
            if evidence is not None:
                lines.append(
                    f"  Evidence: {eid[:8]}... | Heuristic: {evidence.confidence:.6f} "
                    f"-> Calibrated: {probability:.6f} | Direction: {evidence.direction}"
                )
        lines.append("=" * 80)
        return "\n".join(lines)
