from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.run_xauusd_m1_oos_calibration import run


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    events = []
    labels = [True, False] * 6
    for index, label in enumerate(labels):
        events.append({
            "event_id": f"e{index + 1}",
            "timestamp": f"2025-01-01T{index:02d}:00:00+00:00",
            "direction": "bullish",
            "outcome": {
                "hit_threshold_1d": label,
                "data_availability": {
                    "realized_end_1d": f"2025-01-01T{index:02d}:30:00+00:00"
                },
            },
        })
    source = {
        "contract": {"asset": "XAUUSD", "timeframe": "M1", "label": "hit_threshold_1d"},
        "dataset": {"sha256": "a" * 64},
        "events_data": events,
    }
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source, separators=(",", ":")), encoding="utf-8")
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    predictions = []
    for index, label in enumerate(labels):
        predictions.append({
            "event_id": f"e{index + 1}",
            "timestamp": f"2025-01-01T{index:02d}:00:00+00:00",
            "direction": "bullish",
            "probability": 0.2 if label else 0.8,
            "label": int(label),
        })
    result = {
        "stage": "M1_WALK_FORWARD_RAW_PROBABILITY",
        "scientific_status": "OOS_RAW_PROBABILITY_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {"sha256": source_sha},
        "contract": source["contract"],
        "dataset": source["dataset"],
        "folds": [{"predictions": predictions}],
    }
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    return source_path, result_path


def test_oos_calibration_uses_prior_realized_outcomes_only(tmp_path: Path) -> None:
    source, result = _fixture(tmp_path)
    output = run(source, result, tmp_path / "calibrated.json")
    assert output["scientific_status"] == "OOS_CALIBRATION_ONLY_NO_EDGE_CLAIM"
    assert len(output["predictions"]) == 12 - 10
    assert all(
        set(record["calibration_training_event_ids"]).issubset({f"e{i}" for i in range(1, 11)})
        for record in output["predictions"]
    )
    assert all(
        "e11" not in record["calibration_training_event_ids"]
        for record in output["predictions"]
    )


def test_oos_calibration_fails_without_both_prior_classes(tmp_path: Path) -> None:
    source, result = _fixture(tmp_path)
    data = json.loads(result.read_text(encoding="utf-8"))
    for prediction in data["folds"][0]["predictions"][:10]:
        prediction["label"] = 1
    result.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="classes"):
        run(source, result, tmp_path / "calibrated.json")
