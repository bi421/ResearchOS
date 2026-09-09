from pathlib import Path


def test_m1_branch_scope_is_foundational_only() -> None:
    text = Path("docs/M1_BRANCH_READY.md").read_text(encoding="utf-8")
    assert "foundational M1 contract" in text
    assert "Real-data execution" in text
