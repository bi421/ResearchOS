"""
Phase 5.1 — empirical conditional-frequency probability estimator.

A simple, deterministic, lookahead-safe estimator.  For each feature axis it
bins the training feature values and records the empirical conditional class
frequency within each bin.  At prediction time it forecasts the class with the
highest empirical conditional frequency for the feature's bin.

This is intentionally the *simplest* scientifically-decent probability model:
    * Pure Python, no ML libraries, no randomness.
    * Trained ONLY on the training window (no lookahead).
    * Used out-of-sample on the validation window.
    * Self-contained; composes existing ``researchos`` infrastructure only for
      its contracts.

Guarantees:
    * Deterministic: same train/validation splits -> same predictions.
    * Lookahead-safe: each feature's fit is derived only from the training slice.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

FEATURE_NAMES: Tuple[str, ...] = (
    "returns",
    "log_returns",
    "rolling_mean_20",
    "rolling_std_20",
    "momentum_14",
    "rate_of_change_14",
    "rsi_14",
    "macd_hist",
    "atr_14",
    "bb_pct_b",
    "stoch_k",
    "cci_20",
    "mfi_14",
    "vwap",
    "hist_vol_20",
    "vol_ratio",
    "trend_state",
    "vol_regime",
    "momentum_regime",
)

# A feature may safely be selected for the estimator.  We permit all available
# features; the experiment may restrict to a fixed topographic subset by
# passing ``feature_indices``.
DEFAULT_FEATURE_INDICES: Tuple[int, ...] = tuple(range(len(FEATURE_NAMES)))


def _bins_for_feature(
    values: Sequence[Optional[float]],
    n_bins: int,
    floor: Optional[float] = None,
    cap: Optional[float] = None,
) -> Tuple[float, float, float]:
    """Return (floor, width, cap) covering the observed non-None values.

    If ``floor``/``cap`` are given they clamp the range.  The width is the
    range / ``n_bins``.  Degenerate ranges (zero width) are forced to width 1e-9.
    """
    valid = [v for v in values if v is not None and v == v]  # drop NaN
    if not valid:
        return 0.0, 1e-9, 0.0
    lo = min(valid)
    hi = max(valid)
    if floor is not None:
        lo = min(lo, floor)
    if cap is not None:
        hi = max(hi, cap)
    width = (hi - lo) / n_bins
    if width <= 0:
        width = 1e-9
    return lo, width, hi


def _bin_index(value: Optional[float], lo: float, width: float, n_bins: int) -> int:
    """Return the bin index for a value, clamping to [0, n_bins-1]."""
    if value is None or value != value:  # NaN
        return 0
    idx = int((value - lo) / width)
    if idx < 0:
        idx = 0
    if idx >= n_bins:
        idx = n_bins - 1
    return idx


class EmpiricalProbabilityEstimator:
    """Deterministic conditional-frequency probability estimator.

    For each selected feature, it builds a bin boundary table and a
    conditional class-frequency table from the training window.  At predict
    time the chosen feature's bin yields the per-class histogram.
    """

    def __init__(
        self,
        n_bins: int = 10,
        feature_indices: Optional[Sequence[int]] = None,
    ) -> None:
        self.n_bins = int(n_bins)
        self.feature_indices: Tuple[int, ...] = tuple(
            feature_indices if feature_indices is not None else DEFAULT_FEATURE_INDICES
        )
        if not self.feature_indices:
            raise ValueError("At least one feature must be selected")
        self._boundaries: Dict[int, Tuple[float, float, float]] = {}
        self._histograms: Dict[int, Dict[int, List[int]]] = {}
        self._trained = False

    def fit(
        self,
        features: Sequence[Sequence[Optional[float]]],
        labels: Sequence[float],
    ) -> "EmpiricalProbabilityEstimator":
        """Fit bin boundaries + conditional histograms from the training window.

        Args:
            features: Aligned feature rows (same length as ``labels``).
            labels: Training labels (1 / 0 / −1).
        """
        self._boundaries = {}
        self._histograms = {}

        for idx in self.feature_indices:
            col = [row[idx] if idx < len(row) else None for row in features]
            lo, width, hi = _bins_for_feature(col, self.n_bins)
            self._boundaries[idx] = (lo, width, hi)
            # hist[cls] is a list over bins of counts
            table: Dict[int, List[int]] = {
                1: [0] * self.n_bins,
                0: [0] * self.n_bins,
                -1: [0] * self.n_bins,
            }
            for row, label in zip(features, labels):
                value = row[idx] if idx < len(row) else None
                b = _bin_index(value, lo, width, self.n_bins)
                cls = int(label)
                if cls in table:
                    table[cls][b] += 1
            self._histograms[idx] = table

        self._trained = True
        return self

    def predict_class(self, feature_row: Sequence[Optional[float]]) -> int:
        """Predict the class (1 / 0 / −1) for a single feature row.

        Uses the *first* selected feature's conditional frequency.  To keep the
        experiment smallest and most defensible, the estimator predicts from a
        single feature axis chosen during construction, which avoids
        arbitrary feature-combination complexity.  The experiment ties this to
        a topographic feature (e.g. ``trend_state``) via ``feature_indices``.
        """
        if not self._trained:
            raise ValueError("Estimator not fitted")
        idx = self.feature_indices[0]
        value = feature_row[idx] if idx < len(feature_row) else None
        lo, width, _ = self._boundaries[idx]
        b = _bin_index(value, lo, width, self.n_bins)
        table = self._histograms[idx]
        # Deterministic: sum of counts per class, highest wins; tie prefers 1 > 0 > -1.
        counts = {cls: table[cls][b] for cls in (1, 0, -1)}
        best_cls = 1
        best_count = -1
        for cls in (1, 0, -1):
            if counts[cls] > best_count:
                best_count = counts[cls]
                best_cls = cls
        return best_cls

    def predict_proba(self, feature_row: Sequence[Optional[float]]) -> Dict[int, float]:
        """Return empirical per-class probabilities for a feature row."""
        if not self._trained:
            raise ValueError("Estimator not fitted")
        idx = self.feature_indices[0]
        value = feature_row[idx] if idx < len(feature_row) else None
        lo, width, _ = self._boundaries[idx]
        b = _bin_index(value, lo, width, self.n_bins)
        table = self._histograms[idx]
        total = sum(table[cls][b] for cls in (1, 0, -1))
        if total == 0:
            return {1: 1 / 3, 0: 1 / 3, -1: 1 / 3}
        return {cls: table[cls][b] / total for cls in (1, 0, -1)}


__all__ = [
    "FEATURE_NAMES",
    "DEFAULT_FEATURE_INDICES",
    "EmpiricalProbabilityEstimator",
    "_bins_for_feature",
    "_bin_index",
]
