from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest

from scripts.run_xauusd_m1_walkforward import run


def _artifact(tmp_path):
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    events = []
    for i in range(30):
        ts = base + timedelta(days=i)
        direction = "bullish" if i % 2 == 0 else "bearish"
        label = i % 3 != 0
        end = ts + timedelta(hours=1)
        events.append(
            {
                "event_id": f"e{i}",
                "timestamp": ts.isoformat(),
                "direction": direction,
                "outcome": {
                    "hit_threshold_1d": label,
                    "data_availability": {"realized_end_1d": end.isoformat()},
                },
            }
        )
    artifact = {
        "contract": {"asset": "XAUUSD", "timeframe": "M1", "label": "hit_threshold_1d"},
        "dataset": {"sha256": "dataset"},
        "events_data": events,
    }
    path = tmp_path / "events.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def test_walkforward_is_deterministic_and_traceable(tmp_path):
    source = _artifact(tmp_path)
    first = run(source, tmp_path / "a.json", train_size=10, validation_size=5, step_size=5)
    second = run(source, tmp_path / "b.json", train_size=10, validation_size=5, step_size=5)
    assert first["folds"] == second["folds"]
    assert first["aggregate"] == second["aggregate"]
    assert first["split"]["fit_uses_validation_labels"] is False
    assert first["audit"] == {
        "complete_events": 30,
        "oos_unique_validation_events": 20,
        "probabilities_in_unit_interval": True,
        "training_validation_overlap": False,
        "validation_event_reuse": False,
        "all_training_labels_realized_before_validation": True,
        "source_sha256_verified_from_bytes": True,
    }
    assert all(len(fold["predictions"]) == 5 for fold in first["folds"])
    assert all(fold["prediction_methods"] == {"direction_conditional": 5} for fold in first["folds"])


def test_walkforward_embargo_excludes_unrealized_training_labels(tmp_path):
    source = _artifact(tmp_path)
    report = json.loads(source.read_text(encoding="utf-8"))
    validation_start = datetime(2025, 1, 11, tzinfo=timezone.utc)
    report["events_data"][9]["outcome"]["data_availability"]["realized_end_1d"] = (
        validation_start + timedelta(hours=1)
    ).isoformat()
    source.write_text(json.dumps(report), encoding="utf-8")
    result = run(source, tmp_path / "out.json", train_size=10, validation_size=5, step_size=5)
    assert result["folds"][0]["embargoed_events"] == 1
    assert result["folds"][0]["train_events"] == 9


def test_walkforward_rejects_overlapping_oos_windows(tmp_path):
    with pytest.raises(ValueError, match="step_size must be >= validation_size"):
        run(_artifact(tmp_path), tmp_path / "out.json", train_size=10, validation_size=5, step_size=4)


def test_walkforward_rejects_non_boolean_labels(tmp_path):
    source = _artifact(tmp_path)
    report = json.loads(source.read_text(encoding="utf-8"))
    report["events_data"][0]["outcome"]["hit_threshold_1d"] = "true"
    source.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="Outcome label must be boolean"):
        run(source, tmp_path / "out.json", train_size=10, validation_size=5, step_size=5)


def test_walkforward_rejects_missing_direction_history(tmp_path):
    source = _artifact(tmp_path)
    report = json.loads(source.read_text(encoding="utf-8"))
    for event in report["events_data"][:10]:
        event["direction"] = "bullish"
    for event in report["events_data"][10:15]:
        event["direction"] = "bearish"
    source.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="No prior observations for validation direction bearish"):
        run(source, tmp_path / "out.json", train_size=10, validation_size=5, step_size=5)
