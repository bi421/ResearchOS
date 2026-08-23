"""
ResearchOS Macro Intelligence Layer - Relationship Engine

Main orchestrator for historical relationship analysis.
Combines correlation, lag, regime-conditional, and break detection.
"""

from __future__ import annotations

from typing import Any

from macro_intelligence.relationships.break_detection import (
    detect_structural_breaks,
)
from macro_intelligence.relationships.correlation import (
    approximate_p_value,
    classify_relationship,
    pearson_correlation,
    spearman_correlation,
)
from macro_intelligence.relationships.lag_analysis import find_optimal_lag
from macro_intelligence.relationships.models import (
    ALGORITHM_VERSION,
    CorrelationResult,
    LagRelationship,
    RegimeRelationship,
    RelationshipResult,
    RollingCorrelationResult,
    StructuralBreak,
)
from macro_intelligence.relationships.regime_relationship import (
    compute_all_regime_correlations,
)
from macro_intelligence.statistics.provenance import StatisticalProvenance


class RelationshipEngine:
    """
    Main orchestrator for historical relationship analysis.

    Pure, deterministic, stateless engine.
    """

    def __init__(self):
        self._version = ALGORITHM_VERSION

    @property
    def version(self) -> str:
        return self._version

    def _build_provenance(
        self,
        method: str,
        dataset_id: str | None = None,
        dataset_version: str | None = None,
        dataset_hash: str | None = None,
        **params: Any,
    ) -> StatisticalProvenance:
        """Build a provenance envelope for a statistical result."""
        return StatisticalProvenance(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            dataset_hash=dataset_hash,
            computation_method=method,
            method_version=ALGORITHM_VERSION,
            parameters=dict(sorted(params.items())),
        )

    def analyze_correlation(
        self,
        series_a: list[float],
        series_b: list[float],
        series_a_name: str = "",
        series_b_name: str = "",
        method: str = "pearson",
        timestamps: list[str] | None = None,
        evidence_refs: list[str] | None = None,
    ) -> CorrelationResult:
        """
        Compute correlation between two series.

        Args:
            series_a: Values for series A
            series_b: Values for series B
            series_a_name: Name/ID for series A
            series_b_name: Name/ID for series B
            method: "pearson" or "spearman"
            timestamps: Optional timestamp strings
            evidence_refs: Optional evidence references

        Returns:
            CorrelationResult
        """
        n = len(series_a)
        if timestamps is None:
            timestamps = [str(i) for i in range(n)]
        if evidence_refs is None:
            evidence_refs = []

        if method == "spearman":
            correlation = spearman_correlation(series_a, series_b)
        else:
            correlation = pearson_correlation(series_a, series_b)

        if correlation is None:
            correlation = 0.0

        rel_type, rel_strength = classify_relationship(correlation)
        p_value = approximate_p_value(correlation, n) if correlation is not None else None

        provenance = self._build_provenance(
            method=method,
            n=len(series_a),
        )

        return CorrelationResult(
            series_a=series_a_name,
            series_b=series_b_name,
            correlation=correlation,
            p_value=p_value,
            sample_size=n,
            method=method,
            relationship_type=rel_type,
            relationship_strength=rel_strength,
            observation_start=timestamps[0] if timestamps else "",
            observation_end=timestamps[-1] if timestamps else "",
            evidence_refs=evidence_refs,
            provenance=provenance,
        )

    def analyze_rolling_correlation(
        self,
        series_a: list[float],
        series_b: list[float],
        window_size: int,
        series_a_name: str = "",
        series_b_name: str = "",
        timestamps: list[str] | None = None,
        evidence_refs: list[str] | None = None,
    ) -> RollingCorrelationResult:
        """
        Compute rolling correlation between two series.

        Args:
            series_a: Values for series A
            series_b: Values for series B
            window_size: Rolling window size
            series_a_name: Name/ID for series A
            series_b_name: Name/ID for series B
            timestamps: Optional timestamp strings
            evidence_refs: Optional evidence references

        Returns:
            RollingCorrelationResult
        """
        if timestamps is None:
            timestamps = [str(i) for i in range(len(series_a))]
        if evidence_refs is None:
            evidence_refs = []

        correlations, corr_timestamps, stability = __import__(
            "macro_intelligence.relationships.correlation",
            fromlist=["compute_rolling_correlation"],
        ).compute_rolling_correlation(series_a, series_b, window_size)

        provenance = self._build_provenance(
            method="rolling_pearson",
            window_size=window_size,
        )

        return RollingCorrelationResult(
            series_a=series_a_name,
            series_b=series_b_name,
            window_size=window_size,
            correlations=correlations,
            timestamps=corr_timestamps,
            stability=stability,
            algorithm_version=ALGORITHM_VERSION,
            provenance=provenance,
        )

    def analyze_lag(
        self,
        series_a: list[float],
        series_b: list[float],
        series_a_name: str = "",
        series_b_name: str = "",
        max_lag: int = 10,
        evidence_refs: list[str] | None = None,
    ) -> LagRelationship:
        """
        Find optimal lag between two series.

        Args:
            series_a: Values for series A
            series_b: Values for series B
            series_a_name: Name/ID for series A
            series_b_name: Name/ID for series B
            max_lag: Maximum lag to test
            evidence_refs: Optional evidence references

        Returns:
            LagRelationship
        """
        if evidence_refs is None:
            evidence_refs = []

        result = find_optimal_lag(series_a, series_b, max_lag)

        provenance = self._build_provenance(
            method="lag_correlation",
            max_lag=max_lag,
        )

        return LagRelationship(
            series_a=series_a_name,
            series_b=series_b_name,
            optimal_lag=result.optimal_lag,
            lag_correlation=result.lag_correlation,
            lag_type=result.lag_type,
            confidence=result.confidence,
            evidence_refs=evidence_refs,
            provenance=provenance,
        )

    def analyze_regime_relationship(
        self,
        series_a: list[float],
        series_b: list[float],
        regime_labels: list[str],
        series_a_name: str = "",
        series_b_name: str = "",
        evidence_refs: list[str] | None = None,
    ) -> list[RegimeRelationship]:
        """
        Compute correlations conditioned on macro regimes.

        Args:
            series_a: Values for series A
            series_b: Values for series B
            regime_labels: Regime label for each time period
            series_a_name: Name/ID for series A
            series_b_name: Name/ID for series B
            evidence_refs: Optional evidence references

        Returns:
            List of RegimeRelationship
        """
        if evidence_refs is None:
            evidence_refs = []

        results = compute_all_regime_correlations(series_a, series_b, regime_labels)

        provenance = self._build_provenance(
            method="regime_conditional_correlation",
        )

        # Attach names
        return [
            RegimeRelationship(
                series_a=series_a_name,
                series_b=series_b_name,
                regime=rel.regime,
                correlation=rel.correlation,
                sample_size=rel.sample_size,
                confidence=rel.confidence,
                algorithm_version=rel.algorithm_version,
                provenance=provenance,
            )
            for rel in results
        ]

    def detect_breaks(
        self,
        series_a: list[float],
        series_b: list[float],
        series_a_name: str = "",
        series_b_name: str = "",
        break_threshold: float = 0.3,
        min_segment_size: int = 10,
        evidence_refs: list[str] | None = None,
    ) -> list[StructuralBreak]:
        """
        Detect structural breaks in the relationship.

        Args:
            series_a: Values for series A
            series_b: Values for series B
            series_a_name: Name/ID for series A
            series_b_name: Name/ID for series B
            break_threshold: Minimum correlation change to flag
            min_segment_size: Minimum observations per segment
            evidence_refs: Optional evidence references

        Returns:
            List of StructuralBreak
        """
        if evidence_refs is None:
            evidence_refs = []

        breaks = detect_structural_breaks(series_a, series_b, break_threshold, min_segment_size)

        provenance = self._build_provenance(
            method="structural_break_detection",
            break_threshold=break_threshold,
            min_segment_size=min_segment_size,
        )

        # Attach names
        return [
            StructuralBreak(
                series_a=series_a_name,
                series_b=series_b_name,
                break_point=b.break_point,
                break_type=b.break_type,
                correlation_before=b.correlation_before,
                correlation_after=b.correlation_after,
                confidence=b.confidence,
                algorithm_version=b.algorithm_version,
                provenance=provenance,
            )
            for b in breaks
        ]

    def full_analysis(
        self,
        series_a: list[float],
        series_b: list[float],
        series_a_name: str = "",
        series_b_name: str = "",
        regime_labels: list[str] | None = None,
        rolling_window: int | None = None,
        max_lag: int = 10,
        break_threshold: float = 0.3,
        evidence_refs: list[str] | None = None,
    ) -> RelationshipResult:
        """
        Complete relationship analysis combining all methods.

        Args:
            series_a: Values for series A
            series_b: Values for series B
            series_a_name: Name/ID for series A
            series_b_name: Name/ID for series B
            regime_labels: Optional regime labels for each period
            rolling_window: Optional rolling window size
            max_lag: Maximum lag to test
            break_threshold: Minimum correlation change for break detection
            evidence_refs: Optional evidence references

        Returns:
            RelationshipResult with all analysis
        """
        if evidence_refs is None:
            evidence_refs = []

        # Overall correlation
        overall = self.analyze_correlation(
            series_a,
            series_b,
            series_a_name,
            series_b_name,
            evidence_refs=evidence_refs,
        )

        # Rolling correlation
        rolling = None
        if rolling_window is not None and rolling_window >= 2:
            rolling = self.analyze_rolling_correlation(
                series_a,
                series_b,
                rolling_window,
                series_a_name,
                series_b_name,
                evidence_refs=evidence_refs,
            )

        # Lag analysis
        lag = None
        if len(series_a) >= 4:
            lag = self.analyze_lag(
                series_a,
                series_b,
                series_a_name,
                series_b_name,
                max_lag=max_lag,
                evidence_refs=evidence_refs,
            )

        # Regime-conditional correlations
        regime_rels = []
        if regime_labels is not None:
            regime_rels = self.analyze_regime_relationship(
                series_a,
                series_b,
                regime_labels,
                series_a_name,
                series_b_name,
                evidence_refs=evidence_refs,
            )

        # Structural breaks
        breaks = []
        if len(series_a) >= break_threshold * 20:
            breaks = self.detect_breaks(
                series_a,
                series_b,
                series_a_name,
                series_b_name,
                break_threshold=break_threshold,
                evidence_refs=evidence_refs,
            )

        provenance = self._build_provenance(
            method="full_relationship_analysis",
            rolling_window=rolling_window,
            max_lag=max_lag,
            break_threshold=break_threshold,
        )

        return RelationshipResult(
            series_a=series_a_name,
            series_b=series_b_name,
            overall_correlation=overall,
            rolling_correlation=rolling,
            lag_relationship=lag,
            regime_relationships=regime_rels,
            structural_breaks=breaks,
            evidence_refs=evidence_refs,
            provenance=provenance,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return engine metadata."""
        return {
            "version": self._version,
        }
