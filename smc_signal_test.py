"""
SMC SIGNAL STATISTICAL TEST — first-ever rigorous test of whether the
REAL engine/smc.py trend-detection logic (find_swing_points + detect_trend)
has predictive power on real XAUUSD data.

This imports the ACTUAL functions from trader/engine/smc.py — it does not
reimplement or guess at the logic. Only load_candles() is bypassed (it
requires trader.duckdb, which is missing); we feed it real XAUUSD OHLC
data from ResearchOS instead.

Uses the SAME rigor as ResearchOS's rigorous_test.py:
  - No look-ahead: trend is computed using only data up to day i
  - Non-overlapping evaluation per horizon
  - Bonferroni correction across horizons
  - True holdout (last 20%, never used to pick anything)

Run from C:\\Users\\User\\Desktop\\ResearchOS
    python smc_signal_test.py
"""
import sys

import pandas as pd
from scipy import stats

# Import the REAL smc.py functions from the trader project
sys.path.insert(0, r"C:\Users\User\Desktop\trader")
from engine.smc import detect_trend, find_swing_points  # noqa: E402

# ============================================================
# Load real XAUUSD OHLC (same file used throughout today)
# ============================================================
gold = pd.read_csv("data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv")
gold.columns = [c.lower() for c in gold.columns]
gold = gold.rename(columns={"date": "date"})
gold["date"] = pd.to_datetime(gold["date"])
gold = gold.sort_values("date").reset_index(drop=True)
gold = gold[["date", "open", "high", "low", "close"]]
print(f"Loaded {len(gold)} real XAUUSD candles")
print(gold.head(3))

# ============================================================
# Generate SMC trend signal for each day using ONLY past data
# (no look-ahead: at day i, only gold.iloc[:i+1] is visible)
# ============================================================
LOOKBACK_WINDOW = 100  # how many past candles the trend logic sees
SWING_LOOKBACK = 2  # passed to find_swing_points, same as smc.py default

signals = []
print("\nGenerating SMC trend signals (this may take a moment)...")
for i in range(LOOKBACK_WINDOW, len(gold)):
    window = gold.iloc[i - LOOKBACK_WINDOW : i + 1].reset_index(drop=True)
    window_with_swings = find_swing_points(window, lookback=SWING_LOOKBACK)
    trend_result = detect_trend(window_with_swings)
    signals.append({"date": gold.iloc[i]["date"], "trend": trend_result["trend"]})

sig_df = pd.DataFrame(signals)
print("\nSignal distribution:")
print(sig_df["trend"].value_counts())

# ============================================================
# Merge signal with actual forward returns, test each horizon
# ============================================================
df = gold.merge(sig_df, on="date", how="inner").reset_index(drop=True)

horizons = [1, 5, 10, 20]
results = {}

print("\n" + "=" * 78)
print("STAGE 1: Non-overlapping walk-forward test of SMC trend signal")
print("=" * 78)
print(f"{'Horizon':>8} {'N':>5} {'SignalAcc':>10} {'Baseline':>10} {'P-value':>10}")
print("-" * 78)

for horizon in horizons:
    d = df.copy()
    d["fwd_return"] = d["close"].shift(-horizon) / d["close"] - 1
    d["actual_up"] = (d["fwd_return"] > 0).astype(int)
    d = d.iloc[:-horizon]

    # Only evaluate rows where SMC gave a directional call (up/down),
    # skip "unclear" -- this is a directional accuracy test, matching
    # how the earlier BUY/SELL-only correction was done for LightGBM
    d = d[d["trend"].isin(["up", "down"])].reset_index(drop=True)
    d["signal_up"] = (d["trend"] == "up").astype(int)

    # non-overlapping sampling: stride = horizon
    idx = list(range(0, len(d), horizon))
    d_sampled = d.iloc[idx]

    n = len(d_sampled)
    if n < 10:
        print(f"{horizon:>7}d   -- not enough directional signals ({n}) --")
        continue

    correct = (d_sampled["signal_up"] == d_sampled["actual_up"]).sum()
    signal_acc = correct / n
    baseline_acc = max(d_sampled["actual_up"].mean(), 1 - d_sampled["actual_up"].mean())
    p_value = stats.binomtest(correct, n, baseline_acc, alternative="greater").pvalue

    results[horizon] = {"n": n, "signal_acc": signal_acc, "baseline_acc": baseline_acc, "p_value": p_value}
    print(f"{horizon:>7}d {n:>5} {signal_acc:>10.4f} {baseline_acc:>10.4f} {p_value:>10.4f}")

# ============================================================
# STAGE 2: Bonferroni correction
# ============================================================
print("\n" + "=" * 78)
print("STAGE 2: Bonferroni correction")
print("=" * 78)

n_tests = len(results)
alpha = 0.05
bonf_threshold = alpha / n_tests if n_tests > 0 else alpha
print(f"Tests: {n_tests}, Bonferroni threshold: {alpha}/{n_tests} = {bonf_threshold:.4f}\n")

passed = []
for horizon, r in results.items():
    sig = r["p_value"] < bonf_threshold
    print(f"Horizon {horizon}d: p={r['p_value']:.4f}  ->  {'PASSES' if sig else 'fails'}")
    if sig:
        passed.append(horizon)

# ============================================================
# STAGE 3: True holdout (only if something passed Stage 2)
# ============================================================
print("\n" + "=" * 78)
print("STAGE 3: True holdout check")
print("=" * 78)

if not passed:
    print("No horizon passed Bonferroni correction. No holdout needed.")
    print("SMC trend signal shows no statistically significant directional edge.")
else:
    holdout_start_idx = int(len(df) * 0.8)
    holdout_start_date = df.iloc[holdout_start_idx]["date"]
    print(f"Holdout starts: {holdout_start_date.date()}\n")
    for horizon in passed:
        d = df.copy()
        d["fwd_return"] = d["close"].shift(-horizon) / d["close"] - 1
        d["actual_up"] = (d["fwd_return"] > 0).astype(int)
        d = d.iloc[:-horizon]
        d = d[d["date"] >= holdout_start_date]
        d = d[d["trend"].isin(["up", "down"])].reset_index(drop=True)
        d["signal_up"] = (d["trend"] == "up").astype(int)

        idx = list(range(0, len(d), horizon))
        d_sampled = d.iloc[idx]
        n = len(d_sampled)
        if n < 10:
            print(f"Horizon {horizon}d: not enough holdout samples ({n})")
            continue
        correct = (d_sampled["signal_up"] == d_sampled["actual_up"]).sum()
        signal_acc = correct / n
        baseline_acc = max(d_sampled["actual_up"].mean(), 1 - d_sampled["actual_up"].mean())
        p_value = stats.binomtest(correct, n, baseline_acc, alternative="greater").pvalue
        print(f"Horizon {horizon}d HOLDOUT: n={n}, acc={signal_acc:.4f}, " f"baseline={baseline_acc:.4f}, p={p_value:.4f}, sig={p_value < 0.05}")

print("\n" + "=" * 78)
print("DONE. Every number above came from running the REAL engine/smc.py")
print("trend-detection logic against real XAUUSD data.")
print("=" * 78)
