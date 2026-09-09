"""Run a strict, direction-conditioned XAUUSD M1 walk-forward probability study.

This stage consumes the real event/outcome artifact produced by
``run_xauusd_m1_real_pipeline.py``. It estimates P(hit_1d | crossover direction)
using only outcomes whose realized endpoint is strictly before each validation
window. The unconditional training outcome rate is the baseline.

No validation labels are used for fitting. No synthetic/mock fallback exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _complete_rows(report: dict) -> list[dict]:
    rows = []
    for event in report.get("events_data", []):
        outcome = event.get("outcome") or {}
        endpoint = (outcome.get("data_availability") or {}).get("realized_end_1d")
        label = outcome.get("hit_threshold_1d")
        if endpoint is not None and label is not None:
            rows.append(
                {
                    "event_id": event["event_id"],
                    "timestamp": _parse_time(event["timestamp"]),
                    "realized_end": _parse_time(endpoint),
                    "direction": event["direction"],
                    "label": int(bool(label)),
                }
            )
    return sorted(rows, key=lambda row: (row["timestamp"], row["event_id"]))


def _estimate(train: list[dict], row: dict) -> tuple[float, str]:
    """Estimate conditional hit probability from prior training outcomes only."""
    if not train:
        raise ValueError("Cannot estimate probability without training observations")
    same_direction = [item for item in train if item["direction"] == row["direction"]]
    if same_direction:
        return sum(item["label"] for item in same_direction) / len(same_direction), "direction_conditional"
    return sum(item["label"] for item in train) / len(train), "unconditional_fallback"


def _score(predictions: list[float], labels: list[int]) -> dict[str, float | int]:
    if not labels or len(predictions) != len(labels):
        raise ValueError("Predictions and labels must be non-empty and aligned")
    brier = sum((p - y) ** 2 for p, y in zip(predictions, labels)) / len(labels)
    log_loss = 0.0
    import math
    for p, y in zip(predictions, labels):
        p = min(max(p, 1e-15), 1.0 - 1e-15)
        log_loss += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return {
        "sample_count": len(labels),
        "brier_score": round(brier, 10),
        "log_loss": round(log_loss / len(labels), 10),
        "observed_rate": round(sum(labels) / len(labels), 10),
    }


def run(input_path: Path, output_path: Path, train_size: int, validation_size: int, step_size: int) -> dict:
    if train_size <= 0 or validation_size <= 0 or step_size <= 0:
        raise ValueError("train_size, validation_size and step_size must be positive")
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    raw = input_path.read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    report = json.loads(raw.decode("utf-8"))
    contract = report.get("contract", {})
    dataset = report.get("dataset", {})
    if contract.get("asset") != "XAUUSD" or contract.get("timeframe") != "M1":
        raise ValueError("Input artifact is not the XAUUSD M1 contract")
    if contract.get("label") != "hit_threshold_1d":
        raise ValueError("Input artifact does not use the required 1-day label")
    rows = _complete_rows(report)
    if len(rows) < train_size + validation_size:
        raise ValueError("Insufficient complete events for requested walk-forward configuration")

    folds = []
    all_predictions: list[float] = []
    all_baseline: list[float] = []
    all_labels: list[int] = []
    start = 0
    while start + train_size + validation_size <= len(rows):
        val_start_idx = start + train_size
        val_end_idx = val_start_idx + validation_size
        validation = rows[val_start_idx:val_end_idx]
        validation_start = validation[0]["timestamp"]
        train_pool = rows[:val_start_idx]
        # Embargo: a training label must be fully realized before validation starts.
        train = [item for item in train_pool if item["realized_end"] < validation_start]
        if not train:
            raise RuntimeError(f"No leakage-safe training observations for fold starting {validation_start.isoformat()}")
        train_rate = sum(item["label"] for item in train) / len(train)
        fold_predictions = []
        fold_labels = []
        methods: dict[str, int] = {}
        for row in validation:
            probability, method = _estimate(train, row)
            fold_predictions.append(probability)
            fold_labels.append(row["label"])
            methods[method] = methods.get(method, 0) + 1
        fold_score = _score(fold_predictions, fold_labels)
        baseline_score = _score([train_rate] * len(fold_labels), fold_labels)
        folds.append(
            {
                "fold": len(folds) + 1,
                "train_start": train[0]["timestamp"].isoformat(),
                "train_end": train[-1]["timestamp"].isoformat(),
                "validation_start": validation[0]["timestamp"].isoformat(),
                "validation_end": validation[-1]["timestamp"].isoformat(),
                "train_events": len(train),
                "validation_events": len(validation),
                "embargoed_events": len(train_pool) - len(train),
                "training_outcome_rate": round(train_rate, 10),
                "prediction_methods": methods,
                "model": fold_score,
                "baseline": baseline_score,
            }
        )
        all_predictions.extend(fold_predictions)
        all_baseline.extend([train_rate] * len(fold_labels))
        all_labels.extend(fold_labels)
        start += step_size

    model_score = _score(all_predictions, all_labels)
    baseline_score = _score(all_baseline, all_labels)
    report_out = {
        "stage": "M1_WALK_FORWARD_RAW_PROBABILITY",
        "scientific_status": "OOS_RAW_PROBABILITY_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {"path": str(input_path), "sha256": source_sha256},
        "dataset": dataset,
        "contract": contract,
        "split": {
            "train_size": train_size,
            "validation_size": validation_size,
            "step_size": step_size,
            "embargo_rule": "training realized_end < validation_start",
            "fit_uses_validation_labels": False,
        },
        "folds": folds,
        "aggregate": {"model": model_score, "baseline": baseline_score},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report_out, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/xauusd_m1_walkforward.json"))
    parser.add_argument("--train-size", type=int, default=2000)
    parser.add_argument("--validation-size", type=int, default=500)
    parser.add_argument("--step-size", type=int, default=500)
    args = parser.parse_args()
    result = run(args.input, args.output, args.train_size, args.validation_size, args.step_size)
    print(f"Folds: {len(result['folds'])}")
    print(f"OOS samples: {result['aggregate']['model']['sample_count']}")
    print(f"Model Brier: {result['aggregate']['model']['brier_score']}")
    print(f"Baseline Brier: {result['aggregate']['baseline']['brier_score']}")
    print(f"Model LogLoss: {result['aggregate']['model']['log_loss']}")
    print(f"Baseline LogLoss: {result['aggregate']['baseline']['log_loss']}")
    print(f"Artifact: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
