import numpy as np
import pandas as pd
from fredapi import Fred
from scipy import stats

FRED_API_KEY = "c23c25c4c1abb2777d1067591842c1c6"

print("Downloading US10Y real yield (DFII10) from FRED...")
fred = Fred(api_key=FRED_API_KEY)
us10y = fred.get_series("DFII10", observation_start="2021-01-01", observation_end="2025-12-31")
us10y = us10y.reset_index()
us10y.columns = ["date", "real_yield_10y"]
us10y["date"] = pd.to_datetime(us10y["date"])
us10y["real_yield_10y"] = pd.to_numeric(us10y["real_yield_10y"], errors="coerce")
us10y = us10y.dropna()
print("US10Y rows:", len(us10y))
us10y.to_csv("us10y_real_2021_2025.csv", index=False)

gold = pd.read_csv("data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv")
date_col = [c for c in gold.columns if c.lower() in ("date", "time", "datetime")][0]
close_col = [c for c in gold.columns if c.lower() == "close"][0]
gold[date_col] = pd.to_datetime(gold[date_col])
gold = gold[[date_col, close_col]].rename(columns={date_col: "date", close_col: "gold_close"})
gold = gold.sort_values("date").reset_index(drop=True)

dxy = pd.read_csv("dxy_real_2021_2025.csv", skiprows=2)
dxy.columns = ["date", "close", "high", "low", "open", "volume"]
dxy["date"] = pd.to_datetime(dxy["date"])
dxy["dxy_return"] = pd.to_numeric(dxy["close"], errors="coerce").pct_change()
dxy = dxy[["date", "dxy_return"]]

vix = pd.read_csv("vix_real_2021_2025.csv", skiprows=2)
vix.columns = ["date", "close", "high", "low", "open", "volume"]
vix["date"] = pd.to_datetime(vix["date"])
vix["vix_level"] = pd.to_numeric(vix["close"], errors="coerce")
vix["vix_change"] = vix["vix_level"].pct_change()
vix = vix[["date", "vix_level", "vix_change"]]

df = gold.merge(dxy, on="date", how="inner").merge(vix, on="date", how="inner")
df = df.merge(us10y, on="date", how="left").sort_values("date")
df["real_yield_10y"] = df["real_yield_10y"].ffill()
df = df.dropna().reset_index(drop=True)
print("Final merged rows:", len(df))

factor_cols = ["dxy_return", "vix_level", "vix_change", "real_yield_10y"]
horizons = [1, 5, 10, 20]
lookback = 252
results = []

for horizon in horizons:
    d = df.copy()
    d["fwd_return"] = d["gold_close"].shift(-horizon) / d["gold_close"] - 1
    d["target"] = (d["fwd_return"] > 0).astype(int)
    d = d.iloc[:-horizon]
    X_all = d[factor_cols].values
    y_all = d["target"].values
    preds, actuals = [], []
    for i in range(lookback, len(d)):
        X_train = X_all[:i]
        y_train = y_all[:i]
        X_test = X_all[i : i + 1]
        X_train_design = np.column_stack([np.ones(len(X_train)), X_train])
        try:
            coef, res, rank, sv = np.linalg.lstsq(X_train_design, y_train, rcond=None)
        except Exception:
            continue
        X_test_design = np.column_stack([np.ones(1), X_test])
        pred_prob = (X_test_design @ coef)[0]
        pred = 1 if pred_prob > 0.5 else 0
        preds.append(pred)
        actuals.append(y_all[i])
    preds = np.array(preds)
    actuals = np.array(actuals)
    n = len(actuals)
    model_acc = (preds == actuals).mean()
    baseline_acc = max(actuals.mean(), 1 - actuals.mean())
    correct = (preds == actuals).sum()
    binom_result = stats.binomtest(correct, n, baseline_acc, alternative="greater")
    results.append((horizon, n, model_acc, baseline_acc, binom_result.pvalue, binom_result.pvalue < 0.05))

print("")
print("FACTORS: DXY return, VIX level, VIX change, US10Y real yield")
print("Horizon  N      ModelAcc   Baseline   Pvalue     Sig")
for r in results:
    print(r[0], "d", r[1], round(r[2], 4), round(r[3], 4), round(r[4], 4), r[5])
