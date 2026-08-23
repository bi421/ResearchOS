"""
C++ backtest regression test for ResearchOS.

Uses the current ResearchOS CppQuantAdapter.
Does not depend on the legacy cpp_quant.CppQuant API.
"""

from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from researchos.quant_engine.cpp_backend import CppQuantAdapter

SMA_FAST = 20
SMA_SLOW = 50


@pytest.fixture(scope="module")
def cpp_engine() -> CppQuantAdapter:
    engine = CppQuantAdapter()

    if not engine.is_cpp:
        pytest.fail("C++ Quant Engine is not active. " "Refusing to run a C++ regression test against Python fallback.")

    return engine


def load_xauusd_1d() -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[2]

    data_path = project_root / "data" / "raw" / "histdata" / "xauusd"

    if not data_path.exists():
        pytest.fail(f"XAUUSD data directory not found: {data_path}")

    files = sorted(glob.glob(str(data_path / "DAT_ASCII_XAUUSD_M1_*.csv")))

    if not files:
        pytest.fail(f"No XAUUSD M1 CSV files found in: {data_path}")

    frames = []

    for file_path in files:
        df = pd.read_csv(
            file_path,
            sep=";",
            header=None,
            names=[
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
            dtype={"datetime": str},
        )

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            format="%Y%m%d %H%M%S",
            errors="coerce",
        )

        df = df.dropna(subset=["datetime", "close"])

        if df.empty:
            continue

        df = df.set_index("datetime")

        for column in ["open", "high", "low", "close", "volume"]:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        frames.append(df)

    if not frames:
        pytest.fail("No valid XAUUSD data loaded.")

    df = pd.concat(frames).sort_index()

    df = df[~df.index.duplicated(keep="first")]

    df = df.dropna(subset=["open", "high", "low", "close"])

    daily = (
        df.resample("1D")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna(subset=["open", "high", "low", "close"])
    )

    if len(daily) <= SMA_SLOW + 2:
        pytest.fail(f"Insufficient XAUUSD daily data: {len(daily)} rows")

    return daily


def build_sma_strategy(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, int]:
    data = df.copy()

    data["sma20"] = data["close"].rolling(SMA_FAST).mean()

    data["sma50"] = data["close"].rolling(SMA_SLOW).mean()

    data = data.dropna(subset=["sma20", "sma50"]).copy()

    data["signal"] = np.where(
        data["sma20"] > data["sma50"],
        1.0,
        -1.0,
    )

    # Next-bar execution prevents same-bar look-ahead.
    data["position"] = data["signal"].shift(1).fillna(0.0)

    data["market_return"] = data["close"].pct_change().fillna(0.0)

    data["strategy_return"] = data["position"] * data["market_return"]

    returns = data["strategy_return"].iloc[1:].astype(float)

    if returns.empty:
        pytest.fail("SMA20/50 produced no strategy returns.")

    if not np.isfinite(returns.to_numpy()).all():
        pytest.fail("SMA20/50 produced NaN or infinite returns.")

    position_changes = data["position"].diff().fillna(0.0).abs()

    trades = int((position_changes > 0.0).sum())

    return data, returns, trades


def run_cpp_metrics(
    engine: CppQuantAdapter,
    returns: pd.Series,
) -> dict:
    values = [float(x) for x in returns.to_numpy()]

    if len(values) < 2:
        pytest.fail("Not enough strategy returns.")

    if not np.isfinite(np.asarray(values)).all():
        pytest.fail("Strategy returns contain non-finite values.")

    initial_capital = 100000.0

    equity_curve = [initial_capital]

    for r in values:
        equity_curve.append(equity_curve[-1] * (1.0 + r))

    prices = [1.0]

    for r in values:
        prices.append(prices[-1] * (1.0 + r))

    cpp_returns = engine.calculate_returns(
        prices,
        return_type="percentage",
    )

    statistics = engine.calculate_statistics(values)

    metrics = engine.calculate_metrics(
        values,
        equity_curve,
        risk_free_rate=0.0,
    )

    assert cpp_returns
    assert statistics
    assert metrics

    return {
        "cpp_returns": cpp_returns,
        "statistics": statistics,
        "metrics": metrics,
        "equity_curve": equity_curve,
    }


def calculate_winrate(
    returns: pd.Series,
) -> float:
    values = returns.to_numpy(dtype=float)

    values = values[values != 0.0]

    if len(values) == 0:
        return 0.0

    return float((values > 0.0).sum()) / len(values) * 100.0


def calculate_total_return(
    returns: pd.Series,
) -> float:
    values = returns.to_numpy(dtype=float)

    return float(np.prod(1.0 + values) - 1.0) * 100.0


def test_cpp_engine_is_active(
    cpp_engine: CppQuantAdapter,
):
    assert cpp_engine.is_cpp is True

    version = cpp_engine.get_version()

    assert version
    assert version != "python_fallback"


def test_sma_20_50_winrate(
    cpp_engine: CppQuantAdapter,
):
    df = load_xauusd_1d()

    _, returns, trades = build_sma_strategy(df)

    assert trades >= 5

    result = run_cpp_metrics(
        cpp_engine,
        returns,
    )

    winrate = calculate_winrate(returns)

    assert np.isfinite(winrate)

    assert 20.0 <= winrate <= 80.0, f"SMA20/50 winrate {winrate:.2f}% " f"outside regression sanity range."

    assert result["statistics"]
    assert result["metrics"]


def test_sma_20_50_trades_count(
    cpp_engine: CppQuantAdapter,
):
    df = load_xauusd_1d()

    _, returns, trades = build_sma_strategy(df)

    result = run_cpp_metrics(
        cpp_engine,
        returns,
    )

    assert result["statistics"]
    assert trades >= 5, f"SMA20/50 generated {trades} trades; " f"expected at least 5."


def test_sma_20_50_total_return_range(
    cpp_engine: CppQuantAdapter,
):
    df = load_xauusd_1d()

    _, returns, trades = build_sma_strategy(df)

    assert trades >= 5

    result = run_cpp_metrics(
        cpp_engine,
        returns,
    )

    total_return = calculate_total_return(returns)

    assert np.isfinite(total_return)

    assert -95.0 <= total_return <= 1000.0, f"SMA20/50 total return {total_return:.2f}% " f"outside regression sanity range."

    assert result["metrics"]
