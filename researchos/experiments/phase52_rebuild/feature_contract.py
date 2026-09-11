"""Phase 5.2 rebuild feature, timing, and label contract.

The contract makes the prediction-time semantics explicit before model
execution.  A row for calendar day ``t`` is considered observable only after
that UTC day has completed; the prediction timestamp is therefore
``t+1 00:00:00Z``.  Same-day DXY/US10Y/VIX observations are consequently
allowed as features because they are treated as end-of-day observations and
are consumed only after the day closes.

The supervised target remains the existing ResearchOS forward-return
semantics: ``close[t+h] / close[t] - 1``.  It uses future observations only as
a label and is never included in the feature matrix.
"""
from __future__ import annotations

from dataclasses import dataclass

PRICE_FEATURE_NAMES: tuple[str, ...] = (
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

MACRO_FEATURES_PER_SYMBOL: tuple[str, ...] = (
    "return_1",
    "roll_mean_return_5",
    "roll_zscore_20",
)

MACRO_SYMBOLS: tuple[str, ...] = ("DXY", "US10Y", "VIX")
FEATURE_SET_NAMES: tuple[str, ...] = (
    "PRICE_ONLY",
    "PRICE_DXY",
    "PRICE_US10Y",
    "PRICE_VIX",
    "PRICE_ALL",
)

DEFAULT_HORIZON = 5
DEFAULT_THRESHOLD = 0.0
DEFAULT_WARMUP = 60
DEFAULT_MIN_SAMPLES = 1200
DEFAULT_TRAIN_SIZE = 1000
DEFAULT_VALIDATION_SIZE = 200


@dataclass(frozen=True)
class Phase52FeatureContract:
    """Immutable scientific contract for the Phase 5.2 rebuild dataset."""

    horizon: int = DEFAULT_HORIZON
    threshold: float = DEFAULT_THRESHOLD
    warmup: int = DEFAULT_WARMUP
    train_size: int = DEFAULT_TRAIN_SIZE
    validation_size: int = DEFAULT_VALIDATION_SIZE

    @property
    def minimum_samples(self) -> int:
        return self.train_size + self.validation_size

    @property
    def prediction_timing(self) -> str:
        return "after_utc_day_close"

    @property
    def label_definition(self) -> str:
        return f"close[t+{self.horizon}] / close[t] - 1"

    @property
    def final_sample_rule(self) -> str:
        return f"common_days - {self.warmup} feature warmup - {self.horizon} label horizon"


__all__ = [
    "PRICE_FEATURE_NAMES",
    "MACRO_FEATURES_PER_SYMBOL",
    "MACRO_SYMBOLS",
    "FEATURE_SET_NAMES",
    "DEFAULT_HORIZON",
    "DEFAULT_THRESHOLD",
    "DEFAULT_WARMUP",
    "DEFAULT_MIN_SAMPLES",
    "DEFAULT_TRAIN_SIZE",
    "DEFAULT_VALIDATION_SIZE",
    "Phase52FeatureContract",
]
