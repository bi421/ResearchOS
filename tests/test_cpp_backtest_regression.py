"""
Regression test for C++ backtest engine.
Ensures that SMA 20/50 strategy produces consistent winrate on XAUUSD 1D data.
"""

import glob
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cpp_quant" / "python"))

try:
    from cpp_quant import CppQuant

    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False
    pytest.skip("C++ quant engine not available", allow_module_level=True)


def load_xauusd_1d() -> pd.DataFrame:
    """Load XAUUSD 1D data from CSV files."""
    data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "histdata" / "xauusd"
    if not data_path.exists():
        pytest.skip("XAUUSD data not found")
    dfs = []
    for f in glob.glob(str(data_path / "DAT_ASCII_XAUUSD_M1_*.csv")):
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
        dfs.append(df)
    if not dfs:
        pytest.skip("No XAUUSD CSV files found")
    df = pd.concat(dfs).sort_index()
    df_d = df.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    return df_d


def test_sma_20_50_winrate():
    """SMA 20/50 strategy winrate should be ~50% for XAUUSD 1D."""
    if not CPP_AVAILABLE:
        pytest.skip("C++ engine not available")
    df = load_xauusd_1d()
    if df.empty:
        pytest.skip("No data loaded")
    engine = CppQuant()
    engine.load_from_dataframe(df)
    result = engine.run_sma(20, 50)
    winrate = result["winrate"]  # Already a percentage
    # Winrate should be around 50% for a random strategy
    # Allow +/-15% margin due to small sample size
    assert 35 <= winrate <= 65, f"Winrate {winrate:.2f}% expected 35-65%"


def test_sma_20_50_trades_count():
    """SMA 20/50 should have at least 5 trades on 1D data."""
    if not CPP_AVAILABLE:
        pytest.skip("C++ engine not available")
    df = load_xauusd_1d()
    if df.empty:
        pytest.skip("No data loaded")
    engine = CppQuant()
    engine.load_from_dataframe(df)
    result = engine.run_sma(20, 50)
    assert result["num_trades"] >= 5, f"Trades {result['num_trades']} should be >= 5"


def test_sma_20_50_total_return_range():
    """Total return should be within reasonable range."""
    if not CPP_AVAILABLE:
        pytest.skip("C++ engine not available")
    df = load_xauusd_1d()
    if df.empty:
        pytest.skip("No data loaded")
    engine = CppQuant()
    engine.load_from_dataframe(df)
    result = engine.run_sma(20, 50)
    # Total return should be between -50% and +150% (reasonable for 4 years)
    total_return = result["total_return"]  # Already a percentage
    assert -50 <= total_return <= 150, f"Total return {total_return:.2f}% outside range"
