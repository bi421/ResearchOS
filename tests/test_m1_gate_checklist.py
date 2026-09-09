from pathlib import Path


def test_foundational_m1_gates_are_marked_complete() -> None:
    text = Path("docs/M1_GATES_CHECKLIST.md").read_text(encoding="utf-8")
    assert "[x] Direction-aware Outcome Engine semantics" in text
    assert "[x] Deterministic M1 event extraction" in text
    assert "[x] Explicit immutable outcome contract" in text
