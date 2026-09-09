from pathlib import Path


def test_next_gate_requires_mt5_xauusd_m1() -> None:
    text = Path("docs/M1_NEXT_GATE.md").read_text(encoding="utf-8")
    assert "MT5 XAUUSD M1" in text
    assert "another gold instrument" in text
