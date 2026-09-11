from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTINUITY = ROOT / "reports/phase52_rebuild/context_continuity_audit.json"
FEATURE = ROOT / "reports/phase52_rebuild/context_feature_audit.json"
BOUNDARY = ROOT / "reports/phase52_rebuild/context_boundary_sensitivity.json"
CONVERGENCE = ROOT / "reports/phase52_rebuild/context_initialization_convergence.json"
OUT = ROOT / "reports/phase52_rebuild/context_gate.json"

REQUIRED_XAU_CONTEXT_DAYS = 240
REQUIRED_DXY_OVERLAP_DAYS = 60
REQUIRED_RESEARCH_ROWS = 1200


def _load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    continuity = _load(CONTINUITY)
    feature = _load(FEATURE)
    boundary = _load(BOUNDARY)
    convergence = _load(CONVERGENCE)

    continuity_status = continuity.get("status")
    feature_status = feature.get("status")
    boundary_status = boundary.get("status")
    convergence_status = convergence.get(
        "scientific_convergence_status",
        "NOT_PROVEN",
    )

    acceptance = continuity.get("acceptance", {})
    xau_pre_context_days = int(acceptance.get("xau_available_pre_context_days", 0))
    xau_boundary_ok = bool(acceptance.get("xau_pre_context_boundary_ok", False))
    xau_depth_ok = bool(acceptance.get("xau_pre_context_depth_ok", False))
    dxy_overlap_ok = bool(acceptance.get("dxy_overlap_ok", False))
    dxy_overlap_days = int(acceptance.get("dxy_actual_overlap_days", 0))

    feature_research_rows = int(feature.get("research_rows", 0))
    feature_minimum_required = int(feature.get("minimum_required", 0))
    feature_ok = (
        feature_status == "PASS"
        and feature_research_rows >= REQUIRED_RESEARCH_ROWS
        and feature_minimum_required >= REQUIRED_RESEARCH_ROWS
    )

    boundary_results = boundary.get("feature_sets", {})
    boundary_structural_ok = (
        boundary_status == "PASS"
        and bool(boundary_results)
        and all(
            bool(result.get("context_audit_invariant_ok", False))
            and bool(result.get("label_identity", False))
            for result in boundary_results.values()
        )
    )

    continuity_ok = (
        continuity_status == "PASS"
        and xau_boundary_ok
        and xau_depth_ok
        and xau_pre_context_days >= REQUIRED_XAU_CONTEXT_DAYS
        and dxy_overlap_ok
        and dxy_overlap_days >= REQUIRED_DXY_OVERLAP_DAYS
    )

    convergence_proven = convergence_status == "SUPPORTED"

    structural_ok = continuity_ok and feature_ok and boundary_structural_ok

    if structural_ok and convergence_proven:
        overall_status = "PASS"
        exit_code = 0
        reason = (
            "All context structural gates pass and initialization "
            "convergence is scientifically supported."
        )
    elif structural_ok:
        overall_status = "BLOCKED"
        exit_code = 2
        reason = (
            "Structural context gates pass, but initialization convergence "
            "remains NOT_PROVEN. Predictive/evidence execution is blocked."
        )
    else:
        overall_status = "BLOCKED"
        exit_code = 2
        reason = (
            "One or more structural context gates failed. "
            "Predictive/evidence execution is blocked."
        )

    payload = {
        "overall_status": overall_status,
        "reason": reason,
        "structural_gate": {
            "continuity_ok": continuity_ok,
            "feature_ok": feature_ok,
            "boundary_structural_ok": boundary_structural_ok,
            "structural_ok": structural_ok,
        },
        "continuity": {
            "status": continuity_status,
            "xau_pre_context_days": xau_pre_context_days,
            "xau_required_context_days": REQUIRED_XAU_CONTEXT_DAYS,
            "xau_boundary_ok": xau_boundary_ok,
            "xau_depth_ok": xau_depth_ok,
            "dxy_overlap_days": dxy_overlap_days,
            "dxy_required_overlap_days": REQUIRED_DXY_OVERLAP_DAYS,
            "dxy_overlap_ok": dxy_overlap_ok,
        },
        "feature_audit": {
            "status": feature_status,
            "research_rows": feature_research_rows,
            "minimum_required_rows": feature_minimum_required,
            "required_research_rows": REQUIRED_RESEARCH_ROWS,
        },
        "boundary_sensitivity": {
            "status": boundary_status,
            "structural_ok": boundary_structural_ok,
            "interpretation": (
                "Sensitivity is measured, not treated as equivalence "
                "or zero-difference stability."
            ),
        },
        "initialization_convergence": {
            "scientific_status": convergence_status,
            "supported": convergence_proven,
        },
        "acceptance_policy": (
            "Same-feed MT5 XAU pre-research context is required. "
            "XAU overlap with research is not required. "
            "Boundary sensitivity is descriptive/structural and does not "
            "imply feature equality. Initialization convergence must be "
            "scientifically supported before predictive/evidence execution."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print("PHASE 5.2 REBUILD - CONTEXT ACCEPTANCE GATE")
    print("=" * 70)
    print(f"XAU PRE-CONTEXT DAYS   : {xau_pre_context_days}")
    print(f"XAU REQUIRED DAYS      : {REQUIRED_XAU_CONTEXT_DAYS}")
    print(f"XAU BOUNDARY OK        : {xau_boundary_ok}")
    print(f"XAU DEPTH OK            : {xau_depth_ok}")
    print(f"DXY OVERLAP DAYS        : {dxy_overlap_days}")
    print(f"DXY REQUIRED DAYS       : {REQUIRED_DXY_OVERLAP_DAYS}")
    print(f"DXY OVERLAP OK          : {dxy_overlap_ok}")
    print(f"CONTINUITY              : {continuity_status}")
    print(f"FEATURE AUDIT           : {feature_status}")
    print(f"BOUNDARY STRUCTURAL     : {boundary_structural_ok}")
    print(f"CONVERGENCE             : {convergence_status}")
    print(f"STRUCTURAL GATE         : {structural_ok}")
    print(f"OVERALL STATUS          : {overall_status}")
    print(f"OUTPUT                  : {OUT.relative_to(ROOT)}")
    print(f"REASON                  : {reason}")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
