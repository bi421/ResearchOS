"""Run deterministic negative controls for the XAUUSD M1 probability stage.

This module does not alter the production estimator. It tests whether a
reported probability advantage survives when outcome labels are deliberately
shuffled. A shuffled-label control must not be treated as predictive evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(report: dict) -> list[dict]:
    rows = []
    for event in report.get("events_data", []):
        outcome = event.get("outcome") or {}
        availability = outcome.get("data_availability") or {}
        if availability.get("realized_end_1d") is None or outcome.get("hit_threshold_1d") is None:
            continue
        rows.append(
            {
                "event_id": event["event_id"],
                "direction": event["direction"],
                "label": int(outcome["hit_threshold_1d"]),
            }
        )
    return rows


def run(input_path: Path, seed: int = 20260910) -> dict:
    report = _load(input_path)
    rows = _rows(report)
    if len(rows) < 2:
        raise ValueError("Negative control requires at least two complete outcomes")
    labels = [row["label"] for row in rows]
    if len(set(labels)) < 2:
        raise ValueError("Negative control requires both outcome classes")

    shuffled = labels.copy()
    random.Random(seed).shuffle(shuffled)
    same_positions = sum(a == b for a, b in zip(labels, shuffled))
    shuffled_rate = sum(shuffled) / len(shuffled)
    original_rate = sum(labels) / len(labels)
    return {
        "stage": "XAUUSD_M1_LABEL_SHUFFLE_NEGATIVE_CONTROL",
        "scientific_status": "NEGATIVE_CONTROL_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {
            "path": str(input_path),
            "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        },
        "control": {
            "name": "label_shuffle",
            "seed": seed,
            "complete_events": len(rows),
            "original_outcome_rate": round(original_rate, 12),
            "shuffled_outcome_rate": round(shuffled_rate, 12),
            "labels_preserved_as_multiset": sorted(labels) == sorted(shuffled),
            "same_position_count": same_positions,
        },
        "expectation": "Shuffling labels destroys event-outcome association; this control is not predictive evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--output", type=Path, default=Path("artifacts/xauusd_m1_label_shuffle_negative_control.json"))
    args = parser.parse_args()
    result = run(args.input, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
