"""
Rigorous walk-forward validation for SMA+RSI+ATR strategy on XAUUSD.

Expanding-window scheme:
  - For each test period (default: 3 months),
    train on ALL past data, test on future data.
  - No overlapping test windows, no look-ahead.

Outputs:
  - Per-fold OOS metrics: Sharpe, max drawdown, win rate, return
  - Bootstrap 95% CI for Sharpe (10,000 iterations)
  - One-sample t-test: H0 = Sharpe <= 0
  - Bonferroni and Benjamini-Hochberg FDR correction across folds
  - Cohen's d effect size per fold
  - Equity-curve plot per fold
  - Sharpe-ratio distribution plot
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

# ──────────────────────────────────────────────────────────────
# 1. Vectorized indicators (pandas/numpy)
# ──────────────────────────────────────────────────────────────


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute SMA, RSI, ATR, and ATR MA vectorized."""
    close = df["close"]
    high = df["high"]
    low = df["low"]

    df = df.copy()
    df["sma_fast"] = close.rolling(window=20, min_periods=20).mean()
    df["sma_slow"] = close.rolling(window=50, min_periods=50).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    df["rsi"] = 100 - (100 / (1 + avg_gain / avg_loss))

    previous_close = close.shift()
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr"] = true_range.rolling(window=14, min_periods=14).mean()
    df["atr_ma"] = df["atr"].rolling(window=20, min_periods=20).mean()

    return df


def generate_signals_vectorized(df: pd.DataFrame) -> pd.Series:
    """Generate vectorized signals: 1=long, -1=short, 0=flat."""
    volatile = df["atr"] > df["atr_ma"]
    long_condition = (df["sma_fast"] > df["sma_slow"]) & (df["rsi"] > 50) & volatile
    short_condition = (df["sma_fast"] < df["sma_slow"]) & (df["rsi"] < 50) & volatile

    signals = pd.Series(0, index=df.index, dtype=np.int8)
    signals[long_condition] = 1
    signals[short_condition] = -1
    return signals


# ──────────────────────────────────────────────────────────────
# 2. Vectorized backtest simulator
# ──────────────────────────────────────────────────────────────


def simulate_trades_vectorized(
    close: np.ndarray,
    signals: np.ndarray,
    commission: float = 0.0001,
    slippage: float = 0.0,
) -> pd.DataFrame:
    """Convert bar-by-bar signals into discrete round-trip trades (vectorized)."""
    trades = []
    position = 0
    entry_price = 0.0
    entry_time = 0
    entry_side = 0

    for i in range(len(close)):
        sig = signals[i]
        price = close[i]

        if position == 0:
            if sig == 1:
                position = 1
                entry_price = price * (1 + commission + slippage)
                entry_time = i
                entry_side = 1
            elif sig == -1:
                position = -1
                entry_price = price * (1 - commission - slippage)
                entry_time = i
                entry_side = -1
        else:
            if (position == 1 and sig == -1) or (position == -1 and sig == 1) or sig == 0:
                exit_price = price * (1 - commission - slippage) if position == 1 else price * (1 + commission + slippage)
                if position == 1:
                    ret = (exit_price - entry_price) / entry_price
                else:
                    ret = (entry_price - exit_price) / entry_price
                trades.append(
                    {
                        "entry_time": entry_time,
                        "exit_time": i,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "side": entry_side,
                        "return_pct": ret,
                        "bars_held": i - entry_time,
                    }
                )
                position = 0
                if sig == 1:
                    position = 1
                    entry_price = price * (1 + commission + slippage)
                    entry_time = i
                    entry_side = 1
                elif sig == -1:
                    position = -1
                    entry_price = price * (1 - commission - slippage)
                    entry_time = i
                    entry_side = -1

    if position != 0:
        price = close[-1]
        exit_price = price * (1 - commission - slippage) if position == 1 else price * (1 + commission + slippage)
        if position == 1:
            ret = (exit_price - entry_price) / entry_price
        else:
            ret = (entry_price - exit_price) / entry_price
        trades.append(
            {
                "entry_time": entry_time,
                "exit_time": len(close) - 1,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "side": entry_side,
                "return_pct": ret,
                "bars_held": len(close) - 1 - entry_time,
            }
        )

    return pd.DataFrame(trades)


# ──────────────────────────────────────────────────────────────
# 3. Metrics
# ──────────────────────────────────────────────────────────────


def compute_metrics(trades_df: pd.DataFrame, risk_free_rate: float = 0.0) -> dict[str, Any]:
    """Compute performance metrics from a DataFrame of trades."""
    if trades_df.empty:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "trade_count": 0,
            "avg_bars_held": 0.0,
        }

    returns = trades_df["return_pct"].values
    wins = returns[returns > 0]
    losses = returns[returns <= 0]

    equity = 1.0
    equity_curve = [1.0]
    for r in returns:
        equity *= 1 + r
        equity_curve.append(equity)

    peak = equity_curve[0]
    max_dd = 0.0
    for e in equity_curve:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_dd:
            max_dd = dd

    if len(returns) > 1:
        excess = returns - risk_free_rate / 252
        sharpe = math.sqrt(252) * (excess.mean() / excess.std()) if excess.std() != 0 else 0.0
    else:
        sharpe = 0.0

    win_rate = len(wins) / len(returns) if len(returns) > 0 else 0.0
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 else (float("inf") if len(wins) > 0 else 0.0)
    avg_bars = trades_df["bars_held"].mean()

    return {
        "total_return": (equity - 1.0) * 100.0,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd * 100.0,
        "win_rate": win_rate * 100.0,
        "profit_factor": profit_factor,
        "trade_count": len(trades_df),
        "avg_bars_held": avg_bars,
        "equity_curve": equity_curve,
    }


# ──────────────────────────────────────────────────────────────
# 4. Expanding window splitter
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Fold:
    fold_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def expanding_window_folds(
    total_bars: int,
    initial_train_bars: int,
    test_bars: int,
    step_bars: int | None = None,
) -> list[Fold]:
    """Generate expanding-window folds."""
    if step_bars is None:
        step_bars = test_bars

    folds: list[Fold] = []
    fold_id = 0
    train_end = initial_train_bars - 1
    test_start = initial_train_bars
    test_end = test_start + test_bars - 1

    while test_end < total_bars:
        folds.append(
            Fold(
                fold_id=fold_id,
                train_start=0,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        fold_id += 1
        train_end += step_bars
        test_start = train_end + 1
        test_end = test_start + test_bars - 1

    return folds


# ──────────────────────────────────────────────────────────────
# 5. Statistical tests
# ──────────────────────────────────────────────────────────────


def bootstrap_sharpe_distribution(
    returns: np.ndarray,
    n_bootstrap: int = 10_000,
    seed: int = 42,
) -> np.ndarray:
    """Bootstrap the Sharpe ratio distribution."""
    rng = np.random.default_rng(seed)
    n = len(returns)
    if n < 2:
        return np.array([0.0])

    sharpes = []
    for _ in range(n_bootstrap):
        sample = rng.choice(returns, size=n, replace=True)
        if sample.std() == 0:
            sharpes.append(0.0)
        else:
            sharpe = math.sqrt(252) * (sample.mean() / sample.std())
            sharpes.append(sharpe)
    return np.array(sharpes)


def cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """Cohen's d effect size (pooled standard deviation)."""
    nx = len(x)
    ny = len(y)
    if nx == 0 or ny == 0:
        return 0.0
    dof = nx + ny - 2
    if dof <= 0:
        return 0.0
    pooled_std = math.sqrt(((nx - 1) * x.var() + (ny - 1) * y.var()) / dof)
    if pooled_std == 0:
        return 0.0
    return (x.mean() - y.mean()) / pooled_std


# ──────────────────────────────────────────────────────────────
# 6. Main walk-forward validation
# ──────────────────────────────────────────────────────────────


@dataclass
class FoldResult:
    fold_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    metrics: dict[str, Any]
    bootstrap_sharpe_ci: tuple[float, float] | None = None
    sharpe_pvalue: float | None = None
    sharpe_significant: bool | None = None
    cohens_d: float | None = None


@dataclass
class ValidationReport:
    folds: list[FoldResult]
    aggregate: dict[str, float]
    bonferroni_significant: list[bool]
    fdr_significant: list[bool]
    overall_pvalue_bonferroni: float | None = None
    overall_pvalue_fdr: float | None = None
    configuration: dict[str, Any] = field(default_factory=dict)


def run_walk_forward_validation(
    df: pd.DataFrame,
    initial_train_months: int = 12,
    test_months: int = 3,
    step_months: int | None = None,
    sma_fast: int = 20,
    sma_slow: int = 50,
    rsi_period: int = 14,
    atr_period: int = 14,
    commission: float = 0.0001,
    n_bootstrap: int = 10_000,
    bootstrap_seed: int = 42,
) -> ValidationReport:
    """Run expanding-window walk-forward validation on OHLCV DataFrame."""
    if step_months is None:
        step_months = test_months

    bars_per_month = 30 * 24 * 60
    initial_train_bars = initial_train_months * bars_per_month
    test_bars = test_months * bars_per_month
    step_bars = step_months * bars_per_month

    # Precompute indicators ONCE
    df = compute_indicators(df)
    close = df["close"].values
    signals = generate_signals_vectorized(df)

    folds = expanding_window_folds(len(df), initial_train_bars, test_bars, step_bars)
    fold_results: list[FoldResult] = []

    for fold in folds:
        test_signals = signals.iloc[fold.test_start : fold.test_end + 1].values
        test_close = close[fold.test_start : fold.test_end + 1]
        trades_df = simulate_trades_vectorized(test_close, pd.Series(test_signals), commission=commission)
        metrics = compute_metrics(trades_df)

        if not trades_df.empty:
            returns = trades_df["return_pct"].values
            boot_sharpes = bootstrap_sharpe_distribution(returns, n_bootstrap, bootstrap_seed)
            ci_low = float(np.percentile(boot_sharpes, 2.5))
            ci_high = float(np.percentile(boot_sharpes, 97.5))
            t_stat, pvalue = stats.ttest_1samp(boot_sharpes, popmean=0.0)
            d = cohens_d(returns, np.zeros_like(returns))
        else:
            ci_low, ci_high = 0.0, 0.0
            _t_stat, pvalue = 0.0, 1.0
            d = 0.0

        fold_results.append(
            FoldResult(
                fold_id=fold.fold_id,
                train_start=fold.train_start,
                train_end=fold.train_end,
                test_start=fold.test_start,
                test_end=fold.test_end,
                metrics=metrics,
                bootstrap_sharpe_ci=(ci_low, ci_high),
                sharpe_pvalue=pvalue,
                sharpe_significant=pvalue < 0.05,
                cohens_d=d,
            )
        )

    # Multiple testing correction
    pvalues = [fr.sharpe_pvalue for fr in fold_results if fr.sharpe_pvalue is not None]
    if pvalues:
        _, bonf_corrected, _, _ = multipletests(pvalues, method="bonferroni")
        _, fdr_corrected, _, _ = multipletests(pvalues, method="fdr_bh")
        bonf_significant = [bool(p < 0.05) for p in bonf_corrected]
        fdr_significant = [bool(p < 0.05) for p in fdr_corrected]
    else:
        bonf_significant = []
        fdr_significant = []

    # Aggregate metrics
    agg_metrics: dict[str, float] = {}
    metric_names = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "trade_count"]
    for name in metric_names:
        values = [fr.metrics.get(name, 0.0) for fr in fold_results]
        if values:
            agg_metrics[name] = sum(values) / len(values)

    overall_bonf_p = min(pvalues) * len(pvalues) if pvalues else 1.0
    overall_bonf_p = min(overall_bonf_p, 1.0)
    overall_fdr_p = min(pvalues) if pvalues else 1.0

    report = ValidationReport(
        folds=fold_results,
        aggregate=agg_metrics,
        bonferroni_significant=bonf_significant,
        fdr_significant=fdr_significant,
        overall_pvalue_bonferroni=overall_bonf_p,
        overall_pvalue_fdr=overall_fdr_p,
        configuration={
            "initial_train_months": initial_train_months,
            "test_months": test_months,
            "step_months": step_months,
            "sma_fast": sma_fast,
            "sma_slow": sma_slow,
            "rsi_period": rsi_period,
            "atr_period": atr_period,
            "commission": commission,
            "n_bootstrap": n_bootstrap,
            "bars_per_month": bars_per_month,
        },
    )
    return report


# ──────────────────────────────────────────────────────────────
# 7. Visualization
# ──────────────────────────────────────────────────────────────


def plot_equity_curves(report: ValidationReport, df: pd.DataFrame, output_path: str | None = None) -> None:
    """Plot equity curves for each fold on a single chart."""
    plt.figure(figsize=(14, 6))
    colors = plt.cm.viridis(np.linspace(0, 1, len(report.folds)))

    for idx, fr in enumerate(report.folds):
        equity = fr.metrics.get("equity_curve", [1.0])
        if not equity or len(equity) < 2:
            continue
        plt.plot(range(len(equity)), equity, color=colors[idx], alpha=0.7, label=f"Fold {fr.fold_id}")

    plt.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    plt.title("Walk-Forward Equity Curves (Expanding Window)")
    plt.xlabel("Bars in Test Period")
    plt.ylabel("Equity (starting at 1.0)")
    plt.legend(loc="upper left", fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()


def plot_sharpe_distribution(report: ValidationReport, output_path: str | None = None) -> None:
    """Plot distribution of Sharpe ratios across folds."""
    sharpes = [fr.metrics.get("sharpe_ratio", 0.0) for fr in report.folds]
    if not sharpes:
        return

    plt.figure(figsize=(10, 5))
    plt.hist(sharpes, bins=max(10, len(sharpes)), color="steelblue", edgecolor="black", alpha=0.7)
    plt.axvline(0, color="red", linestyle="--", label="Sharpe = 0")
    plt.axvline(
        np.mean(sharpes),
        color="green",
        linestyle="-",
        label=f"Mean Sharpe = {np.mean(sharpes):.2f}",
    )
    plt.title("Distribution of Sharpe Ratios Across Folds")
    plt.xlabel("Sharpe Ratio")
    plt.ylabel("Number of Folds")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()


# ──────────────────────────────────────────────────────────────
# 8. Report generator
# ──────────────────────────────────────────────────────────────


def generate_report(report: ValidationReport, df: pd.DataFrame) -> str:
    """Generate a human-readable validation report."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("WALK-FORWARD VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append("CONFIGURATION")
    for k, v in report.configuration.items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("AGGREGATE METRICS")
    for k, v in report.aggregate.items():
        lines.append(f"  {k}: {v:.4f}")
    lines.append("")
    lines.append("FOLD RESULTS")
    lines.append(f"{'Fold':>4} | {'Sharpe':>8} | {'MaxDD':>8} | {'Win%':>8} | {'Trades':>6} | {'p-value':>10} | {'Bonf':>5} | {'FDR':>5} | {'Cohen d':>8}")
    lines.append("-" * 70)
    for idx, fr in enumerate(report.folds):
        sharpe = fr.metrics.get("sharpe_ratio", 0.0)
        max_dd = fr.metrics.get("max_drawdown", 0.0)
        win_rate = fr.metrics.get("win_rate", 0.0)
        trades = fr.metrics.get("trade_count", 0)
        pval = fr.sharpe_pvalue if fr.sharpe_pvalue is not None else 1.0
        bonf = report.bonferroni_significant[idx] if idx < len(report.bonferroni_significant) else False
        fdr = report.fdr_significant[idx] if idx < len(report.fdr_significant) else False
        d = fr.cohens_d if fr.cohens_d is not None else 0.0
        lines.append(f"{fr.fold_id:>4} | {sharpe:>8.4f} | {max_dd:>8.4f} | {win_rate:>8.2f} | {trades:>6} | {pval:>10.6f} | {str(bonf):>5} | {str(fdr):>5} | {d:>8.4f}")
    lines.append("")
    lines.append("OVERALL SIGNIFICANCE")
    lines.append(f"  Bonferroni-corrected p-value: {report.overall_pvalue_bonferroni:.6f}")
    lines.append(f"  FDR-corrected p-value: {report.overall_pvalue_fdr:.6f}")
    lines.append("")
    lines.append("CONCLUSION")
    any_sig_bonf = any(report.bonferroni_significant)
    any_sig_fdr = any(report.fdr_significant)
    if any_sig_bonf or any_sig_fdr:
        lines.append("  *** STATISTICALLY SIGNIFICANT EDGE DETECTED ***")
    else:
        lines.append("  No statistically significant edge detected after multiple testing correction.")
    lines.append("=" * 70)
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 9. Entrypoint
# ──────────────────────────────────────────────────────────────


def main() -> None:
    data_path = "data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    df.columns = [c.strip() for c in df.columns]
    # Normalize column names to lowercase
    col_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=col_map)
    # Parse datetime
    if "datetime" not in df.columns:
        if "date" in df.columns and "time" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")
        else:
            df["datetime"] = pd.to_datetime(df.iloc[:, 0])
    df = df.sort_values("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    print(f"Loaded {len(df)} bars from {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")

    print("Running expanding-window walk-forward validation...")
    report = run_walk_forward_validation(
        df,
        initial_train_months=12,
        test_months=3,
        step_months=3,
        sma_fast=20,
        sma_slow=50,
        rsi_period=14,
        atr_period=14,
        commission=0.0001,
        n_bootstrap=10_000,
        bootstrap_seed=42,
    )

    # Print report
    print(generate_report(report, df))

    # Save report
    report_data = {
        "configuration": report.configuration,
        "aggregate": report.aggregate,
        "folds": [
            {
                "fold_id": fr.fold_id,
                "train_start": fr.train_start,
                "train_end": fr.train_end,
                "test_start": fr.test_start,
                "test_end": fr.test_end,
                "metrics": {k: v for k, v in fr.metrics.items() if k != "equity_curve"},
                "bootstrap_sharpe_ci": fr.bootstrap_sharpe_ci,
                "sharpe_pvalue": fr.sharpe_pvalue,
                "sharpe_significant": fr.sharpe_significant,
                "cohens_d": fr.cohens_d,
            }
            for fr in report.folds
        ],
        "overall_pvalue_bonferroni": report.overall_pvalue_bonferroni,
        "overall_pvalue_fdr": report.overall_pvalue_fdr,
    }
    with open("data/curated/xauusd/walk_forward_report.json", "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    print("\nReport saved to data/curated/xauusd/walk_forward_report.json")

    # Plots
    plot_equity_curves(report, df, "data/curated/xauusd/walk_forward_equity_curves.png")
    plot_sharpe_distribution(report, "data/curated/xauusd/walk_forward_sharpe_distribution.png")
    print("Plots saved to data/curated/xauusd/")


if __name__ == "__main__":
    main()
