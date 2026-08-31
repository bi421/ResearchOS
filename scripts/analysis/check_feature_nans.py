from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(".").resolve()
GOLD_CSV = PROJECT_ROOT / "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
DXY_CSV = PROJECT_ROOT / "dxy_real_2021_2025.csv"
VIX_CSV = PROJECT_ROOT / "vix_real_2021_2025.csv"
US10Y_CSV = PROJECT_ROOT / "us10y_real_2021_2025.csv"

# Load and merge
gold = pd.read_csv(GOLD_CSV)
date_col = [c for c in gold.columns if c.lower() in ("date", "time", "datetime")][0]
close_col = [c for c in gold.columns if c.lower() == "close"][0]
high_col = [c for c in gold.columns if c.lower() == "high"][0]
low_col = [c for c in gold.columns if c.lower() == "low"][0]
open_col = [c for c in gold.columns if c.lower() == "open"][0]
volume_col = [c for c in gold.columns if c.lower() in ("volume", "tick_volume")][0]
gold[date_col] = pd.to_datetime(gold[date_col])
gold = gold.rename(columns={date_col: "date", close_col: "close", high_col: "high", low_col: "low", open_col: "open", volume_col: "volume"})
gold = gold[["date", "open", "high", "low", "close", "volume"]].sort_values("date").reset_index(drop=True)

dxy = pd.read_csv(DXY_CSV, skiprows=2)
dxy.columns = ["date", "close", "high", "low", "open", "volume"]
dxy["date"] = pd.to_datetime(dxy["date"])
dxy["dxy_close"] = pd.to_numeric(dxy["close"], errors="coerce")
dxy = dxy[["date", "dxy_close"]].sort_values("date").reset_index(drop=True)

vix = pd.read_csv(VIX_CSV, skiprows=2)
vix.columns = ["date", "close", "high", "low", "open", "volume"]
vix["date"] = pd.to_datetime(vix["date"])
vix["vix_close"] = pd.to_numeric(vix["close"], errors="coerce")
vix = vix[["date", "vix_close"]].sort_values("date").reset_index(drop=True)

us10y = pd.read_csv(US10Y_CSV, header=None, skiprows=2)
us10y.columns = ["date", "us10y_close"]
us10y["date"] = pd.to_datetime(us10y["date"])
us10y["us10y_close"] = pd.to_numeric(us10y["us10y_close"], errors="coerce")
us10y = us10y[["date", "us10y_close"]].sort_values("date").reset_index(drop=True)

df = gold.merge(dxy, on="date", how="inner").merge(vix, on="date", how="inner").merge(us10y, on="date", how="inner")
print(f"After merge: {len(df)} rows")

# Add features one by one
df["rolling_5d_return"] = df["close"].pct_change(5)
df["rolling_20d_return"] = df["close"].pct_change(20)
df["rolling_20d_volatility"] = df["close"].pct_change().rolling(20).std()
df["rolling_z_score_price"] = (df["close"] - df["close"].rolling(60).mean()) / df["close"].rolling(60).std()
df["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
df["high_low_range"] = (df["high"] - df["low"]) / df["close"]
df["close_open_ratio"] = df["close"] / df["open"]

df["dxy_return"] = df["dxy_close"].pct_change()
for lag in [1, 3, 5, 10]:
    df[f"dxy_lag_{lag}d"] = df["dxy_return"].shift(lag)

df["vix_change"] = df["vix_close"].diff()
for lag in [1, 3, 5, 10]:
    df[f"vix_lag_{lag}d"] = df["vix_close"].shift(lag)

df["us10y_change"] = df["us10y_close"].diff()
for lag in [1, 3, 5, 10]:
    df[f"us10y_lag_{lag}d"] = df["us10y_close"].shift(lag)

df["dxy_return_x_vix_level"] = df["dxy_return"] * df["vix_close"]
df["vix_change_x_us10y_change"] = df["vix_change"] * df["us10y_change"]

vix_quantile_75 = df["vix_close"].rolling(60).quantile(0.75)
df["vix_regime_high"] = (df["vix_close"] > vix_quantile_75).astype(int)

dxy_sma20 = df["dxy_close"].rolling(20).mean()
df["dxy_trend_up"] = (df["dxy_close"] > dxy_sma20).astype(int)

df["gold_dxy_corr_60d"] = df["close"].pct_change().rolling(60).corr(df["dxy_close"].pct_change())
df["gold_vix_corr_60d"] = df["close"].pct_change().rolling(60).corr(df["vix_close"].pct_change())

# Check NaN counts per feature
feature_cols = [
    "rolling_5d_return",
    "rolling_20d_return",
    "rolling_20d_volatility",
    "rolling_z_score_price",
    "volume_ratio",
    "high_low_range",
    "close_open_ratio",
    "dxy_return",
    "dxy_lag_1d",
    "dxy_lag_3d",
    "dxy_lag_5d",
    "dxy_lag_10d",
    "vix_close",
    "vix_change",
    "vix_lag_1d",
    "vix_lag_3d",
    "vix_lag_5d",
    "vix_lag_10d",
    "us10y_close",
    "us10y_change",
    "us10y_lag_1d",
    "us10y_lag_3d",
    "us10y_lag_5d",
    "us10y_lag_10d",
    "dxy_return_x_vix_level",
    "vix_change_x_us10y_change",
    "vix_regime_high",
    "dxy_trend_up",
    "gold_dxy_corr_60d",
    "gold_vix_corr_60d",
]

print("\nNaN counts per feature:")
for col in feature_cols:
    nan_count = df[col].isna().sum()
    valid_count = len(df) - nan_count
    print(f"  {col}: {nan_count} NaN, {valid_count} valid")

print(f"\nRows with all features valid: {df[feature_cols].dropna().shape[0]}")

# Check first/last valid dates
valid_df = df.dropna(subset=feature_cols)
if len(valid_df) > 0:
    print(f'First valid date: {valid_df["date"].iloc[0]}')
    print(f'Last valid date: {valid_df["date"].iloc[-1]}')
