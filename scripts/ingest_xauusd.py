from pathlib import Path
import hashlib
import polars as pl

PROJECT_ROOT = Path("C:/Users/User/Desktop/ResearchOS")
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "xauusd"
CURATED_DIR = PROJECT_ROOT / "data" / "curated" / "xauusd"
CURATED_DIR.mkdir(parents=True, exist_ok=True)

csv_files = sorted(RAW_DIR.glob("DAT_ASCII_XAUUSD_M1_*.csv"))
dfs = []

for f in csv_files:
    print(f"\nReading {f.name}...")
    rows = []
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line=line.strip()
            if not line:
                continue
            # HistData sometimes uses ; sometimes ,
            line = line.replace(';', ',')
            parts = [p.strip() for p in line.split(',') if p.strip()!='']
            if len(parts) == 1:
                # fallback: space split
                parts = line.split()

            if len(parts) == 6:
                # 20230101 000000,open,high,low,close,vol
                ts_raw, o, h, low, c, v = parts
            elif len(parts) == 7:
                # 20230101,000000,open,high,low,close,vol
                d, t, o, h, low, c, v = parts
                ts_raw = f"{d} {t}"
            else:
                continue
            rows.append((ts_raw, o, h, low, c, v))

    if not rows:
        print("  -> 0 rows parsed!")
        continue

    df = pl.DataFrame(rows, schema=["ts_raw","open","high","low","close","vol"], orient="row")
    df = df.with_columns(
        pl.coalesce(
            pl.col("ts_raw").str.strptime(pl.Datetime, "%Y%m%d %H%M%S", strict=False),
            pl.col("ts_raw").str.strptime(pl.Datetime, "%Y%m%d %H%M%S.%f", strict=False),
            pl.col("ts_raw").str.strptime(pl.Datetime, "%Y%m%d %H:%M:%S", strict=False),
            pl.col("ts_raw").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False),
        ).alias("ts_utc")
    )
    df = df.filter(pl.col("ts_utc").is_not_null())
    df = df.with_columns([
        pl.col("open").cast(pl.Float64), pl.col("high").cast(pl.Float64),
        pl.col("low").cast(pl.Float64), pl.col("close").cast(pl.Float64),
        pl.col("vol").cast(pl.Float64),
    ])
    df = df.select(["ts_utc","open","high","low","close","vol"])
    print(f"  -> {df.height} rows: {df['ts_utc'].min()} to {df['ts_utc'].max()}")
    dfs.append(df)

full_df = pl.concat(dfs).sort("ts_utc").unique(subset=["ts_utc"]).sort("ts_utc")
print("\n=== FINAL DATASET ===")
print(f"Rows: {full_df.height}")
print(f"Range: {full_df['ts_utc'].min()} to {full_df['ts_utc'].max()}")

parquet_path = CURATED_DIR / "xauusd_m1_2023_2025.parquet"
full_df.write_parquet(parquet_path, compression="zstd")
print(f"Saved: {parquet_path} ({parquet_path.stat().st_size/1024/1024:.1f} MB)")

h = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
print(f"SHA256: {h}")
(CURATED_DIR / "xauusd_m1_2023_2025.sha256").write_text(f"{h}  {parquet_path.name}\n")
print("DONE")
