"""Validate an already-produced XAUUSD evidence registry.

This script is an external validation boundary. It does not manufacture a
"real-data" registry, invent WFO results, or mark a calibrator as fitted.
Real-market evidence and explicit ground-truth outcomes must be supplied by
the production research pipeline before this script can return success.
"""
from __future__ import annotations

from typing import Mapping

from researchos.experiments.external_validator import EvidenceChainValidator
from researchos.experiments.synthetic_boundary import SyntheticBoundaryChecker
from researchos.market_memory.probability_calibration import ProbabilityCalibrator
from researchos.objects.evidence import EvidenceRegistry


def run_pipeline_validation(
    registry: EvidenceRegistry | None = None,
    ground_truth_outcomes: Mapping[str, bool] | None = None,
) -> bool:
    """Validate evidence integrity and calibration without manufacturing inputs.

    Returns ``True`` only when a caller supplies a non-empty registry, the
    evidence-chain and synthetic boundaries pass, and calibration is fitted
    from at least ten matched historical outcomes.
    """
    sep = "=" * 80
    print(sep)
    print(" RESEARCHOS: XAUUSD M1 EVIDENCE PIPELINE VALIDATION")
    print(sep)

    if registry is None or not registry.evidence:
        print("\n FINAL VERDICT: BLOCKED")
        print(" No real evidence registry was supplied; validation cannot pass.")
        print(" This validator intentionally does not create synthetic stand-ins.")
        print(sep)
        return False

    print(f"\n[1/3] Loaded Registry: {registry.research_id} (Items: {len(registry.evidence)})")

    print("\n[2/3] Running Evidence Chain + Synthetic Boundary validation...")
    chain_passed, violations = EvidenceChainValidator(registry).validate_all()
    boundary_passed = SyntheticBoundaryChecker(registry).validate_no_mixing()
    if not chain_passed:
        for violation in violations:
            print(f"       FAILED: {violation}")
    if not boundary_passed:
        print("       FAILED: synthetic and real evidence are mixed")
    if chain_passed and boundary_passed:
        print("       PASSED")

    print("\n[3/3] Running Probability Calibration...")
    calibration_passed = False
    if ground_truth_outcomes is None:
        print("       BLOCKED: explicit historical ground-truth outcomes are required")
    else:
        try:
            calibrator = ProbabilityCalibrator(method="isotonic")
            calibrator.fit(registry, dict(ground_truth_outcomes))
            report = calibrator.calibrate(registry)
            print(
                "       PASSED: Fitted "
                + str(report.total_samples)
                + " samples. ECE: "
                + "{:.6f}".format(report.expected_calibration_error)
            )
            print("\n" + calibrator.generate_report(report, registry))
            calibration_passed = report.total_samples >= 10
        except (RuntimeError, ValueError) as exc:
            print("       FAILED: " + str(exc))

    success = chain_passed and boundary_passed and calibration_passed
    print("\n" + sep)
    if success:
        print(" FINAL VERDICT: PIPELINE INTEGRITY + CALIBRATION VERIFIED")
        print(" Evidence is real-input supplied, outcome-grounded, and reproducible.")
    else:
        print(" FINAL VERDICT: NOT CERTIFIED")
        print(" No downstream decision claim may be made from this run.")
    print(sep + "\n")
    return success


if __name__ == "__main__":
    raise SystemExit(1 if not run_pipeline_validation() else 0)
