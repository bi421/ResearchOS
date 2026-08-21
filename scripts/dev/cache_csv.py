import pandas as pd
import glob

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
df.to_parquet("data/raw/histdata/xauusd/xauusd_m1_cached.parquet")
print(f"?????????: {len(df):,} ???")
