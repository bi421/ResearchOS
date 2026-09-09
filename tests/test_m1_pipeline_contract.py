from pathlib import Path


def test_m1_pipeline_documentation_has_scientific_boundary() -> None:
    text = Path("docs/M1_RESEARCH_PIPELINE.md").read_text(encoding="utf-8")
    assert "No synthetic/mock fallback" in text
    assert "does **not** claim predictive edge" in text
    assert "Calibration fitted only from prior observations" in text
