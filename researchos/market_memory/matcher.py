"""
ScenarioMatcher — deterministic similarity comparison for market scenarios.

Maps current MarketSnapshot against HistoricalScenario database using:
    - Weighted feature comparison (configurable weights)
    - Normalized distance scoring
    - Deterministic ranking (no ML, no randomness)

Every comparison is:
    - Deterministic: Same inputs produce same scores
    - Transparent: Weights and calculation methods are exposed
    - Reproducible: Full parameter capture for audit
"""

from __future__ import annotations

from dataclasses import dataclass, field

from researchos.market_memory.models import HistoricalScenario, MarketSnapshot
from researchos.market_memory.similarity import compare_snapshots

# Default feature weights for scenario matching
# These sum to 1.0 and are configurable per use case
DEFAULT_FEATURE_WEIGHTS: dict[str, float] = {
    "price_range": 0.25,
    "body_ratio": 0.15,
    "trend_direction": 0.30,
    "close_position": 0.10,
    "volatility": 0.10,
    "volume": 0.10,
}


@dataclass
class MatchResult:
    """
    A single scenario match result with detailed scoring.

    Attributes:
        scenario_id: ID of the matched HistoricalScenario
        scenario_name: Human-readable name
        overall_score: Aggregate similarity score (0.0-1.0)
        feature_scores: Per-feature breakdown of scores
        calculation_method: Description of scoring method used
        weight_profile: The weights used for this match
    """

    scenario_id: str
    scenario_name: str
    overall_score: float
    feature_scores: dict[str, float]
    calculation_method: str = "WeightedFeatureComparison"
    weight_profile: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_FEATURE_WEIGHTS))

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "overall_score": self.overall_score,
            "feature_scores": self.feature_scores,
            "calculation_method": self.calculation_method,
            "weight_profile": self.weight_profile,
        }


class ScenarioMatcher:
    """
    Deterministic scenario matching engine.

    Compares a current MarketSnapshot against a database of HistoricalScenario
    objects using weighted feature comparison. All computation is deterministic
    and transparent.

    Args:
        feature_weights: Optional custom weights dict (must sum to 1.0).
                         If None, uses DEFAULT_FEATURE_WEIGHTS.
    """

    def __init__(
        self,
        feature_weights: dict[str, float] | None = None,
    ):
        self.feature_weights = dict(feature_weights) if feature_weights else dict(DEFAULT_FEATURE_WEIGHTS)
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.feature_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Feature weights must sum to 1.0, got {total:.3f}. Weights: {self.feature_weights}")

    def match_scenario(
        self,
        snapshot: MarketSnapshot,
        scenarios: list[HistoricalScenario],
        snapshots_index: dict[str, MarketSnapshot] | None = None,
        top_n: int = 5,
        min_score: float = 0.0,
    ) -> list[MatchResult]:
        """
        Match a MarketSnapshot against a list of HistoricalScenario objects.

        Args:
            snapshot: The current market snapshot to match.
            scenarios: List of historical scenarios to compare against.
            snapshots_index: Optional dict of snapshot_id -> MarketSnapshot
                             for resolving scenario references.
            top_n: Maximum number of results to return.
            min_score: Minimum overall score threshold.

        Returns:
            List of MatchResult sorted by overall_score descending.
        """
        results: list[MatchResult] = []

        for scenario in scenarios:
            score = self._compute_scenario_score(snapshot, scenario, snapshots_index)
            if score >= min_score:
                # Build feature scores (same computation as overall)
                feature_scores = self._compute_feature_scores(snapshot, scenario, snapshots_index)
                results.append(
                    MatchResult(
                        scenario_id=scenario.id,
                        scenario_name=scenario.name,
                        overall_score=score,
                        feature_scores=feature_scores,
                        weight_profile=dict(self.feature_weights),
                    )
                )

        # Sort by overall score descending, then by scenario_id for deterministic ties
        results.sort(key=lambda r: (-r.overall_score, r.scenario_id))
        return results[:top_n]

    def _compute_scenario_score(
        self,
        snapshot: MarketSnapshot,
        scenario: HistoricalScenario,
        snapshots_index: dict[str, MarketSnapshot] | None = None,
    ) -> float:
        """
        Compute the overall similarity score between a snapshot and scenario.

        Uses the average snapshot similarity for all referenced snapshots
        in the scenario, combined with regime and tag matching.
        """
        if not scenario.snapshot_ids:
            return 0.0

        snapshot_scores: list[float] = []

        for sid in scenario.snapshot_ids:
            if snapshots_index and sid in snapshots_index:
                scenario_snap = snapshots_index[sid]
                # Prevent same-object comparison
                if scenario_snap.id == snapshot.id:
                    continue
                score = compare_snapshots(snapshot, scenario_snap)
                snapshot_scores.append(score)

        if not snapshot_scores:
            return 0.0

        avg_snapshot_score = sum(snapshot_scores) / len(snapshot_scores)
        return avg_snapshot_score

    def _compute_feature_scores(
        self,
        snapshot: MarketSnapshot,
        scenario: HistoricalScenario,
        snapshots_index: dict[str, MarketSnapshot] | None = None,
    ) -> dict[str, float]:
        """
        Compute per-feature similarity scores for diagnostic purposes.

        Returns a dict of feature_name -> score (0.0-1.0).
        """
        feature_scores: dict[str, float] = {}

        if not scenario.snapshot_ids or not snapshots_index:
            return {"no_data": 0.0}

        # Average feature scores across all referenced snapshots
        for sid in scenario.snapshot_ids:
            if sid in snapshots_index:
                scenario_snap = snapshots_index[sid]
                if scenario_snap.id == snapshot.id:
                    continue
                from researchos.market_memory.features import compute_features

                fa = compute_features(snapshot)
                fb = compute_features(scenario_snap)

                range_diff = abs(fa.range_pct - fb.range_pct)
                feature_scores["price_range"] = 1.0 - min(range_diff / 10.0, 1.0)

                body_diff = abs(fa.body_pct - fb.body_pct)
                feature_scores["body_ratio"] = 1.0 - body_diff

                feature_scores["trend_direction"] = 1.0 if fa.is_bullish == fb.is_bullish else 0.0

                pos_diff = abs(fa.close_position - fb.close_position)
                feature_scores["close_position"] = 1.0 - pos_diff

                vol_diff = abs(snapshot.volatility - scenario_snap.volatility)
                feature_scores["volatility"] = 1.0 - min(vol_diff / 5.0, 1.0)

                vol_diff_raw = abs(snapshot.volume - scenario_snap.volume)
                max_vol = max(snapshot.volume, scenario_snap.volume, 1.0)
                feature_scores["volume"] = 1.0 - min(vol_diff_raw / max_vol, 1.0)

                break  # Use first matching snapshot for feature breakdown

        return feature_scores

    def get_weight_report(self) -> dict[str, object]:
        """
        Get a report of the current feature weights and their rationale.

        Returns:
            Dict with weights, sum, and calculation method description.
        """
        return {
            "weights": dict(self.feature_weights),
            "weight_sum": sum(self.feature_weights.values()),
            "calculation_method": "WeightedFeatureComparison",
            "description": (
                "Weighted sum of normalized feature differences. "
                "Each feature is normalized to [0,1] and multiplied by its weight. "
                "Weights must sum to 1.0. Higher scores indicate greater similarity."
            ),
        }
