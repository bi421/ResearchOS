from pathlib import Path


def test_m1_handoff_points_to_real_data_oos() -> None:
    text = Path("docs/M1_HANDOFF.md").read_text(encoding="utf-8")
    assert "real MT5 XAUUSD M1 integration" in text
    assert "OOS evaluation" in text
