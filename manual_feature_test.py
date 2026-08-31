import numpy as np
import pandas as pd
from scipy import stats

print("=" * 70)
print("STAGE 0: Loading real data files")
print("=" * 70)

gold = pd.read_csv("data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv")
date_col = [c for c in gold.columns if c.lower() in ("date", "time", "datetime")][0]
close_col = [c for c in gold.columns if c.lower() == "close"][0]
gold[date_col] = pd.to_datetime(gold[date_col])
gold = gold[[date_col, close_col]].rename(columns={date_col: "date", close_col: "gold_close"})
gold = gold.sort_values("date").reset_index(drop=True)
print("Gold rows:", len(gold))

dxy = pd.read_csv("dxy_real_2021_2025.csv", skiprows=2)
dxy.columns = ["date", "close", "high", "low", "open", "volume"]
dxy["date"] = pd.to_datetime(dxy["date"])
dxy["dxy_return"] = pd.to_numeric(dxy["close"], errors="coerce").pct_change()
dxy = dxy[["date", "dxy_return"]]
print("DXY rows:", len(dxy))

vix = pd.read_csv("vix_real_2021_2025.csv", skiprows=2)
vix.columns = ["date", "close", "high", "low", "open", "volume"]
vix["date"] = pd.to_datetime(vix["date"])
vix["vix_level"] = pd.to_numeric(vix["close"], errors="coerce")
vix = vix[["date", "vix_level"]]
print("VIX rows:", len(vix))

us10y = pd.read_csv("us10y_real_2021_2025.csv")
us10y["date"] = pd.to_datetime(us10y["date"])
print("US10Y rows:", len(us10y))

print("")
print("=" * 70)
print("STAGE 1: Merging and building features")
print("=" * 70)

df = gold.merge(dxy, on="date", how="inner").merge(vix, on="date", how="inner")
df = df.merge(us10y, on="date", how="left").sort_values("date").reset_index(drop=True)
df["real_yield_10y"] = df["real_yield_10y"].ffill()
df["gold_return"] = df["gold_close"].pct_change()

df["dxy_return_lag1"] = df["dxy_return"].shift(1)
df["dxy_return_lag3"] = df["dxy_return"].shift(3)
df["vix_level_lag1"] = df["vix_level"].shift(1)
df["dxy_vix_interaction"] = df["dxy_return"] * df["vix_level"]
df["high_vol_regime"] = (df["vix_level"] > df["vix_level"].quantile(0.7)).astype(int)
df["rolling_corr_gold_dxy"] = df["gold_return"].rolling(60).corr(df["dxy_return"])

df = df.dropna().reset_index(drop=True)

print("Final merged+featured rows:", len(df))
print("Columns:", list(df.columns))

factor_cols = ["dxy_return", "vix_level", "real_yield_10y", "dxy_return_lag1", "dxy_return_lag3", "vix_level_lag1", "dxy_vix_interaction", "high_vol_regime", "rolling_corr_gold_dxy"]
print("")
print("Factors used:", len(factor_cols), factor_cols)

print("")
print("=" * 70)
print("STAGE 2: Non-overlapping walk-forward")
print("=" * 70)

horizons = [1, 5, 10, 20]
lookback = 252


def run_horizon_test(data, factor_cols, horizon, lookback):
    d = data.copy()
    d["fwd_return"] = d["gold_close"].shift(-horizon) / d["gold_close"] - 1
    d["target"] = (d["fwd_return"] > 0).astype(int)
    d = d.iloc[:-horizon]
    X_all = d[factor_cols].values
    y_all = d["target"].values
    preds, actuals = [], []
    i = lookback
    while i < len(d):
        X_train = X_all[:i]
        y_train = y_all[:i]
        X_test = X_all[i : i + 1]
        X_train_design = np.column_stack([np.ones(len(X_train)), X_train])
        try:
            coef, res, rank, sv = np.linalg.lstsq(X_train_design, y_train, rcond=None)
            X_test_design = np.column_stack([np.ones(1), X_test])
            pred_prob = (X_test_design @ coef)[0]
            pred = 1 if pred_prob > 0.5 else 0
            preds.append(pred)
            actuals.append(y_all[i])
        except Exception:
            pass
        i += horizon
    preds = np.array(preds)
    actuals = np.array(actuals)
    n = len(actuals)
    if n < 10:
        return None
    model_acc = (preds == actuals).mean()
    baseline_acc = max(actuals.mean(), 1 - actuals.mean())
    correct = (preds == actuals).sum()
    p_value = stats.binomtest(correct, n, baseline_acc, alternative="greater").pvalue
    return {"n": n, "model_acc": model_acc, "baseline_acc": baseline_acc, "p_value": p_value}


stage2_results = {}
print("Horizon   N   ModelAcc   Baseline   P-value")
for horizon in horizons:
    r = run_horizon_test(df, factor_cols, horizon, lookback)
    if r is None:
        print(horizon, "d -- not enough samples --")
        continue
    stage2_results[horizon] = r
    print(horizon, "d", r["n"], round(r["model_acc"], 4), round(r["baseline_acc"], 4), round(r["p_value"], 4))

print("")
print("=" * 70)
print("STAGE 3: Bonferroni correction")
print("=" * 70)

n_tests = len(stage2_results)
alpha = 0.05
bonferroni_threshold = alpha / n_tests if n_tests > 0 else alpha
print("Number of tests:", n_tests)
print("Bonferroni threshold:", alpha, "/", n_tests, "=", round(bonferroni_threshold, 4))
print("")

passed = []
for horizon, r in stage2_results.items():
    sig = r["p_value"] < bonferroni_threshold
    print("Horizon", horizon, "d: p=", round(r["p_value"], 4), "threshold=", round(bonferroni_threshold, 4), "PASSES" if sig else "fails")
    if sig:
        passed.append(horizon)

print("")
print("=" * 70)
print("STAGE 4: Holdout check")
print("=" * 70)

if not passed:
    print("No horizon passed Bonferroni correction in Stage 3.")
    print("Nothing to holdout-test. Stopping here.")
else:
    holdout_start_idx = int(len(df) * 0.8)
    print("Holdout starts at row", holdout_start_idx)
    for horizon in passed:
        d = df.copy()
        d["fwd_return"] = d["gold_close"].shift(-horizon) / d["gold_close"] - 1
        d["target"] = (d["fwd_return"] > 0).astype(int)
        d = d.iloc[:-horizon]
        X_all = d[factor_cols].values
        y_all = d["target"].values
        preds, actuals = [], []
        i = holdout_start_idx
        while i < len(d):
            X_train = X_all[:i]
            y_train = y_all[:i]
            X_test = X_all[i : i + 1]
            X_train_design = np.column_stack([np.ones(len(X_train)), X_train])
            try:
                coef, res, rank, sv = np.linalg.lstsq(X_train_design, y_train, rcond=None)
                X_test_design = np.column_stack([np.ones(1), X_test])
                pred_prob = (X_test_design @ coef)[0]
                pred = 1 if pred_prob > 0.5 else 0
                preds.append(pred)
                actuals.append(y_all[i])
            except Exception:
                pass
            i += horizon
        preds = np.array(preds)
        actuals = np.array(actuals)
        n = len(actuals)
        if n < 10:
            print("Horizon", horizon, "d: not enough holdout samples")
            continue
        model_acc = (preds == actuals).mean()
        baseline_acc = max(actuals.mean(), 1 - actuals.mean())
        correct = (preds == actuals).sum()
        p_value = stats.binomtest(correct, n, baseline_acc, alternative="greater").pvalue
        print("Horizon", horizon, "d HOLDOUT: n=", n, "acc=", round(model_acc, 4), "baseline=", round(baseline_acc, 4), "p=", round(p_value, 4), "sig=", p_value < 0.05)

print("")
print("=" * 70)
print("DONE. Every number above came from actually running this script.")
print("=" * 70)
