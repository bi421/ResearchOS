"""Strict adapter for outcome-grounded probability calibration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from researchos.market_memory.probability_calibration import ProbabilityCalibrator
from researchos.objects.evidence import EvidenceRegistry


def load_ground_truth(path: str | Path) -> dict[str, bool]:
    """Load explicit binary outcomes; reject missing or malformed labels."""
    outcome_path = Path(path)
    if not outcome_path.exists():
        raise FileNotFoundError(f"Ground-truth outcomes not found: {outcome_path}")
    raw: Any = json.loads(outcome_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Ground-truth outcomes must be a JSON object keyed by evidence id.")

    outcomes: dict[str, bool] = {}
    for evidence_id, record in raw.items():
        if not isinstance(evidence_id, str) or not isinstance(record, dict):
            raise ValueError("Each outcome record must be an object keyed by evidence id.")
        if "actual_is_win" not in record or not isinstance(record["actual_is_win"], bool):
            raise ValueError(f"Missing explicit boolean actual_is_win for {evidence_id}.")
        outcomes[evidence_id] = record["actual_is_win"]
    return outcomes


def ingest_and_calibrate(outcomes_file_path: str, registry: EvidenceRegistry) -> str:
    """Fit calibration only when real, matched, binary outcomes are available."""
    outcomes = load_ground_truth(outcomes_file_path)
    matched = sum(1 for eid in registry.evidence_ids if eid in outcomes)
    print(f"[Ingest] Loaded {len(outcomes)} outcomes; matched evidence: {matched}.")

    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(registry, outcomes)  # intentionally raises on insufficient/invalid data
    report = calibrator.calibrate(registry)
    return calibrator.generate_report(report, registry)


if __name__ == "__main__":
    raise SystemExit(
        "This adapter requires an EvidenceRegistry supplied by the research pipeline; "
        "it will not manufacture evidence or perform mock calibration."
    )
