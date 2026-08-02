"""
Historical Analytics Engine — deterministic historical research analytics.

Research-only. No online data, no trading logic.
"""

from researchos.quant_engine.historical.contracts import (
    DrawdownStatistics,
    FeatureExtraction,
    MarketState,
    RegimeStatistics,
    ReturnSeries,
    SeasonalityProfile,
    StateTransitionTable,
)
from researchos.quant_engine.historical.analytics import (
    pattern_frequencies,
    consecutive_streaks,
    detect_market_regimes,
    monthly_seasonality,
    weekly_seasonality,
    session_statistics,
    volatility_clustering,
    trend_persistence,
    breakout_frequency,
    mean_reversion_frequency,
    drawdown_statistics,
    recovery_statistics,
    state_transition_table,
    extract_features,
)

__all__ = [
    "DrawdownStatistics",
    "FeatureExtraction",
    "MarketState",
    "RegimeStatistics",
    "ReturnSeries",
    "SeasonalityProfile",
    "StateTransitionTable",
    "pattern_frequencies",
    "consecutive_streaks",
    "detect_market_regimes",
    "monthly_seasonality",
    "weekly_seasonality",
    "session_statistics",
    "volatility_clustering",
    "trend_persistence",
    "breakout_frequency",
    "mean_reversion_frequency",
    "drawdown_statistics",
    "recovery_statistics",
    "state_transition_table",
    "extract_features",
]

