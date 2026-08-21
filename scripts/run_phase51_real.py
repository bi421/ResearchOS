import json
import math
from datetime import datetime
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path("C:/Users/User/Desktop/ResearchOS")
PARQUET = PROJECT_ROOT / "data" / "curated" / "xauusd" / "xauusd_m1_2023_2025.parquet"
RESULT_DIR = PROJECT_ROOT / "data" / "curated" / "xauusd"
RESULT_DIR.mkdir(exist_ok=True)

print(f"Loading {PARQUET}...")
df = pl.read_parquet(PARQUET).sort("ts_utc")
print(f"Loaded M1: {len(df)} rows {df['ts_utc'].min()} -> {df['ts_utc'].max()}")

# 1. M1 -> H1 resample (1M row -> 18k row, backtest 10x хурдан)
print("Resampling M1 -> H1...")
df_h1 = (
    df.sort("ts_utc")
    .group_by_dynamic("ts_utc", every="1h")
    .agg(
        [
            pl.col("open").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
        ]
    )
    .filter(pl.col("close").is_not_null())
    .sort("ts_utc")
)
print(f"H1 rows: {len(df_h1)}")

# 2. Simple Baseline Strategy: SMA 50 vs SMA 200 crossover (H1)
df_h1 = df_h1.with_columns(
    [
        pl.col("close").rolling_mean(window_size=50).alias("sma50"),
        pl.col("close").rolling_mean(window_size=200).alias("sma200"),
    ]
)
df_h1 = df_h1.with_columns((pl.col("close") / pl.col("close").shift(1) - 1).alias("ret"))
df_h1 = df_h1.with_columns((pl.when(pl.col("sma50") > pl.col("sma200")).then(1).otherwise(0)).alias("pos"))
df_h1 = df_h1.with_columns((pl.col("pos").shift(1) * pl.col("ret")).alias("strat_ret"))
df_h1 = df_h1.filter(pl.col("sma200").is_not_null())

# 3. Walk-Forward Split: 2023-2024 Train / 2025 Test
train = df_h1.filter(pl.col("ts_utc") < datetime(2025, 1, 1))
test = df_h1.filter(pl.col("ts_utc") >= datetime(2025, 1, 1))


def metrics(d):
    if len(d) == 0:
        return {}
    mean = d["strat_ret"].mean()
    std = d["strat_ret"].std()
    sharpe = (mean / std * math.sqrt(252 * 24)) if std and std != 0 else 0
    # Cumulative
    cum = (1 + d["strat_ret"].fill_null(0)).cum_prod()
    peak = cum.cum_max()
    dd = cum / peak - 1
    max_dd = dd.min()
    win_rate = (
        (d.filter(pl.col("strat_ret") > 0).height / d.filter(pl.col("pos") == 1).height * 100) if d.filter(pl.col("pos") == 1).height > 0 else 0
    )
    total_ret = cum[-1] - 1 if len(cum) > 0 else 0
    return {
        "rows": len(d),
        "total_return_pct": round(float(total_ret * 100), 2),
        "sharpe": round(float(sharpe), 3),
        "max_drawdown_pct": round(float(max_dd * 100), 2),
        "win_rate_pct": round(float(win_rate), 2),
        "avg_ret_bps": round(float(mean * 10000), 2) if mean else 0,
    }


train_m = metrics(train)
test_m = metrics(test)
full_m = metrics(df_h1)

print("\n=== PHASE 5.1 REAL DATA VALIDATION (XAUUSD H1) ===")
print(f"TRAIN 2023-2024: {train_m}")
print(f"TEST 2025 : {test_m}")
print(f"FULL 2023-2025: {full_m}")

# 4. Save evidence (for your RELEASE_CANDIDATE_v1.0_EVIDENCE.md)
result = {
    "dataset": str(PARQUET),
    "dataset_sha256": (RESULT_DIR / "xauusd_m1_2023_2025.sha256").read_text().split()[0]
    if (RESULT_DIR / "xauusd_m1_2023_2025.sha256").exists()
    else "unknown",
    "timeframe": "H1 resampled from M1",
    "strategy": "SMA50 > SMA200 long-only baseline",
    "train": train_m,
    "test": test_m,
    "full": full_m,
    "generated_at": datetime.utcnow().isoformat(),
}
out_path = RESULT_DIR / "phase51_real_baseline.json"
out_path.write_text(json.dumps(result, indent=2))
print(f"\nEvidence saved: {out_path}")
