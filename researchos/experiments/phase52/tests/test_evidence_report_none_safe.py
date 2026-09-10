from __future__ import annotations

import json

from scripts.run_phase52_evidence import _write_report


def test_report_writer_handles_blocked_result(tmp_path) -> None:
    payload = {
        "repository_commit": "test",
        "common_sample": {"count": 1246, "first": "2021-01-04", "last": "2025-12-30"},
        "sources": {"DXY": {"identity": "Dukascopy dollaridxusd; secondary DXY series"}},
        "results": {
            "PRICE_ONLY": {
                "outcome": "BLOCKED",
                "model": None,
                "cost": None,
                "significance": None,
            },
            "PRICE + DXY": {"outcome": "BLOCKED", "model": None, "cost": None, "significance": None},
            "PRICE + US10Y": {"outcome": "BLOCKED", "model": None, "cost": None, "significance": None},
            "PRICE + VIX": {"outcome": "BLOCKED", "model": None, "cost": None, "significance": None},
            "PRICE + ALL": {"outcome": "BLOCKED", "model": None, "cost": None, "significance": None},
        },
        "reproducibility_hashes": {},
    }
    output = tmp_path / "report.md"
    _write_report(output, payload)
    text = output.read_text(encoding="utf-8")
    assert "PRICE_ONLY" in text
    assert "BLOCKED" in text
    assert "—" in text
    json.dumps(payload)
