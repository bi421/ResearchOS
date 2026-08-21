"""
Market memory similarity comparison functions.

Provides deterministic functions for comparing market snapshots
and scenarios to find historical analogues.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from researchos.memory.features import compute_features
from researchos.memory.models import HistoricalScenario, MarketSnapshot


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to [0, 1] range."""
    if max_val <= min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compare_snapshots(
    a: MarketSnapshot,
    b: MarketSnapshot,
) -> float:
    """
    Compute similarity between two market snapshots.

    Returns a score between 0.0 (completely different) and 1.0 (identical).

    The comparison uses:
        - Price range similarity (normalized difference in range %)
        - Body ratio similarity
        - Trend direction match
        - Close position similarity
        - Volatility proximity

    Args:
        a: First market snapshot.
        b: Second market snapshot.

    Returns:
        Similarity score from 0.0 to 1.0.
    """
    # Extract features
    fa = compute_features(a)
    fb = compute_features(b)

    # Price range similarity (inverse of normalized difference)
    range_diff = abs(fa.range_pct - fb.range_pct)
    range_sim = 1.0 - _normalize(range_diff, 0.0, 10.0)

    # Body ratio similarity
    body_diff = abs(fa.body_pct - fb.body_pct)
    body_sim = 1.0 - body_diff

    # Trend direction (exact match = 1.0, mismatch = 0.0)
    trend_sim = 1.0 if fa.is_bullish == fb.is_bullish else 0.0

    # Close position similarity
    pos_diff = abs(fa.close_position - fb.close_position)
    pos_sim = 1.0 - pos_diff

    # Volatility proximity
    vol_diff = abs(a.volatility - b.volatility)
    vol_sim = 1.0 - _normalize(vol_diff, 0.0, 5.0)

    # Weighted combination
    weights = {
        "range": 0.25,
        "body": 0.20,
        "trend": 0.25,
        "position": 0.15,
        "volatility": 0.15,
    }

    score = (
        weights["range"] * range_sim
        + weights["body"] * body_sim
        + weights["trend"] * trend_sim
        + weights["position"] * pos_sim
        + weights["volatility"] * vol_sim
    )

    return max(0.0, min(1.0, score))


def find_similar_snapshots(
    target: MarketSnapshot,
    candidates: List[MarketSnapshot],
    top_n: int = 5,
    min_score: float = 0.0,
) -> List[Tuple[MarketSnapshot, float]]:
    """
    Find the most similar snapshots to a target.

    Args:
        target: The reference snapshot to compare against.
        candidates: List of candidate snapshots.
        top_n: Maximum number of results to return.
        min_score: Minimum similarity score threshold.

    Returns:
        List of (snapshot, score) tuples sorted by score descending.
    """
    scored: List[Tuple[MarketSnapshot, float]] = []
    for candidate in candidates:
        score = compare_snapshots(target, candidate)
        if score >= min_score:
            scored.append((candidate, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def compare_scenarios(
    a: HistoricalScenario,
    b: HistoricalScenario,
    snapshots: Dict[str, MarketSnapshot],
) -> float:
    """
    Compute similarity between two historical scenarios.

    Combines snapshot similarity, regime match, and macro context.

    Args:
        a: First scenario.
        b: Second scenario.
        snapshots: Dictionary of snapshot_id -> MarketSnapshot.

    Returns:
        Similarity score from 0.0 to 1.0.
    """
    # Regime match
    regime_sim = 1.0 if a.regime_id == b.regime_id else 0.0

    # Snapshot similarity (average of all matching pairs)
    snapshot_scores: List[float] = []
    common_ids = set(a.snapshot_ids) & set(b.snapshot_ids)
    for sid in common_ids:
        sa = snapshots.get(a.snapshot_ids[0]) if a.snapshot_ids else None
        sb = snapshots.get(b.snapshot_ids[0]) if b.snapshot_ids else None
        if sa and sb:
            snapshot_scores.append(compare_snapshots(sa, sb))

    avg_snapshot_sim = sum(snapshot_scores) / len(snapshot_scores) if snapshot_scores else 0.5

    # Tag overlap
    common_tags = set(a.tags) & set(b.tags)
    all_tags = set(a.tags) | set(b.tags)
    tag_sim = len(common_tags) / len(all_tags) if all_tags else 0.5

    # Combined score
    score = 0.4 * regime_sim + 0.4 * avg_snapshot_sim + 0.2 * tag_sim
    return max(0.0, min(1.0, score))
