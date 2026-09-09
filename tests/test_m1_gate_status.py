from pathlib import Path


def test_m1_gate_status_requires_real_data_validation() -> None:
    text = Path("docs/M1_GATE_STATUS.md").read_text(encoding="utf-8")
    assert "Real-data validation remains intentionally open" in text
