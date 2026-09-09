from pathlib import Path


def test_m1_status_requires_real_oos_gates() -> None:
    text = Path("docs/M1_PIPELINE_STATUS.md").read_text(encoding="utf-8")
    for gate in ("integrity audit", "leakage audit", "walk-forward OOS", "calibration", "evidence report"):
        assert gate in text
