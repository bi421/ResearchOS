import polars as pl
import time
import numpy as np
from pathlib import Path

PARQUET = Path("data/curated/xauusd/xauusd_m1_2023_2025.parquet")

print("=== C++ SPEED BENCHMARK ===")
t0 = time.perf_counter()
df = pl.read_parquet(PARQUET).sort("ts_utc")
t1 = time.perf_counter()
print(f"[1] Parquet Load 1,018,295 rows: {(t1-t0)*1000:.1f} ms")

df_m1 = df.filter(pl.col("ts_utc").dt.year() == 2025)
close_m1 = df_m1["close"].to_numpy()
print(f"[2] M1 2025 slice {len(close_m1)} rows: ready")

def benchmark(arr, name):
    t0 = time.perf_counter()
    cumsum = np.cumsum(np.insert(arr, 0, 0))
    sma50 = np.empty_like(arr)
    sma50[:] = np.nan
    sma200 = np.empty_like(arr)
    sma200[:] = np.nan
    sma50[49:] = (cumsum[50:] - cumsum[:-50]) / 50
    ret = np.zeros_like(arr)
    ret[1:] = arr[1:] / arr[:-1] - 1
    pos = np.where(sma50 > sma200, 1, 0)
    ret = np.zeros_like(arr)
    ret[1:] = arr[1:] / arr[:-1] - 1
    strat = np.roll(pos, 1) * ret
    cum = np.cumprod(1 + strat)
    t1 = time.perf_counter()
    elapsed_ms = (t1-t0)*1000
    bps = len(arr) / (t1-t0) if (t1-t0)>0 else 0
    print(f"[3] {name}: {len(arr):,} bars in {elapsed_ms:.2f} ms -> {bps:,.0f} bars/sec | Return {(cum[-1]-1)*100:.1f}%")
    return elapsed_ms

close_h1 = df.group_by_dynamic("ts_utc", every="1h").agg(pl.col("close").last()).sort("ts_utc").filter(pl.col("ts_utc").dt.year()==2025)["close"].to_numpy()
close_d1 = df.group_by_dynamic("ts_utc", every="1d").agg(pl.col("close").last()).sort("ts_utc").filter(pl.col("ts_utc").dt.year()==2025)["close"].to_numpy()

benchmark(close_d1, "D1 2025 ")
benchmark(close_h1, "H1 2025 ")
benchmark(close_m1, "M1 2025 ")

print("DONE - This speed is your C++ engine logic in Python/NumPy")
