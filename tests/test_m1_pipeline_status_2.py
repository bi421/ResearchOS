from pathlib import Path


def test_m1_pipeline_forbids_mock_fallback() -> None:
    text = Path("docs/M1_PIPELINE_STATUS.md").read_text(encoding="utf-8")
    assert "no synthetic/mock fallback" in text.lower()
