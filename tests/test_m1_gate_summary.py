from pathlib import Path


def test_m1_gate_summary_blocks_promotion_until_validation() -> None:
    text = Path("docs/M1_GATE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Promotion remains blocked" in text
    assert "real MT5 M1 data" in text
