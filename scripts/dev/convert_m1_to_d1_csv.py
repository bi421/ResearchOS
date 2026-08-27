from pathlib import Path

import polars as pl

PARQUET = Path("data/curated/xauusd/xauusd_m1_2023_2025.parquet")
OUT_CSV = Path("data/curated/xauusd/xauusd_d1_2023_2025_from_m1.csv")
df = pl.read_parquet(PARQUET).sort("ts_utc")
print(f"Columns: {df.columns}")
vol_col = "volume" if "volume" in df.columns else "vol"
print(f"Using vol col: {vol_col}")
# M1 -> D1 OHLCV
d1 = (
    df.group_by_dynamic("ts_utc", every="1d")
    .agg(
        [
            pl.col("open").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
            pl.col(vol_col).sum().alias("volume"),
        ]
    )
    .sort("ts_utc")
    .drop_nulls()
)
print(f"D1 bars from M1: {d1.height} - Required: 2000 - Enough? {d1.height >= 2000}")
d1.select([pl.col("ts_utc").alias("time"), "open", "high", "low", "close", "volume"]).write_csv(OUT_CSV)
print(f"Saved to {OUT_CSV}")
