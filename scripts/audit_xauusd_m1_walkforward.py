"""Independent structural audit for the XAUUSD M1 walk-forward artifact.

This auditor deliberately does not call the walk-forward implementation. It
recomputes temporal and accounting invariants from the emitted artifact so that
"the producer says it is valid" is not the same as "the artifact is valid".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def _time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"naive timestamp: {value}")
    return dt.astimezone(timezone.utc)


def audit(path: Path) -> dict:
    raw = path.read_bytes()
    report = json.loads(raw.decode("utf-8"))
    failures: list[str] = []

    if report.get("stage") != "M1_WALK_FORWARD_RAW_PROBABILITY":
        failures.append("wrong stage")
    contract = report.get("contract", {})
    if (contract.get("asset"), contract.get("timeframe"), contract.get("label")) != (
        "XAUUSD", "M1", "hit_threshold_1d"
    ):
        failures.append("wrong research contract")
    if report.get("scientific_status") != "OOS_RAW_PROBABILITY_ONLY_NO_EDGE_CLAIM":
        failures.append("scientific boundary changed or missing")

    rows = report.get("folds", [])
    if not rows:
        failures.append("no folds")

    seen_validation: set[str] = set()
    fold_count = 0
    prediction_count = 0
    for fold in rows:
        fold_count += 1
        train_ids = fold.get("training_event_ids", [])
        predictions = fold.get("predictions", [])
        if len(train_ids) != fold.get("train_events"):
            failures.append(f"fold {fold.get('fold')}: training id count mismatch")
        if len(predictions) != fold.get("validation_events"):
            failures.append(f"fold {fold.get('fold')}: prediction count mismatch")
        if len(set(train_ids)) != len(train_ids):
            failures.append(f"fold {fold.get('fold')}: duplicate training ids")

        validation_start = _time(fold["validation_start"])
        validation_end = _time(fold["validation_end"])
        train_end = _time(fold["train_end"])
        if not train_end < validation_start:
            failures.append(f"fold {fold.get('fold')}: train_end is not before validation_start")
        if validation_end < validation_start:
            failures.append(f"fold {fold.get('fold')}: validation interval reversed")

        for prediction in predictions:
            event_id = prediction.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                failures.append(f"fold {fold.get('fold')}: invalid prediction event id")
            elif event_id in seen_validation:
                failures.append(f"validation event reused: {event_id}")
            else:
                seen_validation.add(event_id)
            timestamp = _time(prediction["timestamp"])
            if not validation_start <= timestamp <= validation_end:
                failures.append(f"fold {fold.get('fold')}: prediction outside validation interval")
            probability = prediction.get("probability")
            if not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                failures.append(f"fold {fold.get('fold')}: probability outside [0,1]")
            if prediction.get("label") not in (0, 1):
                failures.append(f"fold {fold.get('fold')}: invalid prediction label")
            prediction_count += 1

        expected_model = _score(
            [float(p["probability"]) for p in predictions],
            [int(p["label"]) for p in predictions],
        )
        if expected_model != fold.get("model"):
            failures.append(f"fold {fold.get('fold')}: model score does not recompute")
        rate = fold.get("training_outcome_rate")
        expected_baseline = _score([float(rate)] * len(predictions), [int(p["label"]) for p in predictions])
        if expected_baseline != fold.get("baseline"):
            failures.append(f"fold {fold.get('fold')}: baseline score does not recompute")

    aggregate_predictions = []
    aggregate_labels = []
    aggregate_baseline = []
    for fold in rows:
        for prediction in fold.get("predictions", []):
            aggregate_predictions.append(float(prediction["probability"]))
            aggregate_labels.append(int(prediction["label"]))
            aggregate_baseline.append(float(fold["training_outcome_rate"]))
    if aggregate_predictions:
        if _score(aggregate_predictions, aggregate_labels) != report.get("aggregate", {}).get("model"):
            failures.append("aggregate model score does not recompute")
        if _score(aggregate_baseline, aggregate_labels) != report.get("aggregate", {}).get("baseline"):
            failures.append("aggregate baseline score does not recompute")

    expected_source_hash = report.get("source_artifact", {}).get("sha256")
    if not isinstance(expected_source_hash, str) or len(expected_source_hash) != 64:
        failures.append("missing source artifact SHA-256")

    return {
        "status": "PASS" if not failures else "FAIL",
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "folds": fold_count,
        "oos_unique_validation_events": len(seen_validation),
        "prediction_records": prediction_count,
        "checks": {
            "contract": not any("contract" in f for f in failures),
            "temporal_order": not any("train_end" in f or "validation interval" in f for f in failures),
            "no_validation_reuse": not any("validation event reused" in f for f in failures),
            "prediction_bounds": not any("probability outside" in f for f in failures),
            "scores_recompute": not any("score does not recompute" in f for f in failures),
            "source_identity_present": not any("source artifact SHA-256" in f for f in failures),
        },
        "failures": failures,
    }


def _score(predictions: list[float], labels: list[int]) -> dict[str, float | int]:
    if not labels or len(predictions) != len(labels):
        raise ValueError("empty or misaligned score input")
    brier = sum((p - y) ** 2 for p, y in zip(predictions, labels)) / len(labels)
    log_loss = sum(
        -(y * math.log(min(max(p, 1e-15), 1 - 1e-15))
          + (1 - y) * math.log(1 - min(max(p, 1e-15), 1 - 1e-15)))
        for p, y in zip(predictions, labels)
    ) / len(labels)
    return {
        "sample_count": len(labels),
        "brier_score": round(brier, 10),
        "log_loss": round(log_loss, 10),
        "observed_rate": round(sum(labels) / len(labels), 10),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    result = audit(args.artifact)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
