from pathlib import Path


def test_m1_implementation_keeps_d1_extractor_compatible() -> None:
    text = Path("docs/M1_IMPLEMENTATION_NOTE.md").read_text(encoding="utf-8")
    assert "existing D1 extractor" in text
    assert "single forward-label implementation" in text
