from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(".").resolve()
GOLD_CSV = PROJECT_ROOT / "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
DXY_CSV = PROJECT_ROOT / "dxy_real_2021_2025.csv"
VIX_CSV = PROJECT_ROOT / "vix_real_2021_2025.csv"
US10Y_CSV = PROJECT_ROOT / "us10y_real_2021_2025.csv"

gold = pd.read_csv(GOLD_CSV)
date_col = [c for c in gold.columns if c.lower() in ("date", "time", "datetime")][0]
close_col = [c for c in gold.columns if c.lower() == "close"][0]
gold[date_col] = pd.to_datetime(gold[date_col])
gold = gold[[date_col, close_col]].rename(columns={date_col: "date", close_col: "close"})
gold = gold.sort_values("date").reset_index(drop=True)
print(f'Gold: {len(gold)} rows, {gold["date"].min()} -> {gold["date"].max()}')

dxy = pd.read_csv(DXY_CSV, skiprows=2)
dxy.columns = ["date", "close", "high", "low", "open", "volume"]
dxy["date"] = pd.to_datetime(dxy["date"])
dxy["dxy_close"] = pd.to_numeric(dxy["close"], errors="coerce")
dxy = dxy[["date", "dxy_close"]].sort_values("date").reset_index(drop=True)
print(f'DXY: {len(dxy)} rows, {dxy["date"].min()} -> {dxy["date"].max()}')

vix = pd.read_csv(VIX_CSV, skiprows=2)
vix.columns = ["date", "close", "high", "low", "open", "volume"]
vix["date"] = pd.to_datetime(vix["date"])
vix["vix_close"] = pd.to_numeric(vix["close"], errors="coerce")
vix = vix[["date", "vix_close"]].sort_values("date").reset_index(drop=True)
print(f'VIX: {len(vix)} rows, {vix["date"].min()} -> {vix["date"].max()}')

us10y = pd.read_csv(US10Y_CSV, header=None, skiprows=2)
us10y.columns = ["date", "us10y_close"]
us10y["date"] = pd.to_datetime(us10y["date"])
us10y["us10y_close"] = pd.to_numeric(us10y["us10y_close"], errors="coerce")
us10y = us10y[["date", "us10y_close"]].sort_values("date").reset_index(drop=True)
print(f'US10Y: {len(us10y)} rows, {us10y["date"].min()} -> {us10y["date"].max()}')

merged = gold.merge(dxy, on="date", how="inner").merge(vix, on="date", how="inner").merge(us10y, on="date", how="inner")
print(f"Merged: {len(merged)} rows")
