from pathlib import Path


def test_m1_boundary_disallows_predictive_claims() -> None:
    text = Path("docs/M1_IMPLEMENTATION_BOUNDARY.md").read_text(encoding="utf-8")
    assert "does not" in text
    assert "claim a trading edge" in text
    assert "synthetic or mock fallback" in text
