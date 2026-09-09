from pathlib import Path


def test_m1_ci_scope_keeps_predictive_claims_gated() -> None:
    text = Path("docs/M1_CI_SCOPE.md").read_text(encoding="utf-8")
    assert "real-data OOS validation" in text
