"""Vectorized SMA, RSI, and ATR multi-feature strategy signals."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_multi_feature_signals(df: pd.DataFrame) -> pd.Series:
    """Generate vectorized multi-feature signals.

    Returns a Series aligned with ``df.index`` containing ``1`` for Long,
    ``-1`` for Short, and ``0`` for Flat or unavailable indicator values.
    RSI uses Wilder smoothing and ATR uses a 14-period rolling mean.
    """
    required_columns = {"close", "high", "low"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    close = df["close"]
    high = df["high"]
    low = df["low"]

    sma_20 = close.rolling(window=20, min_periods=20).mean()
    sma_50 = close.rolling(window=50, min_periods=50).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    previous_close = close.shift()
    true_range = np.maximum(
        high - low,
        np.maximum((high - previous_close).abs(), (low - previous_close).abs()),
    )
    atr = true_range.rolling(window=14, min_periods=14).mean()
    atr_sma_20 = atr.rolling(window=20, min_periods=20).mean()

    volatile = atr > atr_sma_20
    long_condition = (sma_20 > sma_50) & (rsi > 50) & volatile
    short_condition = (sma_20 < sma_50) & (rsi < 50) & volatile

    signals = pd.Series(0, index=df.index, dtype=np.int8)
    signals.loc[long_condition] = 1
    signals.loc[short_condition] = -1
    return signals


generate_vectorized_multi_signals = generate_multi_feature_signals
