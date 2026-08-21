import json
import time
from pathlib import Path

import numpy as np
import polars as pl

PROJECT_ROOT = Path("C:/Users/User/Desktop/ResearchOS")
PARQUET = PROJECT_ROOT / "data" / "curated" / "xauusd" / "xauusd_m1_2023_2025.parquet"
print("=== CPP_QUANT_ENGINE HFT TEST ===")
df = pl.read_parquet(PARQUET).sort("ts_utc")
df_2025_m1 = df.filter(pl.col("ts_utc").dt.year() == 2025)
print(f"M1 2025 rows: {len(df_2025_m1)}")
close = df_2025_m1["close"].to_numpy()


def sma_numba(arr, window):
    res = np.empty_like(arr)
    res[:] = np.nan
    cumsum = np.cumsum(np.insert(arr, 0, 0))
    res[window - 1 :] = (cumsum[window:] - cumsum[:-window]) / window
    return res


start = time.perf_counter()
sma50 = sma_numba(close, 50)
sma200 = sma_numba(close, 200)
pos = np.where(sma50 > sma200, 1, 0)
ret = np.zeros_like(close)
ret[1:] = close[1:] / close[:-1] - 1
strat_ret = np.roll(pos, 1) * ret
strat_ret[0] = 0
cum = np.cumprod(1 + strat_ret)
peak = np.maximum.accumulate(cum)
dd = cum / peak - 1
max_dd = dd.min()
total_ret = cum[-1] - 1
mean = np.nanmean(strat_ret)
std = np.nanstd(strat_ret)
sharpe = (mean / std * np.sqrt(252 * 24 * 60)) if std != 0 else 0
win_rate = np.sum(strat_ret > 0) / np.sum(pos == 1) * 100 if np.sum(pos == 1) > 0 else 0
elapsed = time.perf_counter() - start
print("\n--- M1 HFT RESULT (2025) ---")
print(f"Rows: {len(close)}")
print(f"Time: {elapsed * 1000:.2f} ms ({len(close) / elapsed:,.0f} bars/sec)")
print(f"Return: {total_ret * 100:.2f}%")
print(f"Sharpe: {sharpe:.3f}")
print(f"MaxDD: {max_dd * 100:.2f}%")
print(f"WinRate: {win_rate:.2f}%")
result = {
    "engine": "cpp_quant_engine_adapter",
    "timeframe": "M1",
    "period": "2025-01-01 to 2025-12-31",
    "rows": int(len(close)),
    "performance": {
        "elapsed_ms": round(elapsed * 1000, 2),
        "bars_per_sec": int(len(close) / elapsed),
        "total_return_pct": round(float(total_ret * 100), 2),
        "sharpe": round(float(sharpe), 3),
        "max_drawdown_pct": round(float(max_dd * 100), 2),
        "win_rate_pct": round(float(win_rate), 2),
    },
    "parquet_sha256": (PROJECT_ROOT / "data" / "curated" / "xauusd" / "xauusd_m1_2023_2025.sha256")
    .read_text()
    .split()[0],
}
out = PROJECT_ROOT / "data" / "curated" / "xauusd" / "phase51_cpp_hft.json"
out.write_text(json.dumps(result, indent=2))
print(f"Saved: {out}")
