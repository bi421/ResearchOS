from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.audit_xauusd_m1_source_to_result import audit


def _source(tmp_path: Path) -> Path:
    events = []
    from datetime import datetime, timedelta, timezone

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for i in range(6):
        ts = start + timedelta(days=i)
        events.append(
            {
                "event_id": f"E{i:02d}",
                "timestamp": ts.isoformat(),
                "direction": "bullish" if i % 2 == 0 else "bearish",
                "outcome": {
                    "hit_threshold_1d": bool(i % 2),
                    "data_availability": {"realized_end_1d": (ts + timedelta(hours=1)).isoformat()},
                },
            }
        )
    path = tmp_path / "events.json"
    path.write_text(json.dumps({
        "contract": {"asset": "XAUUSD", "timeframe": "M1", "label": "hit_threshold_1d"},
        "dataset": {"sha256": "a" * 64},
        "events_data": events,
    }, indent=2), encoding="utf-8")
    return path


def _result(source: Path, tmp_path: Path, *, label: int = 0) -> Path:
    raw = source.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    predictions = [
        {"event_id": "E04", "timestamp": "2025-01-05T00:00:00+00:00", "direction": "bullish", "probability": 0.0, "label": label},
        {"event_id": "E05", "timestamp": "2025-01-06T00:00:00+00:00", "direction": "bearish", "probability": 1.0, "label": 1},
    ]
    fold_model = {
        "sample_count": 2,
        "brier_score": 0.0,
        "log_loss": 0.0,
        "observed_rate": 0.5,
    }
    fold_baseline = {
        "sample_count": 2,
        "brier_score": 0.25,
        "log_loss": 0.6931471806,
        "observed_rate": 0.5,
    }
    result = {
        "stage": "M1_WALK_FORWARD_RAW_PROBABILITY",
        "scientific_status": "OOS_RAW_PROBABILITY_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {"sha256": source_sha},
        "dataset": {"sha256": "a" * 64},
        "contract": {"asset": "XAUUSD", "timeframe": "M1", "label": "hit_threshold_1d"},
        "split": {"train_size": 4, "validation_size": 2, "step_size": 2},
        "folds": [{
            "fold": 1,
            "train_start": "2025-01-01T00:00:00+00:00",
            "train_end": "2025-01-04T00:00:00+00:00",
            "validation_start": "2025-01-05T00:00:00+00:00",
            "validation_end": "2025-01-06T00:00:00+00:00",
            "train_events": 4,
            "validation_events": 2,
            "embargoed_events": 0,
            "training_event_ids": ["E00", "E01", "E02", "E03"],
            "training_outcome_rate": 0.5,
            "predictions": predictions,
            "model": fold_model,
            "baseline": fold_baseline,
        }],
        "aggregate": {"model": fold_model, "baseline": fold_baseline},
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    return path


def test_source_to_result_audit_accepts_valid_result(tmp_path: Path):
    source = _source(tmp_path)
    result = _result(source, tmp_path, label=0)
    output = audit(source, result)
    assert output["status"] == "PASS"
    assert output["checks"]["probability_recomputation"] is True
    assert output["checks"]["score_recomputation"] is True


def test_source_to_result_audit_rejects_tampered_label(tmp_path: Path):
    source = _source(tmp_path)
    result = _result(source, tmp_path, label=1)
    output = audit(source, result)
    assert output["status"] == "FAIL"
    assert any("label mismatch" in failure for failure in output["failures"])


def test_source_to_result_audit_rejects_tampered_training_membership(tmp_path: Path):
    source = _source(tmp_path)
    result = _result(source, tmp_path, label=0)
    payload = json.loads(result.read_text(encoding="utf-8"))
    payload["folds"][0]["training_event_ids"][-1] = "E09"
    result.write_text(json.dumps(payload), encoding="utf-8")
    output = audit(source, result)
    assert output["status"] == "FAIL"
    assert any("training membership differs" in failure for failure in output["failures"])


def test_source_to_result_audit_rejects_wrong_source_hash(tmp_path: Path):
    source = _source(tmp_path)
    result = _result(source, tmp_path, label=0)
    payload = json.loads(result.read_text(encoding="utf-8"))
    payload["source_artifact"]["sha256"] = "b" * 64
    result.write_text(json.dumps(payload), encoding="utf-8")
    output = audit(source, result)
    assert output["status"] == "FAIL"
    assert any("SHA-256" in failure for failure in output["failures"])


def test_source_to_result_audit_rejects_tampered_dataset_identity(tmp_path: Path):
    source = _source(tmp_path)
    result = _result(source, tmp_path, label=0)
    payload = json.loads(result.read_text(encoding="utf-8"))
    payload["dataset"]["sha256"] = "c" * 64
    result.write_text(json.dumps(payload), encoding="utf-8")
    output = audit(source, result)
    assert output["status"] == "FAIL"
    assert any("dataset SHA-256" in failure for failure in output["failures"])
