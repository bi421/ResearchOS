from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_xauusd_m1_negative_controls import run


def _fixture(tmp_path: Path) -> Path:
    events = []
    labels = [True, False, True, True, False, False, True, False]
    directions = ["bullish", "bullish", "bearish", "bearish", "bullish", "bearish", "bullish", "bearish"]
    for index, (label, direction) in enumerate(zip(labels, directions)):
        events.append(
            {
                "event_id": f"event-{index}",
                "direction": direction,
                "outcome": {
                    "hit_threshold_1d": label,
                    "data_availability": {"realized_end_1d": f"2021-01-{index + 2:02d}T00:00:00+00:00"},
                },
            }
        )
    path = tmp_path / "source.json"
    path.write_text(json.dumps({"events_data": events}), encoding="utf-8")
    return path


def test_label_shuffle_is_deterministic_and_preserves_multiset(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    first = run(path, seed=42)
    second = run(path, seed=42)
    assert first == second
    assert first["control"]["labels_preserved_as_multiset"] is True
    assert first["control"]["original_outcome_rate"] == first["control"]["shuffled_outcome_rate"]


def test_different_seed_changes_permutation_for_nontrivial_fixture(tmp_path: Path) -> None:
    path = _fixture(tmp_path)
    first = run(path, seed=1)
    second = run(path, seed=2)
    assert first["control"]["same_position_count"] != second["control"]["same_position_count"]


def test_requires_both_classes(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    path.write_text(
        json.dumps({
            "events_data": [
                {"event_id": "a", "direction": "bullish", "outcome": {"hit_threshold_1d": True, "data_availability": {"realized_end_1d": "2021-01-02T00:00:00+00:00"}}},
                {"event_id": "b", "direction": "bearish", "outcome": {"hit_threshold_1d": True, "data_availability": {"realized_end_1d": "2021-01-03T00:00:00+00:00"}}},
            ]
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="both outcome classes"):
        run(path)
