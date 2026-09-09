"""Calibrate XAUUSD M1 walk-forward probabilities using prior OOS outcomes only.

This stage is deliberately separate from the in-sample ProbabilityCalibrator.
Each validation prediction is calibrated only from earlier OOS predictions whose
realized outcome endpoint is strictly before the prediction timestamp.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

MIN_SAMPLES = 10


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return parsed.astimezone(timezone.utc)


def _pava(rows: list[tuple[float, int]]) -> tuple[tuple[float, float], ...]:
    ordered = sorted(rows, key=lambda item: (item[0], item[1]))
    blocks: list[list[float | int]] = []
    for x, y in ordered:
        blocks.append([x, y, 1, y])
        while len(blocks) >= 2:
            a, b = blocks[-2], blocks[-1]
            if float(a[3]) / int(a[2]) <= float(b[3]) / int(b[2]):
                break
            blocks[-2:] = [[
                min(float(a[0]), float(b[0])),
                0.0,
                int(a[2]) + int(b[2]),
                float(a[3]) + float(b[3]),
            ]]
    return tuple(
        (float(block[0]), round(max(0.0, min(1.0, float(block[3]) / int(block[2]))), 12))
        for block in blocks
    )


def _predict(breakpoints: tuple[tuple[float, float], ...], probability: float) -> float:
    xs = tuple(x for x, _ in breakpoints)
    index = bisect_right(xs, probability) - 1
    if index < 0:
        index = 0
    return breakpoints[index][1]


def _score(predictions: list[float], labels: list[int]) -> dict[str, float | int]:
    if not predictions or len(predictions) != len(labels):
        raise ValueError("Predictions and labels must be non-empty and aligned")
    brier = sum((p - y) ** 2 for p, y in zip(predictions, labels)) / len(labels)
    log_loss = 0.0
    for p, y in zip(predictions, labels):
        p = min(max(p, 1e-15), 1.0 - 1e-15)
        log_loss += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return {
        "sample_count": len(labels),
        "brier_score": round(brier, 10),
        "log_loss": round(log_loss / len(labels), 10),
        "observed_rate": round(sum(labels) / len(labels), 10),
    }


def _source_rows(source: dict) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for event in source.get("events_data", []):
        event_id = event.get("event_id")
        outcome = event.get("outcome") or {}
        endpoint = (outcome.get("data_availability") or {}).get("realized_end_1d")
        label = outcome.get("hit_threshold_1d")
        if endpoint is None or label is None:
            continue
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("Complete source event requires event_id")
        if event_id in rows:
            raise ValueError(f"Duplicate source event_id: {event_id}")
        if not isinstance(label, bool):
            raise ValueError(f"Source outcome label must be boolean: {event_id}")
        timestamp = _time(event["timestamp"])
        realized_end = _time(endpoint)
        if realized_end <= timestamp:
            raise ValueError(f"Source realized_end must be after event timestamp: {event_id}")
        rows[event_id] = {
            "timestamp": timestamp,
            "realized_end": realized_end,
            "label": int(label),
            "direction": event.get("direction"),
        }
    return rows


def run(source_path: Path, result_path: Path, output_path: Path) -> dict:
    source_raw = source_path.read_bytes()
    result_raw = result_path.read_bytes()
    source = json.loads(source_raw.decode("utf-8"))
    result = json.loads(result_raw.decode("utf-8"))
    if result.get("stage") != "M1_WALK_FORWARD_RAW_PROBABILITY":
        raise ValueError("Input result is not the required walk-forward stage")
    source_contract = source.get("contract", {})
    result_contract = result.get("contract", {})
    if source_contract != result_contract:
        raise ValueError("Source and result contracts differ")
    if source_contract != {"asset": "XAUUSD", "timeframe": "M1", "label": "hit_threshold_1d"}:
        raise ValueError("Unexpected XAUUSD M1 contract")
    if result.get("source_artifact", {}).get("sha256") != hashlib.sha256(source_raw).hexdigest():
        raise ValueError("Result source artifact SHA-256 does not match supplied source")

    source_rows = _source_rows(source)
    predictions: list[dict] = []
    seen: set[str] = set()
    for fold in result.get("folds", []):
        for prediction in fold.get("predictions", []):
            event_id = prediction.get("event_id")
            if event_id in seen:
                raise ValueError(f"Duplicate OOS prediction event_id: {event_id}")
            if event_id not in source_rows:
                raise ValueError(f"Prediction event is missing from source: {event_id}")
            if not isinstance(prediction.get("probability"), (int, float)):
                raise ValueError(f"Invalid probability: {event_id}")
            p = float(prediction["probability"])
            if not math.isfinite(p) or not 0.0 <= p <= 1.0:
                raise ValueError(f"Probability outside [0,1]: {event_id}")
            source_row = source_rows[event_id]
            if source_row["timestamp"] != _time(prediction["timestamp"]):
                raise ValueError(f"Prediction timestamp differs from source: {event_id}")
            if source_row["label"] != int(prediction["label"]):
                raise ValueError(f"Prediction label differs from source: {event_id}")
            predictions.append({
                "event_id": event_id,
                "timestamp": source_row["timestamp"],
                "probability": p,
                "label": source_row["label"],
            })
            seen.add(event_id)

    predictions.sort(key=lambda row: (row["timestamp"], row["event_id"]))
    if len(predictions) < MIN_SAMPLES + 1:
        raise ValueError("At least 11 OOS predictions are required for leakage-safe calibration")

    calibrated: list[float] = []
    raw_eligible: list[float] = []
    labels: list[int] = []
    records: list[dict] = []
    warmup_count = 0
    for index, row in enumerate(predictions):
        prior = [
            item for item in predictions[:index]
            if item["timestamp"] < row["timestamp"]
            and source_rows[item["event_id"]]["realized_end"] < row["timestamp"]
        ]
        classes = {item["label"] for item in prior}
        if len(prior) < MIN_SAMPLES or classes != {0, 1}:
            warmup_count += 1
            continue
        breakpoints = _pava([(item["probability"], item["label"]) for item in prior])
        calibrated_probability = _predict(breakpoints, row["probability"])
        raw_eligible.append(row["probability"])
        calibrated.append(calibrated_probability)
        labels.append(row["label"])
        records.append({
            "event_id": row["event_id"],
            "timestamp": row["timestamp"].isoformat(),
            "raw_probability": round(row["probability"], 12),
            "calibrated_probability": round(calibrated_probability, 12),
            "label": row["label"],
            "calibration_training_event_ids": [item["event_id"] for item in prior],
        })

    if len(records) < 1:
        raise ValueError("No OOS predictions have sufficient leakage-safe calibration history")

    output = {
        "stage": "M1_OOS_ISOTONIC_CALIBRATION",
        "scientific_status": "OOS_CALIBRATION_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {"path": str(source_path), "sha256": hashlib.sha256(source_raw).hexdigest()},
        "result_artifact": {"path": str(result_path), "sha256": hashlib.sha256(result_raw).hexdigest()},
        "contract": result_contract,
        "calibration": {
            "method": "isotonic_pava",
            "minimum_prior_samples": MIN_SAMPLES,
            "fit_uses_current_validation_label": False,
            "fit_uses_future_outcomes": False,
            "temporal_rule": "training realized_end < current validation timestamp",
            "total_oos_predictions": len(predictions),
            "eligible_oos_predictions": len(records),
            "warmup_excluded_predictions": warmup_count,
        },
        "raw_score": _score(raw_eligible, labels),
        "calibrated_score": _score(calibrated, labels),
        "predictions": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/xauusd_m1_oos_calibration.json"))
    args = parser.parse_args()
    output = run(args.source, args.result, args.output)
    print(f"OOS samples: {len(output['predictions'])}")
    print(f"Raw Brier: {output['raw_score']['brier_score']}")
    print(f"Calibrated Brier: {output['calibrated_score']['brier_score']}")
    print(f"Artifact: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
