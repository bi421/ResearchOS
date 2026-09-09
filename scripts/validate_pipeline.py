"""Fail-closed validation entrypoint for the real-data research pipeline.

This module deliberately does not manufacture evidence, labels, timestamps, or
calibration state. A successful calibration requires an externally constructed
EvidenceRegistry and explicit ground-truth outcome labels.
"""
from __future__ import annotations

from researchos.experiments.external_validator import EvidenceChainValidator
from researchos.experiments.synthetic_boundary import SyntheticBoundaryChecker
from researchos.market_memory.probability_calibration import ProbabilityCalibrator
from researchos.objects.evidence import EvidenceRegistry


def run_pipeline_validation(
    registry: EvidenceRegistry | None = None,
    ground_truth_outcomes: dict[str, bool] | None = None,
) -> bool:
    """Validate supplied evidence and calibrate only from explicit outcomes."""
    sep = "=" * 80
    print(sep)
    print(" RESEARCHOS: XAUUSD M1 REAL DATA PIPELINE VALIDATION")
    print(sep)

    if registry is None or ground_truth_outcomes is None:
        print(" FINAL VERDICT: NOT RUN — real evidence and explicit outcomes are required")
        print(" No evidence, labels, or calibration state was manufactured.")
        print(sep)
        return False

    print(f"\n[1/4] Loaded Registry: {registry.research_id} (Items: {len(registry.evidence)})")

    print("\n[2/4] Running External Evidence Chain Validator...")
    chain_passed, chain_violations = EvidenceChainValidator(registry).validate_all()
    if not chain_passed:
        print(f"       FAILED: {chain_violations}")
        return False
    print("       PASSED")

    print("\n[3/4] Running Synthetic-Data Boundary Checker...")
    if not SyntheticBoundaryChecker(registry).validate_no_mixing():
        print("       FAILED")
        return False
    print("       PASSED")

    print("\n[4/4] Running outcome-grounded probability calibration...")
    try:
        calibrator = ProbabilityCalibrator(method="isotonic")
        calibrator.fit(registry, ground_truth_outcomes)
        report = calibrator.calibrate(registry)
    except Exception as exc:
        print(f"       FAILED: {exc}")
        return False

    print(
        "       PASSED: "
        f"{report.total_samples} matched samples; "
        f"ECE={report.expected_calibration_error:.6f}; "
        f"Brier={report.brier_score:.6f}"
    )
    print("\n" + sep)
    print(" FINAL VERDICT: REAL EVIDENCE CHAIN + OUTCOME CALIBRATION VERIFIED")
    print(sep + "\n")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if run_pipeline_validation() else 1)
