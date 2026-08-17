"""
H1 feature sweep with Bonferroni-corrected significance.
Resamples M1 -> H1, uses M1 tick-count as a legitimate volume proxy,
and re-runs the Phase 5.1 feature sweep with a corrected alpha to
avoid the multiple-testing false positive seen in the D1 sweep.
"""

import json

import pandas as pd

from researchos.data_engine.loader import CsvLoader
from researchos.experiments.phase51 import Phase51Config, run_phase51

RAW_M1 = "data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv"
H1_OUT = "data/curated/xauusd/xauusd_h1_2021_2025_mt5.csv"

FEATURE_NAMES = [
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
]


def build_h1():
    df = pd.read_csv(RAW_M1)
    df["dt"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%Y.%m.%d %H:%M:%S")
    df = df.set_index("dt").sort_index()

    h1 = df.resample("1h").agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
        }
    )
    # legitimate volume proxy: number of M1 ticks observed in each H1 bucket
    h1["tick_volume"] = df["Open"].resample("1h").count()
    h1 = h1.dropna(subset=["Open", "High", "Low", "Close"])
    h1 = h1[h1["tick_volume"] > 0]

    h1 = h1.reset_index()
    h1["Date"] = h1["dt"].dt.strftime("%Y.%m.%d")
    h1["Time"] = h1["dt"].dt.strftime("%H:%M:%S")
    h1 = h1[["Date", "Time", "Open", "High", "Low", "Close", "tick_volume"]]
    h1.to_csv(H1_OUT, index=False)
    print(f"Wrote {len(h1)} H1 bars -> {H1_OUT}")
    return len(h1)


def main():
    build_h1()

    loader = CsvLoader()
    candles = loader.load_mt5_candles(H1_OUT, symbol="XAUUSD", timeframe="1h")
    close = [c.close for c in candles]
    high = [c.high for c in candles]
    low = [c.low for c in candles]
    volume = [c.volume for c in candles]
    print(f"Loaded {len(candles)} candles, volume[0]={volume[0]}")

    n = len(close)
    train_size = int(n * 0.65)
    valid_size = int(n * 0.10)
    step_size = valid_size

    alpha_raw = 0.05
    alpha_corrected = alpha_raw / len(FEATURE_NAMES)
    print(f"train={train_size} valid={valid_size} step={step_size}")
    print(f"Bonferroni-corrected alpha = {alpha_corrected:.5f}\n")

    results = []
    for idx, fname in enumerate(FEATURE_NAMES):
        cfg = Phase51Config(
            symbol="XAUUSD",
            timeframe="1h",
            horizon=5,
            threshold=0.0,
            train_size=train_size,
            validation_size=valid_size,
            step_size=step_size,
            estimator_feature=idx,
            spread_spec="fixed:0.20",
            slippage_spec="fixed:0.10",
            commission_spec="fixed:0.05",
        )
        res = run_phase51(close, high, low, volume, cfg)
        d = res.to_dict() if hasattr(res, "to_dict") else res.__dict__

        model_acc = d.get("model", {}).get("accuracy")
        base_acc = d.get("baseline", {}).get("accuracy")
        p_value = d.get("significance", {}).get("p_value")
        sig_raw = p_value is not None and p_value < alpha_raw
        sig_corrected = p_value is not None and p_value < alpha_corrected

        results.append(
            {
                "feature": fname,
                "model_acc": model_acc,
                "baseline_acc": base_acc,
                "p_value": p_value,
                "sig_raw_0.05": sig_raw,
                "sig_bonferroni": sig_corrected,
            }
        )
        flag = "***" if sig_corrected else ("*" if sig_raw else "")
        print(f"{fname:20s} model={model_acc:.4f} base={base_acc:.4f} p={p_value:.4f} {flag}")

    passed = [r for r in results if r["sig_bonferroni"]]
    print(f"\nFeatures passing Bonferroni-corrected significance: {len(passed)}")
    for r in passed:
        print(
            f"  -> {r['feature']} (p={r['p_value']:.5f}, model={r['model_acc']:.4f} vs base={r['baseline_acc']:.4f})"
        )

    with open("data/curated/xauusd/phase51_h1_sweep_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved: data/curated/xauusd/phase51_h1_sweep_results.json")


if __name__ == "__main__":
    main()
