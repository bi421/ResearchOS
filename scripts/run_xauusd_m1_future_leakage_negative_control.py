"""Deliberately inject future validation data into training metadata.

This control is intentionally invalid: the independent source-to-result
auditor must reject the emitted result. It is not evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def run(result_path: Path, output_path: Path) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    folds = result.get("folds") or []
    if not folds:
        raise ValueError("result contains no folds")

    first = folds[0]
    validation = first.get("predictions") or []
    if not validation:
        raise ValueError("first fold contains no validation predictions")
    future_event_id = validation[0].get("event_id")
    if not isinstance(future_event_id, str) or not future_event_id:
        raise ValueError("first validation prediction has no event_id")

    corrupted = json.loads(json.dumps(result, ensure_ascii=False))
    training_ids = corrupted["folds"][0].get("training_event_ids")
    if not isinstance(training_ids, list):
        raise ValueError("first fold has no training_event_ids")
    if future_event_id in training_ids:
        raise ValueError("selected validation event is already in training set")
    training_ids.append(future_event_id)

    corrupted["negative_control"] = {
        "stage": "XAUUSD_M1_FUTURE_LEAKAGE_NEGATIVE_CONTROL",
        "scientific_status": "NEGATIVE_CONTROL_ONLY_EXPECT_AUDIT_FAIL",
        "violation": "validation_event_injected_into_training_membership",
        "injected_fold": 1,
        "injected_future_event_id": future_event_id,
        "expected_audit_status": "FAIL",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(corrupted, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return corrupted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
