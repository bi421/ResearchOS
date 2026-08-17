"""
Historical Analytics Engine — deterministic historical research analytics.

Research-only. No online data, no trading logic.
"""

from researchos.quant_engine.historical.analytics import (
    breakout_frequency,
    consecutive_streaks,
    detect_market_regimes,
    drawdown_statistics,
    extract_features,
    mean_reversion_frequency,
    monthly_seasonality,
    pattern_frequencies,
    recovery_statistics,
    session_statistics,
    state_transition_table,
    trend_persistence,
    volatility_clustering,
    weekly_seasonality,
)
from researchos.quant_engine.historical.contracts import (
    DrawdownStatistics,
    FeatureExtraction,
    MarketState,
    RegimeStatistics,
    ReturnSeries,
    SeasonalityProfile,
    StateTransitionTable,
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
