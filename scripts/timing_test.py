import sys

sys.path.append("cpp_quant/python")
import glob
import time

import pandas as pd
from cpp_quant import CppQuant

print("=" * 60)
print("??????? ?????????")
print("=" * 60)

t0 = time.time()
all_dfs = []
for f in glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv"):
    df = pd.read_csv(
        f,
        sep=";",
        header=None,
        names=["datetime", "open", "high", "low", "close", "volume"],
        dtype={"datetime": str},
    )
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S", errors="coerce")
    df = df.dropna(subset=["datetime"])
    df.set_index("datetime", inplace=True)
    all_dfs.append(df)

df = pd.concat(all_dfs).sort_index()
t1 = time.time()
print(f"CSV ????? + concat: {t1 - t0:.2f} ??? ({len(df):,} ???)")

timeframes = [("1min", "1min"), ("5min", "5min"), ("1h", "1h"), ("1D", "1D")]

for label, rule in timeframes:
    ta = time.time()
    df_resampled = df.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    tb = time.time()

    engine = CppQuant()
    engine.load_from_dataframe(df_resampled)
    tc = time.time()

    result = engine.run_sma(20, 50)
    td = time.time()

    print(f"{label}: resample={tb - ta:.2f}s | load_from_dataframe={tc - tb:.2f}s | run_sma={td - tc:.2f}s | candles={len(df_resampled):,}")
