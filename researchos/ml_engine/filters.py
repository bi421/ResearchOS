"""
Market noise filters for signal extraction and regime detection.
"""
import numpy as np
import pandas as pd
from scipy import signal


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average Directional Index (ADX) – Trend strength indicator.
    ADX > 25 indicates strong trend (low noise), ADX < 20 indicates ranging market (high noise).
    """
    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)
    
    # True Range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # +DM and -DM
    up_move = high - high.shift()
    down_move = low.shift() - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smooth DMs
    plus_dm_smooth = pd.Series(plus_dm).rolling(window=period).mean()
    minus_dm_smooth = pd.Series(minus_dm).rolling(window=period).mean()
    
    # DI+
    di_plus = 100 * (plus_dm_smooth / atr)
    di_minus = 100 * (minus_dm_smooth / atr)
    
    # DX and ADX
    dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus)
    adx = dx.rolling(window=period).mean()
    return adx


def kalman_filter_1d(price: pd.Series, q: float = 1e-5, r: float = 0.01) -> pd.Series:
    """
    1D Kalman Filter for smoothing noisy price series.
    Extracts the underlying trend (signal) from the noise.
    """
    n = len(price)
    estimated = np.zeros(n)
    error_cov = np.zeros(n)
    
    estimated[0] = price.iloc[0]
    error_cov[0] = 1.0
    
    for i in range(1, n):
        # Prediction
        predicted = estimated[i-1]
        pred_error_cov = error_cov[i-1] + q
        
        # Update (Kalman Gain)
        kg = pred_error_cov / (pred_error_cov + r)
        estimated[i] = predicted + kg * (price.iloc[i] - predicted)
        error_cov[i] = (1 - kg) * pred_error_cov
    
    return pd.Series(estimated, index=price.index)


def calculate_volatility_regime(close: pd.Series, lookback: int = 50) -> pd.Series:
    """
    Returns a boolean mask where volatility is in the 'normal' range.
    Filters out periods of extreme volatility (where noise dominates).
    """
    returns = close.pct_change()
    rolling_std = returns.rolling(window=lookback).std()
    # Z-score of volatility
    vol_zscore = (rolling_std - rolling_std.mean()) / rolling_std.std()
    # Exclude periods where volatility is > 1.5 standard deviations above mean (extreme noise)
    return vol_zscore < 1.5


def is_trending_regime(adx: pd.Series, threshold: float = 25.0) -> pd.Series:
    """
    Returns True for periods where ADX > threshold (strong trend, low noise).
    """
    return adx > threshold


def apply_noise_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds noise filter indicators to the DataFrame.
    Also adds a boolean column 'valid_trade' which is True when:
    1. ADX > 25 (trending)
    2. Volatility is NOT extreme (normal regime)
    """
    df = df.copy()
    df['adx'] = calculate_adx(df['high'], df['low'], df['close'])
    df['kalman_trend'] = kalman_filter_1d(df['close'])
    df['price_vs_trend'] = df['close'] / df['kalman_trend'] - 1  # deviation from trend
    
    df['volatility_filter'] = calculate_volatility_regime(df['close'])
    df['trend_filter'] = is_trending_regime(df['adx'])
    
    # Combine filters: Must be trending AND low volatility to trade.
    df['valid_trade'] = df['volatility_filter'] & df['trend_filter']
    
    return df
