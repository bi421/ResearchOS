"""Strict real-data loader used by legacy analysis entry points.

This module is deliberately fail-closed.  Missing market data, synthetic
fallbacks, random macro factors, and forward-filled macro observations are
not acceptable inputs to ResearchOS evidence.
"""

from pathlib import Path

import pandas as pd


DEFAULT_XAUUSD_PATH = Path("data/curated/xauusd/xauusd_daily.csv")
DEFAULT_MACRO_PATHS = {
    "dxy": Path("data/macro/raw/DXY_Dukascopy_2021_2025.csv"),
    "us10y": Path("data/macro/raw/DGS10_fred.csv"),
    "vix": Path("data/macro/raw/VIXCLS_fred.csv"),
}


def _read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"required real-data source not found: {path}")
    return pd.read_csv(path)


def _date_column(df: pd.DataFrame, path: Path) -> str:
    for name in ("date", "timestamp", "observation_date", "time"):
        if name in df.columns:
            return name
    raise ValueError(f"no supported date column in {path}")


def _value_column(df: pd.DataFrame, path: Path) -> str:
    for name in ("close", "value", "DGS10", "VIXCLS"):
        if name in df.columns:
            return name
    raise ValueError(f"no supported scalar/close column in {path}")


def _normalise_daily_scalar(path: Path, output_name: str) -> pd.DataFrame:
    df = _read_table(path)
    date_col = _date_column(df, path)
    value_col = _value_column(df, path)
    out = df[[date_col, value_col]].copy()
    out["date"] = pd.to_datetime(out[date_col], utc=True, errors="raise").dt.normalize()
    out[output_name] = pd.to_numeric(out[value_col], errors="raise")
    out = out[["date", output_name]]
    if out["date"].duplicated().any():
        raise ValueError(f"duplicate daily observations in {path}")
    if not out[output_name].map(pd.api.types.is_number).all():
        raise ValueError(f"non-numeric values in {path}")
    return out


def load_and_merge_real_data(
    xauusd_path: Path = DEFAULT_XAUUSD_PATH,
    macro_paths: dict[str, Path] | None = None,
) -> pd.DataFrame:
    """Load real XAUUSD and macro data with exact daily inner alignment.

    No synthetic fallback, random data, interpolation, or forward-fill is
    performed.  Missing sources or duplicate dates fail immediately.
    """
    macro_paths = macro_paths or DEFAULT_MACRO_PATHS
    required = {"dxy", "us10y", "vix"}
    if set(macro_paths) != required:
        raise ValueError(f"macro_paths must contain exactly {sorted(required)}")

    xau = _read_table(xauusd_path)
    date_col = _date_column(xau, xauusd_path)
    required_xau = {"open", "high", "low", "close"}
    missing = required_xau - set(xau.columns)
    if missing:
        raise ValueError(f"XAUUSD source missing columns: {sorted(missing)}")

    xau = xau.copy()
    xau["date"] = pd.to_datetime(xau[date_col], utc=True, errors="raise").dt.normalize()
    if xau["date"].duplicated().any():
        raise ValueError(f"duplicate daily XAUUSD observations in {xauusd_path}")
    for column in ("open", "high", "low", "close"):
        xau[column] = pd.to_numeric(xau[column], errors="raise")
    xau = xau[["date", "open", "high", "low", "close"]]

    merged = xau
    for name in ("dxy", "us10y", "vix"):
        merged = merged.merge(_normalise_daily_scalar(macro_paths[name], name), on="date", how="inner")

    merged = merged.sort_values("date").reset_index(drop=True)
    if merged.empty:
        raise ValueError("real-data intersection is empty")
    if merged["date"].duplicated().any():
        raise ValueError("merged real-data intersection contains duplicate dates")

    print(f"✅ Real aligned data: {len(merged)} rows")
    print(f"   First day: {merged['date'].iloc[0].date()}")
    print(f"   Last day : {merged['date'].iloc[-1].date()}")
    return merged


if __name__ == "__main__":
    real_df = load_and_merge_real_data()
    print("\n📊 Эхний 5 мөр:")
    print(real_df.head())
