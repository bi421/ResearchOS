from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.audit_xauusd_m1_source_to_result import audit
from scripts.run_xauusd_m1_future_leakage_negative_control import run


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = {
        "contract": {"asset": "XAUUSD", "timeframe": "M1", "label": "hit_threshold_1d"},
        "dataset": {"sha256": "a" * 64},
        "events_data": [
            {"event_id": "e1", "timestamp": "2025-01-01T00:00:00+00:00", "direction": "bullish", "outcome": {"hit_threshold_1d": True, "data_availability": {"realized_end_1d": "2025-01-01T00:30:00+00:00"}}},
            {"event_id": "e2", "timestamp": "2025-01-01T01:00:00+00:00", "direction": "bullish", "outcome": {"hit_threshold_1d": False, "data_availability": {"realized_end_1d": "2025-01-01T01:30:00+00:00"}}},
            {"event_id": "e3", "timestamp": "2025-01-01T02:00:00+00:00", "direction": "bullish", "outcome": {"hit_threshold_1d": True, "data_availability": {"realized_end_1d": "2025-01-02T02:00:00+00:00"}}},
        ],
    }
    source_path = tmp_path / "source.json"
    source_path.write_text(json.dumps(source, separators=(",", ":")), encoding="utf-8")
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    result = {
        "stage": "M1_WALK_FORWARD_RAW_PROBABILITY",
        "scientific_status": "OOS_RAW_PROBABILITY_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {"sha256": source_sha},
        "contract": source["contract"],
        "dataset": {"sha256": source["dataset"]["sha256"]},
        "split": {"train_size": 2, "validation_size": 1, "step_size": 1},
        "folds": [{
            "training_event_ids": ["e1", "e2"],
            "train_events": 2,
            "validation_events": 1,
            "embargoed_events": 0,
            "train_start": "2025-01-01T00:00:00+00:00",
            "train_end": "2025-01-01T01:00:00+00:00",
            "validation_start": "2025-01-01T02:00:00+00:00",
            "validation_end": "2025-01-01T02:00:00+00:00",
            "training_outcome_rate": 0.5,
            "predictions": [{"event_id": "e3", "timestamp": "2025-01-01T02:00:00+00:00", "direction": "bullish", "label": 1, "probability": 0.5, "method": "direction_conditional"}],
            "model": {"sample_count": 1, "brier_score": 0.25, "log_loss": 0.6931471806, "observed_rate": 1.0},
            "baseline": {"sample_count": 1, "brier_score": 0.25, "log_loss": 0.6931471806, "observed_rate": 1.0},
        }],
        "aggregate": {
            "model": {"sample_count": 1, "brier_score": 0.25, "log_loss": 0.6931471806, "observed_rate": 1.0},
            "baseline": {"sample_count": 1, "brier_score": 0.25, "log_loss": 0.6931471806, "observed_rate": 1.0},
        },
    }
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    return source_path, result_path


def test_future_leakage_control_is_rejected_by_independent_auditor(tmp_path: Path) -> None:
    source_path, result_path = _fixture(tmp_path)
    corrupted_path = tmp_path / "corrupted.json"
    run(result_path, corrupted_path)
    audited = audit(source_path, corrupted_path)
    assert audited["status"] == "FAIL"
    assert any("training membership differs" in failure for failure in audited["failures"])


def test_control_injects_validation_event_into_training(tmp_path: Path) -> None:
    _, result_path = _fixture(tmp_path)
    corrupted_path = tmp_path / "corrupted.json"
    corrupted = run(result_path, corrupted_path)
    assert corrupted["negative_control"]["expected_audit_status"] == "FAIL"
    assert corrupted["negative_control"]["injected_future_event_id"] == "e3"
    assert "e3" in corrupted["folds"][0]["training_event_ids"]
