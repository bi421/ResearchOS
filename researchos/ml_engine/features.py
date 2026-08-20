# -*- coding: utf-8 -*-
"""
Technical features for ML models.
Optimized for XAUUSD quantitative analysis.
"""

import pandas as pd
import numpy as np


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]

    # 1. Returns and lags
    df["returns"] = close.pct_change()
    for lag in [1, 2, 3, 5, 10, 20]:
        df[f"return_lag_{lag}"] = df["returns"].shift(lag)
        df[f"close_lag_{lag}"] = close.shift(lag)

    # 2. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # 3. MACD
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_diff"] = df["macd"] - df["macd_signal"]

    # 4. Bollinger Bands Position
    rolling_mean = close.rolling(window=20).mean()
    rolling_std = close.rolling(window=20).std()
    df["bb_high"] = rolling_mean + (rolling_std * 2)
    df["bb_low"] = rolling_mean - (rolling_std * 2)
    bb_width = df["bb_high"] - df["bb_low"]
    df["bb_position"] = np.where(bb_width != 0, (close - df["bb_low"]) / bb_width, 0.5)

    # 5. ATR and ATR Ratio
    if "high" in df.columns and "low" in df.columns:
        high, low = df["high"], df["low"]
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=14).mean()
    else:
        df["atr"] = df["returns"].rolling(14).std()

    df["atr_ratio"] = df["atr"] / close
    df["volatility"] = df["returns"].rolling(20).std()

    # 6. Target Definition
    df["target"] = (close.shift(-1) > close).astype(int)

    # 7. Drop original raw price columns
    df = df.drop(columns=["open", "high", "low"], errors="ignore")

    # 8. Clean up NaN values
    df = df.dropna()

    return df
