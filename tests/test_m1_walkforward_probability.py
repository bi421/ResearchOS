from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

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


def test_walkforward_is_deterministic_and_oos(tmp_path):
    source = _artifact(tmp_path)
    first = run(source, tmp_path / "a.json", train_size=10, validation_size=5, step_size=5)
    second = run(source, tmp_path / "b.json", train_size=10, validation_size=5, step_size=5)
    assert first["folds"] == second["folds"]
    assert first["aggregate"] == second["aggregate"]
    assert all(not fold["split_uses_validation_labels"] if "split_uses_validation_labels" in fold else True for fold in first["folds"])
    assert first["split"]["fit_uses_validation_labels"] is False


def test_walkforward_embargo_excludes_unrealized_training_labels(tmp_path):
    source = _artifact(tmp_path)
    report = json.loads(source.read_text(encoding="utf-8"))
    # Force the last pre-validation training event to remain unrealized into validation.
    validation_start = datetime(2025, 1, 11, tzinfo=timezone.utc)
    report["events_data"][9]["outcome"]["data_availability"]["realized_end_1d"] = (
        validation_start + timedelta(hours=1)
    ).isoformat()
    source.write_text(json.dumps(report), encoding="utf-8")
    result = run(source, tmp_path / "out.json", train_size=10, validation_size=5, step_size=5)
    assert result["folds"][0]["embargoed_events"] == 1
    assert result["folds"][0]["train_events"] == 9
