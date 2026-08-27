import math
from datetime import datetime
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path("C:/Users/User/Desktop/ResearchOS")
# ???? DST-??? ????
PARQUET_CLEAN = PROJECT_ROOT / "data" / "curated" / "xauusd" / "xauusd_m1_2021_2025_clean.parquet"
PARQUET_OLD = PROJECT_ROOT / "data" / "curated" / "xauusd" / "xauusd_m1_2023_2025.parquet"

print(f"Loading clean {PARQUET_CLEAN}...")
df = pl.read_parquet(PARQUET_CLEAN).sort("timestamp")
# ts_utc ?????? ???????? (?????? ts_utc ??????)
if "ts_utc" not in df.columns and "timestamp" in df.columns:
    df = df.rename({"timestamp": "ts_utc"})
print(f"Loaded: {len(df)} rows {df['ts_utc'].min()} -> {df['ts_utc'].max()}")

# M1 -> H1
df_h1 = (
    df.sort("ts_utc")
    .group_by_dynamic("ts_utc", every="1h")
    .agg(
        [
            pl.col("Open").first().alias("open") if "Open" in df.columns else pl.col("open").first().alias("open"),
            pl.col("High").max().alias("high") if "High" in df.columns else pl.col("high").max().alias("high"),
            pl.col("Low").min().alias("low") if "Low" in df.columns else pl.col("low").min().alias("low"),
            pl.col("Close").last().alias("close") if "Close" in df.columns else pl.col("close").last().alias("close"),
        ]
    )
    .filter(pl.col("close").is_not_null())
    .sort("ts_utc")
)
print(f"H1 rows: {len(df_h1)}")

# SMA 50/200
df_h1 = df_h1.with_columns(
    [
        pl.col("close").rolling_mean(50).alias("sma50"),
        pl.col("close").rolling_mean(200).alias("sma200"),
    ]
)
df_h1 = df_h1.with_columns((pl.col("close") / pl.col("close").shift(1) - 1).alias("ret"))
df_h1 = df_h1.with_columns((pl.when(pl.col("sma50") > pl.col("sma200")).then(1).otherwise(0)).alias("pos"))
df_h1 = df_h1.with_columns((pl.col("pos").shift(1) * pl.col("ret")).alias("strat_ret"))
df_h1 = df_h1.filter(pl.col("sma200").is_not_null())

train = df_h1.filter(pl.col("ts_utc") < datetime(2025, 1, 1))
test = df_h1.filter(pl.col("ts_utc") >= datetime(2025, 1, 1))


def metrics(d):
    if len(d) == 0:
        return {}
    mean = d["strat_ret"].mean()
    std = d["strat_ret"].std()
    sharpe = (mean / std * math.sqrt(252 * 24)) if std else 0
    cum = (1 + d["strat_ret"].fill_null(0)).cum_prod()
    peak = cum.cum_max()
    dd = cum / peak - 1
    return {
        "rows": len(d),
        "total_return_pct": round(float((cum[-1] - 1) * 100), 2) if len(cum) > 0 else 0,
        "sharpe": round(float(sharpe), 3),
        "max_drawdown_pct": round(float(dd.min() * 100), 2),
    }


print("TRAIN 2021-2024:", metrics(train))
print("TEST 2025:", metrics(test))
print("FULL 2021-2025:", metrics(df_h1))
