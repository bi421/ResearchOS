from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.create_xauusd_m1_evidence_envelope import build_envelope


def _write_chain(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    raw = tmp_path / "XAUUSD_MT5_M1.csv"
    source = tmp_path / "source.json"
    result = tmp_path / "result.json"
    audit = tmp_path / "audit.json"
    raw.write_bytes(b"time,open,high,low,close,tick_volume\n1,1,1,1,1,1\n")
    import hashlib
    raw_sha = hashlib.sha256(raw.read_bytes()).hexdigest()
    source_data = {
        "contract": {
            "asset": "XAUUSD", "timeframe": "M1", "event": "SMA20/100 crossover",
            "label": "hit_threshold_1d", "horizon_days": 1, "threshold_return": 0.0,
            "price_field": "close", "direction_aware": True,
        },
        "dataset": {"sha256": raw_sha},
        "events_data": [],
    }
    source.write_text(json.dumps(source_data), encoding="utf-8")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    result_data = {
        "stage": "M1_WALK_FORWARD_RAW_PROBABILITY",
        "scientific_status": "OOS_RAW_PROBABILITY_ONLY_NO_EDGE_CLAIM",
        "source_artifact": {"sha256": source_sha},
        "dataset": {"sha256": raw_sha},
        "contract": source_data["contract"],
        "split": {
            "train_size": 1, "validation_size": 1, "step_size": 1,
            "embargo_rule": "training realized_end < validation_start",
            "fit_uses_validation_labels": False,
            "validation_windows_overlap": False,
        },
    }
    result.write_text(json.dumps(result_data), encoding="utf-8")
    result_sha = hashlib.sha256(result.read_bytes()).hexdigest()
    audit.write_text(json.dumps({
        "status": "PASS", "source_sha256": source_sha, "result_artifact_sha256": result_sha,
    }), encoding="utf-8")
    return raw, source, result, audit


def test_valid_chain_builds(tmp_path: Path) -> None:
    paths = _write_chain(tmp_path)
    envelope = build_envelope(*paths, code_commit="abc123")
    assert envelope["stage"] == "XAUUSD_M1_EVIDENCE_ENVELOPE"
    assert envelope["scientific_status"] == "REPRODUCIBILITY_LINEAGE_ONLY_NO_EDGE_CLAIM"
    assert len(envelope["envelope_sha256"]) == 64
    assert envelope["identity"]["code_commit"] == "abc123"


@pytest.mark.parametrize("target", ["raw", "source", "result", "audit"])
def test_chain_fails_closed_when_any_artifact_changes(tmp_path: Path, target: str) -> None:
    raw, source, result, audit = _write_chain(tmp_path)
    paths = {"raw": raw, "source": source, "result": result, "audit": audit}
    path = paths[target]
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ValueError):
        build_envelope(raw, source, result, audit, code_commit="abc123")


def test_dataset_identity_must_bind_to_raw_bytes(tmp_path: Path) -> None:
    raw, source, result, audit = _write_chain(tmp_path)
    source_data = json.loads(source.read_text(encoding="utf-8"))
    source_data["dataset"]["sha256"] = "0" * 64
    source.write_text(json.dumps(source_data), encoding="utf-8")
    with pytest.raises(ValueError, match="raw CSV bytes"):
        build_envelope(raw, source, result, audit, code_commit="abc123")
