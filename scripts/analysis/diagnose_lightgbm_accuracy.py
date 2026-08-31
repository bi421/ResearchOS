"""
Diagnostic script for LightGBM signal generator accuracy calculation.

Checks:
  1. Exact accuracy calculation line and logic
  2. How HOLD signals are treated
  3. Accuracy using only BUY/SELL signals
  4. Direction inversion check
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_CSV = PROJECT_ROOT / "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
SIGNAL_CSV = PROJECT_ROOT / "reports/signals/lightgbm_signals.csv"

print("=" * 70)
print("LightGBM ACCURACY DIAGNOSTIC")
print("=" * 70)

# Load signal file
df = pd.read_csv(SIGNAL_CSV)
print(f"\nSignal file: {SIGNAL_CSV}")
print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

# Load original data to get actual target
gold = pd.read_csv(GOLD_CSV)
date_col = [c for c in gold.columns if c.lower() in ("date", "time", "datetime")][0]
close_col = [c for c in gold.columns if c.lower() == "close"][0]
gold[date_col] = pd.to_datetime(gold[date_col])
gold = gold[[date_col, close_col]].rename(columns={date_col: "date", close_col: "close"})
gold = gold.sort_values("date").reset_index(drop=True)
gold["actual"] = (gold["close"].shift(-1) > gold["close"]).astype(int)
gold = gold[["date", "actual"]].dropna()

# Merge actual into signals
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.merge(gold, left_on="timestamp", right_on="date", how="left")
df = df.dropna(subset=["actual"])
print(f"Rows with actual target: {len(df)}")

# Show distribution
buy_count = (df["signal"] == 1).sum()
sell_count = (df["signal"] == -1).sum()
hold_count = (df["signal"] == 0).sum()
total = len(df)
print("\nSignal distribution:")
print(f"  BUY (1):  {buy_count} ({buy_count/total*100:.1f}%)")
print(f"  SELL (-1): {sell_count} ({sell_count/total*100:.1f}%)")
print(f"  HOLD (0): {hold_count} ({hold_count/total*100:.1f}%)")

# The original accuracy calculation (line 393)
# model_acc = (signals_df.loc[valid_mask, "signal"] == signals_df.loc[valid_mask, "actual"]).mean()
print("\n" + "=" * 70)
print("1. ORIGINAL ACCURACY CALCULATION (line 393)")
print("=" * 70)
print("Code: (signals_df['signal'] == signals_df['actual']).mean()")
print()
print("signal values: {-1, 0, 1}")
print("actual values: {0, 1}  (binary target)")
print()

# Show the comparison matrix
print("Comparison matrix (signal vs actual):")
for sig in [-1, 0, 1]:
    for act in [0, 1]:
        count = ((df["signal"] == sig) & (df["actual"] == act)).sum()
        match = "MATCH" if sig == act else "MISMATCH"
        print(f"  signal={sig:2d}, actual={act} -> {count:4d} rows ({match})")

# Original accuracy
original_acc = (df["signal"] == df["actual"]).mean()
print(f"\nOriginal accuracy: {original_acc:.4f}")
print("This is WRONG because:")
print("  - signal=-1 (SELL) can NEVER equal actual (actual is only 0 or 1)")
print("  - signal=-1 vs actual=0 is counted as WRONG (but SELL for down move IS correct)")
print("  - signal=-1 vs actual=1 is counted as WRONG (correct)")
print("  - All SELL signals are automatically penalized")

# ------------------------------------------------------------------
# 2. HOLD treatment
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("2. HOLD SIGNAL TREATMENT")
print("=" * 70)

hold_df = df[df["signal"] == 0]
print(f"HOLD rows: {len(hold_df)}")
print("HOLD vs actual distribution:")
for act in [0, 1]:
    count = (hold_df["actual"] == act).sum()
    pct = count / len(hold_df) * 100 if len(hold_df) > 0 else 0
    print(f"  actual={act}: {count} ({pct:.1f}%)")

print()
print("HOLD is treated as a DIRECT CLASS LABEL in accuracy calculation:")
print("  - HOLD (0) vs actual=0 (down) -> counted as CORRECT")
print("  - HOLD (0) vs actual=1 (up)   -> counted as WRONG")
print()
print("This means HOLD is implicitly interpreted as 'predict down',")
print("which is semantically incorrect. HOLD means 'no prediction'.")
print("HOLD is NOT subtracted from total — it IS included in the comparison.")

# ------------------------------------------------------------------
# 3. BUY/SELL-only accuracy
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("3. BUY/SELL-ONLY ACCURACY (HOLD excluded)")
print("=" * 70)

trade_df = df[df["signal"] != 0].copy()
print(f"BUY/SELL rows: {len(trade_df)}")
print(f"  BUY:  {(trade_df['signal'] == 1).sum()}")
print(f"  SELL: {(trade_df['signal'] == -1).sum()}")

# For BUY/SELL, convert signal to binary direction:
# signal=1 (BUY) -> predict up (1)
# signal=-1 (SELL) -> predict down (0)
# actual: 1=up, 0=down
trade_df["signal_direction"] = (trade_df["signal"] == 1).astype(int)
trade_only_acc = (trade_df["signal_direction"] == trade_df["actual"]).mean()
print(f"\nBUY/SELL-only accuracy: {trade_only_acc:.4f}")
print("  (signal=1 BUY -> actual=1 is correct)")
print("  (signal=-1 SELL -> actual=0 is correct)")

# Also show breakdown by signal type
buy_df = trade_df[trade_df["signal"] == 1]
sell_df = trade_df[trade_df["signal"] == -1]
if len(buy_df) > 0:
    buy_acc = (buy_df["signal_direction"] == buy_df["actual"]).mean()
    print(f"\n  BUY accuracy:  {buy_acc:.4f} (n={len(buy_df)})")
if len(sell_df) > 0:
    sell_acc = (sell_df["signal_direction"] == sell_df["actual"]).mean()
    print(f"  SELL accuracy: {sell_acc:.4f} (n={len(sell_df)})")

# ------------------------------------------------------------------
# 4. Direction inversion check
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("4. DIRECTION INVERSION CHECK")
print("=" * 70)

# Check if model is predicting opposite of what it should
# LightGBM predicts P(class=1) where class=1 = "up"
# So high probability should mean "up" -> BUY signal
# Low probability should mean "down" -> SELL signal

print("Model output interpretation:")
print("  - LightGBM predict_proba[:, 1] = P(price goes UP)")
print("  - High prob -> BUY signal (signal=1)")
print("  - Low prob -> SELL signal (signal=-1)")
print()

# Check correlation between prediction and actual
corr = df["prediction"].corr(df["actual"])
print(f"Correlation(prediction, actual): {corr:.4f}")

if corr < 0:
    print("WARNING: Negative correlation suggests direction inversion!")
    print("  Model predicts opposite of actual direction.")
else:
    print("Correlation is positive -> no inversion at model output level.")

# Check BUY vs actual
buy_correct = (buy_df["signal_direction"] == buy_df["actual"]).mean() if len(buy_df) > 0 else 0
sell_correct = (sell_df["signal_direction"] == sell_df["actual"]).mean() if len(sell_df) > 0 else 0

print(f"\nBUY correctness rate:  {buy_correct:.4f}")
print(f"SELL correctness rate: {sell_correct:.4f}")

if buy_correct < 0.5 and sell_correct < 0.5:
    print("\nWARNING: Both BUY and SELL are below 50%!")
    print("Possible causes:")
    print("  a) Model is inverted (predicting opposite direction)")
    print("  b) Model is poorly calibrated")
    print("  c) Features have no predictive power on daily timeframe")
    print("  d) Overfitting to noise (walk-forward still sees past data)")
elif buy_correct < 0.5:
    print("\nWARNING: BUY signals are below 50% (inverted for up moves)")
elif sell_correct < 0.5:
    print("\nWARNING: SELL signals are below 50% (inverted for down moves)")

# ------------------------------------------------------------------
# 5. Corrected accuracy (fixing the comparison)
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("5. CORRECTED ACCURACY (proper signal-to-direction mapping)")
print("=" * 70)

# Map signal to direction: BUY=up(1), SELL=down(0), HOLD=ignore
df["signal_as_direction"] = df["signal"].map({1: 1, -1: 0, 0: np.nan})
corrected_df = df.dropna(subset=["signal_as_direction"])

print(f"Rows after excluding HOLD: {len(corrected_df)}")
corrected_acc = (corrected_df["signal_as_direction"] == corrected_df["actual"]).mean()
print(f"Corrected accuracy (BUY/SELL only): {corrected_acc:.4f}")

# Baseline for BUY/SELL subset
trade_baseline = max(corrected_df["actual"].mean(), 1 - corrected_df["actual"].mean())
print(f"Baseline (majority class): {trade_baseline:.4f}")
print(f"Improvement: {corrected_acc - trade_baseline:+.4f}")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Original accuracy (all signals):     {original_acc:.4f}  <-- WRONG (3-way vs 2-way)")
print(f"Corrected accuracy (BUY/SELL only):  {corrected_acc:.4f}  <-- TRUE directional accuracy")
print(f"Baseline accuracy:                   {trade_baseline:.4f}")
print(f"BUY correctness:                     {buy_correct:.4f}")
print(f"SELL correctness:                    {sell_correct:.4f}")
print(f"Correlation(pred, actual):           {corr:.4f}")
print()
print("ROOT CAUSE:")
if original_acc != corrected_acc:
    print("  The 35.59% accuracy is ARTIFICIALLY LOW because:")
    print("  - SELL signals (signal=-1) can never match binary actual {0,1}")
    print("  - All SELL signals are counted as WRONG by construction")
    print("  - This is a comparison bug, not a model failure")
else:
    print("  Accuracy calculation is correct but model has no predictive power.")
