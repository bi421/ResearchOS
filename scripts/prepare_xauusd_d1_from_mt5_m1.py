"""Prepare the canonical XAUUSD D1 CSV from an MT5 M1 CSV or ZIP archive.

Accepted M1 columns:
    time, open, high, low, close, tick_volume

Optional columns such as spread and real_volume are ignored for D1 aggregation.
The output format intentionally matches ``load_xauusd_d1``:
    Date, Time, Open, High, Low, Close, tick_volume

Example:
    python scripts/prepare_xauusd_d1_from_mt5_m1.py \
        --input data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.zip \
        --output data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import polars as pl


REQUIRED = {"time", "open", "high", "low", "close", "tick_volume"}


def _read_input(path: Path) -> pl.DataFrame:
    if path.suffix.lower() != ".zip":
        return pl.read_csv(path)

    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV file found inside {path}")
        if len(csv_names) > 1:
            csv_names.sort()
        with archive.open(csv_names[0]) as handle:
            return pl.read_csv(io.BytesIO(handle.read()))


def _normalise(df: pl.DataFrame) -> pl.DataFrame:
    missing = REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"MT5 M1 input is missing required columns: {sorted(missing)}")

    out = df.select(
        [
            pl.col("time").cast(pl.String),
            pl.col("open").cast(pl.Float64),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
            pl.col("tick_volume").cast(pl.Float64),
        ]
    )
    out = out.with_columns(
        pl.col("time")
        .str.to_datetime(strict=False, time_zone="UTC")
        .alias("timestamp")
    )
    if out["timestamp"].null_count():
        raise ValueError("M1 input contains timestamps that cannot be parsed")

    invalid = out.filter(
        (pl.col("open") <= 0)
        | (pl.col("high") <= 0)
        | (pl.col("low") <= 0)
        | (pl.col("close") <= 0)
        | (pl.col("high") < pl.max_horizontal("open", "close", "low"))
        | (pl.col("low") > pl.min_horizontal("open", "close", "high"))
        | (pl.col("tick_volume") < 0)
    )
    if invalid.height:
        raise ValueError(f"M1 input contains {invalid.height} invalid OHLCV rows")

    return (
        out.drop("time")
        .unique(subset=["timestamp"], keep="first")
        .sort("timestamp")
    )


def _aggregate_d1(m1: pl.DataFrame) -> pl.DataFrame:
    d1 = (
        m1.group_by_dynamic("timestamp", every="1d", closed="left", label="left")
        .agg(
            [
                pl.col("open").first().alias("Open"),
                pl.col("high").max().alias("High"),
                pl.col("low").min().alias("Low"),
                pl.col("close").last().alias("Close"),
                pl.col("tick_volume").sum().round(0).cast(pl.Int64).alias("tick_volume"),
            ]
        )
        .drop_nulls()
        .sort("timestamp")
    )
    return d1.select(
        [
            pl.col("timestamp").dt.strftime("%Y.%m.%d").alias("Date"),
            pl.col("timestamp").dt.strftime("%H:%M:%S").alias("Time"),
            "Open",
            "High",
            "Low",
            "Close",
            "tick_volume",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="MT5 M1 CSV or ZIP archive")
    parser.add_argument("--output", required=True, help="Canonical D1 CSV output")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"M1 input not found: {input_path}")

    raw = _read_input(input_path)
    m1 = _normalise(raw)
    d1 = _aggregate_d1(m1)

    if d1.height < 100:
        raise ValueError(f"Only {d1.height} D1 bars were produced; refusing to publish")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    d1.write_csv(output_path)

    print(f"M1 rows (deduplicated): {m1.height}")
    print(f"D1 rows              : {d1.height}")
    print(f"D1 start              : {d1['Date'][0]} {d1['Time'][0]}")
    print(f"D1 end                : {d1['Date'][-1]} {d1['Time'][-1]}")
    print(f"Output                : {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
