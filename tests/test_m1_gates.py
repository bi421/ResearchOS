from pathlib import Path


def test_m1_gates_include_real_data_and_oos_controls() -> None:
    text = Path("docs/M1_GATES.md").read_text(encoding="utf-8")
    assert "Real MT5 XAUUSD M1 dataset identity verified" in text
    assert "Walk-forward predictions are strictly out-of-sample" in text
    assert "Calibration uses prior outcomes only" in text
