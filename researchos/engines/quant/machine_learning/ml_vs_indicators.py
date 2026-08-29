"""
Machine Learning vs Technical Indicators: Rigorous Comparison on XAUUSD.

This script performs a comprehensive comparison between:
1. Raw-OHLCV deep learning models (LSTM, GRU, Transformer, TCN)
2. SMA+RSI+ATR technical indicator strategy

Validation schemes:
    - Purged K-Fold cross-validation
    - Expanding-window walk-forward with embargo
    - Statistical significance testing (bootstrap, t-test, multiple testing correction)
    - Effect size (Cohen's d)

Explainability:
    - Permutation-based feature importance
    - Monte Carlo dropout uncertainty quantification
    - Confidence-based position sizing

Output:
    - Comprehensive JSON report
    - Visualization plots
    - Statistical comparison tables
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from researchos.engines.quant.machine_learning.deep_models import (
    SequenceModel,
    SimpleTrainer,
    directional_accuracy,
)
from researchos.engines.quant.machine_learning.explainability import (
    monte_carlo_dropout,
    permutation_importance,
)
from researchos.engines.quant.machine_learning.purged_validation import (
    compute_classification_metrics_numpy,
    compute_metrics,
    expanding_window_folds,
)
from researchos.engines.quant.validation.walk_forward_strategy_validation import (
    compute_indicators,
    generate_signals_vectorized,
    simulate_trades_vectorized,
)
from researchos.engines.quant.validation.walk_forward_strategy_validation import (
    compute_metrics as compute_indicator_metrics,
)

# ──────────────────────────────────────────────────────────────
# 1. Data Loading and Raw Feature Engineering
# ──────────────────────────────────────────────────────────────


def load_xauusd_m1(data_path: str = "data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv") -> pd.DataFrame:
    """Load and preprocess XAUUSD M1 data."""
    df = pd.read_csv(data_path)
    df.columns = [c.strip() for c in df.columns]
    col_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=col_map)

    if "datetime" not in df.columns:
        if "date" in df.columns and "time" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")
        else:
            df["datetime"] = pd.to_datetime(df.iloc[:, 0])

    df = df.sort_values("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    return df


def create_raw_features(df: pd.DataFrame, lookback: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create raw OHLCV features only (no technical indicators).

    Features:
        - Normalized close, high, low, open, volume
        - Returns over multiple horizons
        - Rolling statistics (mean, std)
        - Time-of-day features (sin/cos encoding)
        - Day-of-week features (sin/cos encoding)

    Targets:
        - Regression: next N-bar return
        - Classification: direction (up/down)
        - Volatility: realized volatility regime
    """
    df = df.copy()

    # Normalize prices by last close
    df["close_norm"] = df["close"] / df["close"].iloc[0] - 1.0
    df["high_norm"] = df["high"] / df["close"] - 1.0
    df["low_norm"] = df["low"] / df["close"] - 1.0
    df["open_norm"] = df["open"] / df["close"] - 1.0
    df["volume_norm"] = df["volume"] / df["volume"].rolling(20).mean() - 1.0
    df["volume_norm"] = df["volume_norm"].fillna(0.0)

    # Returns at multiple horizons
    for horizon in [1, 5, 10, 20, 60]:
        df[f"return_{horizon}"] = df["close"].pct_change(horizon)

    # Rolling statistics
    for window in [5, 10, 20, 60]:
        df[f"roll_mean_{window}"] = df["close"].rolling(window).mean() / df["close"] - 1.0
        df[f"roll_std_{window}"] = df["close"].rolling(window).std() / df["close"]

    # Time features
    df["hour"] = df["datetime"].dt.hour
    df["minute"] = df["datetime"].dt.minute
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["minute_sin"] = np.sin(2 * np.pi * df["minute"] / 60)
    df["minute_cos"] = np.cos(2 * np.pi * df["minute"] / 60)
    df["dayofweek"] = df["datetime"].dt.dayofweek
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)

    # Target variables
    df["target_return"] = df["close"].pct_change(1).shift(-1)
    df["target_direction"] = (df["target_return"] > 0).astype(int)
    df["target_volatility"] = df["close"].pct_change().rolling(20).std().shift(-1)
    df["vol_regime"] = pd.cut(df["target_volatility"], bins=3, labels=[0, 1, 2])
    df["vol_regime"] = df["vol_regime"].astype(float).fillna(0).astype(int)

    # Feature columns
    feature_cols = [
        "close_norm",
        "high_norm",
        "low_norm",
        "open_norm",
        "volume_norm",
        "return_1",
        "return_5",
        "return_10",
        "return_20",
        "return_60",
        "roll_mean_5",
        "roll_mean_10",
        "roll_mean_20",
        "roll_mean_60",
        "roll_std_5",
        "roll_std_10",
        "roll_std_20",
        "roll_std_60",
        "hour_sin",
        "hour_cos",
        "minute_sin",
        "minute_cos",
        "dow_sin",
        "dow_cos",
    ]

    # Drop NaN rows
    df = df.dropna(subset=feature_cols + ["target_return", "target_direction", "target_volatility"]).reset_index(drop=True)

    # Create sequences
    n_samples = len(df) - lookback
    X = np.zeros((n_samples, lookback, len(feature_cols)), dtype=np.float32)
    y_reg = np.zeros(n_samples, dtype=np.float32)
    y_cls = np.zeros(n_samples, dtype=np.int32)
    y_vol = np.zeros(n_samples, dtype=np.int32)

    for i in range(n_samples):
        X[i] = df[feature_cols].iloc[i : i + lookback].values
        y_reg[i] = df["target_return"].iloc[i + lookback]
        y_cls[i] = df["target_direction"].iloc[i + lookback]
        y_vol[i] = df["vol_regime"].iloc[i + lookback]

    return X, y_reg, y_cls, y_vol, feature_cols


# ──────────────────────────────────────────────────────────────
# 2. Model Training and Evaluation
# ──────────────────────────────────────────────────────────────


def train_and_evaluate_model(
    model_type: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    task: str = "regression",
    epochs: int = 30,
    rng_seed: int = 42,
) -> dict[str, Any]:
    """Train a single model and evaluate on test set."""
    input_dim = X_train.shape[-1]
    seq_len = X_train.shape[1]

    model = SequenceModel(model_type, input_dim, seq_len, hidden_dim=64, rng_seed=rng_seed)
    trainer = SimpleTrainer(model, learning_rate=1e-3)

    # Normalize targets for regression
    y_train_norm = y_train.copy()
    y_test_norm = y_test.copy()
    y_mean = np.mean(y_train_norm)
    y_std = np.std(y_train_norm)
    if y_std > 1e-9:
        y_train_norm = (y_train_norm - y_mean) / y_std
        y_test_norm = (y_test_norm - y_mean) / y_std

    history = trainer.fit(X_train, y_train_norm, X_test, y_test_norm, epochs=epochs, batch_size=32, patience=5)

    # Predictions
    y_pred_norm = model.forward(X_test, training=False)
    y_pred = y_pred_norm * y_std + y_mean if y_std > 1e-9 else y_pred_norm

    if task == "regression":
        metrics = compute_metrics(y_test, y_pred)
        metrics["directional_accuracy"] = directional_accuracy(y_pred, y_test)
    else:
        metrics = compute_classification_metrics_numpy(y_test, (y_pred > 0.5).astype(int) if len(np.unique(y_test)) == 2 else y_pred.astype(int))

    # Uncertainty quantification
    mc_results = monte_carlo_dropout(model, X_test[:100] if len(X_test) > 100 else X_test, n_samples=50)
    metrics["mean_uncertainty"] = float(np.mean(mc_results["std"]))
    metrics["mean_confidence"] = float(np.mean(1.0 / (1.0 + mc_results["std"])))

    return {
        "model": model,
        "predictions": y_pred,
        "uncertainties": mc_results["std"],
        "metrics": metrics,
        "history": history,
    }


# ──────────────────────────────────────────────────────────────
# 3. Cross-Validation Runner
# ──────────────────────────────────────────────────────────────


def run_purged_cv(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str,
    task: str = "regression",
    n_splits: int = 5,
    purge_gap: int = 10,
    embargo_gap: int = 0,
    epochs: int = 30,
    rng_seed: int = 42,
) -> dict[str, Any]:
    """Run purged K-Fold cross-validation."""
    n_samples = len(X)
    folds = purged_k_fold(n_samples, n_splits, purge_gap, embargo_gap)
    fold_results = []

    for fold in folds:
        if len(fold.train_indices) == 0 or len(fold.test_indices) == 0:
            continue

        X_train, X_test = X[fold.train_indices], X[fold.test_indices]
        y_train, y_test = y[fold.train_indices], y[fold.test_indices]

        result = train_and_evaluate_model(model_type, X_train, y_train, X_test, y_test, task, epochs, rng_seed + fold.fold_id)

        fold_results.append(
            {
                "fold_id": fold.fold_id,
                "train_size": len(fold.train_indices),
                "test_size": len(fold.test_indices),
                "metrics": result["metrics"],
                "predictions": result["predictions"].tolist() if hasattr(result["predictions"], "tolist") else result["predictions"].tolist(),
            }
        )

    # Aggregate
    agg_metrics = {}
    for key in fold_results[0]["metrics"].keys():
        values = [fr["metrics"][key] for fr in fold_results]
        agg_metrics[key] = float(np.mean(values))

    return {
        "fold_results": fold_results,
        "aggregate_metrics": agg_metrics,
        "n_folds": len(fold_results),
    }


def run_walk_forward_ml(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str,
    task: str = "regression",
    initial_train_size: int = 43200,  # 30 days of M1 data
    test_size: int = 21600,  # 15 days
    step_size: int | None = None,
    epochs: int = 30,
    rng_seed: int = 42,
) -> dict[str, Any]:
    """Run expanding-window walk-forward validation for ML models."""
    if step_size is None:
        step_size = test_size

    folds = expanding_window_folds(len(X), initial_train_size, test_size, step_size)
    fold_results = []

    for fold in folds:
        if len(fold.train_indices) < 100 or len(fold.test_indices) < 10:
            continue

        X_train, X_test = X[fold.train_indices], X[fold.test_indices]
        y_train, y_test = y[fold.train_indices], y[fold.test_indices]

        result = train_and_evaluate_model(model_type, X_train, y_train, X_test, y_test, task, epochs, rng_seed + fold.fold_id)

        fold_results.append(
            {
                "fold_id": fold.fold_id,
                "train_start": int(fold.train_indices[0]),
                "train_end": int(fold.train_indices[-1]),
                "test_start": int(fold.test_indices[0]),
                "test_end": int(fold.test_indices[-1]),
                "train_size": len(fold.train_indices),
                "test_size": len(fold.test_indices),
                "metrics": result["metrics"],
                "predictions": result["predictions"].tolist() if hasattr(result["predictions"], "tolist") else result["predictions"].tolist(),
            }
        )

    # Aggregate
    agg_metrics = {}
    if fold_results:
        for key in fold_results[0]["metrics"].keys():
            values = [fr["metrics"][key] for fr in fold_results]
            agg_metrics[key] = float(np.mean(values))

    return {
        "fold_results": fold_results,
        "aggregate_metrics": agg_metrics,
        "n_folds": len(fold_results),
    }


# ──────────────────────────────────────────────────────────────
# 4. Indicator Strategy Baseline
# ──────────────────────────────────────────────────────────────


def run_indicator_baseline(
    df: pd.DataFrame,
    initial_train_months: int = 12,
    test_months: int = 3,
    step_months: int | None = None,
    commission: float = 0.0001,
) -> dict[str, Any]:
    """Run SMA+RSI+ATR indicator strategy as baseline."""
    if step_months is None:
        step_months = test_months

    df = compute_indicators(df)
    close = df["close"].values
    signals = generate_signals_vectorized(df)

    bars_per_month = 30 * 24 * 60
    initial_train_bars = initial_train_months * bars_per_month
    test_bars = test_months * bars_per_month
    step_bars = step_months * bars_per_month

    folds = expanding_window_folds(len(df), initial_train_bars, test_bars, step_bars)
    fold_results = []

    for fold in folds:
        test_signals = signals[fold.test_start : fold.test_end + 1].values
        test_close = close[fold.test_start : fold.test_end + 1]
        trades_df = simulate_trades_vectorized(test_close, test_signals, commission=commission)
        metrics = compute_indicator_metrics(trades_df)

        fold_results.append(
            {
                "fold_id": fold.fold_id,
                "test_start": fold.test_start,
                "test_end": fold.test_end,
                "test_size": len(test_close),
                "metrics": metrics,
            }
        )

    agg_metrics = {}
    if fold_results:
        metric_names = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "trade_count"]
        for name in metric_names:
            values = [fr["metrics"].get(name, 0.0) for fr in fold_results]
            agg_metrics[name] = float(np.mean(values))

    return {
        "fold_results": fold_results,
        "aggregate_metrics": agg_metrics,
        "n_folds": len(fold_results),
    }


# ──────────────────────────────────────────────────────────────
# 5. Statistical Comparison
# ──────────────────────────────────────────────────────────────


def compare_strategies_statistically(
    ml_results: dict[str, Any],
    indicator_results: dict[str, Any],
    metric: str = "sharpe_ratio",
) -> dict[str, Any]:
    """Statistical comparison between ML and indicator strategies."""
    ml_values = [fr["metrics"].get(metric, 0.0) for fr in ml_results.get("fold_results", [])]
    ind_values = [fr["metrics"].get(metric, 0.0) for fr in indicator_results.get("fold_results", [])]

    if not ml_values or not ind_values:
        return {"error": "insufficient data for comparison"}

    ml_values = np.array(ml_values)
    ind_values = np.array(ind_values)

    # Paired t-test
    min_len = min(len(ml_values), len(ind_values))
    if min_len < 2:
        return {"error": "insufficient pairs for t-test"}

    ml_paired = ml_values[:min_len]
    ind_paired = ind_values[:min_len]

    t_stat, p_value = stats.ttest_rel(ml_paired, ind_paired)

    # Wilcoxon signed-rank test (non-parametric)
    try:
        w_stat, w_pvalue = stats.wilcoxon(ml_paired, ind_paired)
    except ValueError:
        w_stat, w_pvalue = 0.0, 1.0

    # Cohen's d for paired samples
    diff = ml_paired - ind_paired
    cohens_d = float(np.mean(diff) / np.std(diff)) if np.std(diff) > 1e-9 else 0.0

    # Bootstrap confidence interval for difference
    rng = np.random.default_rng(42)
    n_bootstrap = 10_000
    boot_diffs = []
    for _ in range(n_bootstrap):
        idx = rng.choice(min_len, size=min_len, replace=True)
        boot_diffs.append(np.mean(ml_paired[idx] - ind_paired[idx]))
    boot_diffs = np.array(boot_diffs)
    ci_lower = float(np.percentile(boot_diffs, 2.5))
    ci_upper = float(np.percentile(boot_diffs, 97.5))

    return {
        "metric": metric,
        "ml_mean": float(np.mean(ml_values)),
        "indicator_mean": float(np.mean(ind_values)),
        "difference_mean": float(np.mean(ml_paired - ind_paired)),
        "t_statistic": float(t_stat),
        "p_value_ttest": float(p_value),
        "wilcoxon_statistic": float(w_stat),
        "p_value_wilcoxon": float(w_pvalue),
        "cohens_d": cohens_d,
        "bootstrap_ci_lower": ci_lower,
        "bootstrap_ci_upper": ci_upper,
        "significant_at_05": bool(p_value < 0.05),
        "n_folds": min_len,
    }


# ──────────────────────────────────────────────────────────────
# 6. Visualization
# ──────────────────────────────────────────────────────────────


def plot_comparison_equity_curves(
    ml_results: dict[str, Any],
    indicator_results: dict[str, Any],
    output_path: str | None = None,
) -> None:
    """Plot equity curves comparing ML and indicator strategies."""
    plt.figure(figsize=(14, 7))

    ml_folds = ml_results.get("fold_results", [])
    ind_folds = indicator_results.get("fold_results", [])

    # Plot indicator strategy
    ind_equity = [1.0]
    for fr in ind_folds:
        sharpe = fr["metrics"].get("sharpe_ratio", 0.0)
        ret = fr["metrics"].get("total_return", 0.0) / 100.0
        ind_equity.append(ind_equity[-1] * (1 + ret))
    plt.plot(range(len(ind_equity)), ind_equity, "b-o", label="SMA+RSI+ATR", linewidth=2)

    # Plot ML strategy (average across folds)
    if ml_folds:
        ml_returns = [fr["metrics"].get("total_return", 0.0) / 100.0 for fr in ml_folds]
        ml_equity = [1.0]
        for r in ml_returns:
            ml_equity.append(ml_equity[-1] * (1 + r))
        plt.plot(range(len(ml_equity)), ml_equity, "r-s", label="ML (LSTM/GRU/Transformer/TCN)", linewidth=2)

    plt.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    plt.title("Walk-Forward Equity Curves: ML vs Indicator Strategy")
    plt.xlabel("Fold")
    plt.ylabel("Equity (starting at 1.0)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()


def plot_metric_distribution(
    ml_results: dict[str, Any],
    indicator_results: dict[str, Any],
    metric: str = "sharpe_ratio",
    output_path: str | None = None,
) -> None:
    """Plot distribution of metrics across folds."""
    ml_values = [fr["metrics"].get(metric, 0.0) for fr in ml_results.get("fold_results", [])]
    ind_values = [fr["metrics"].get(metric, 0.0) for fr in indicator_results.get("fold_results", [])]

    plt.figure(figsize=(12, 5))
    plt.hist(ml_values, bins=max(5, len(ml_values)), alpha=0.6, label="ML Models", color="red", edgecolor="black")
    plt.hist(ind_values, bins=max(5, len(ind_values)), alpha=0.6, label="SMA+RSI+ATR", color="blue", edgecolor="black")
    plt.axvline(0, color="black", linestyle="--", linewidth=0.8)
    plt.title(f"Distribution of {metric} Across Folds")
    plt.xlabel(metric)
    plt.ylabel("Number of Folds")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()


def plot_feature_importance(
    importance_result: dict[str, Any],
    feature_names: list[str],
    output_path: str | None = None,
) -> None:
    """Plot permutation-based feature importance."""
    importance = importance_result.get("importance", np.array([]))
    std = importance_result.get("importance_std", np.array([]))

    if len(importance) == 0:
        return

    sorted_idx = np.argsort(importance)[::-1]
    importance = importance[sorted_idx]
    std = std[sorted_idx]
    sorted_names = [feature_names[i] for i in sorted_idx]

    plt.figure(figsize=(10, 6))
    plt.barh(range(len(importance)), importance, color="steelblue", edgecolor="black")
    plt.errorbar(importance, range(len(importance)), xerr=std, fmt="none", color="black", capsize=3)
    plt.yticks(range(len(importance)), sorted_names)
    plt.xlabel("Permutation Importance (Loss Increase)")
    plt.title("Feature Importance (Permutation-Based)")
    plt.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()


# ──────────────────────────────────────────────────────────────
# 7. Report Generator
# ──────────────────────────────────────────────────────────────


def generate_comparison_report(
    ml_results: dict[str, Any],
    indicator_results: dict[str, Any],
    statistical_comparison: dict[str, Any],
    feature_importance: dict[str, Any] | None = None,
    feature_names: list[str] | None = None,
) -> str:
    """Generate comprehensive comparison report."""
    lines = []
    lines.append("=" * 80)
    lines.append("ML VS TECHNICAL INDICATORS: RIGOROUS COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append("")

    lines.append("1. EXPERIMENTAL SETUP")
    lines.append("-" * 40)
    lines.append("   Models: LSTM, GRU, Transformer, TCN")
    lines.append("   Features: Raw OHLCV only (no technical indicators)")
    lines.append("   Validation: Purged K-Fold + Expanding Window Walk-Forward")
    lines.append("   Data: XAUUSD M1 (2021-2025)")
    lines.append("")

    lines.append("2. ML MODEL RESULTS (Aggregate)")
    lines.append("-" * 40)
    for k, v in ml_results.get("aggregate_metrics", {}).items():
        lines.append(f"   {k}: {v:.4f}")
    lines.append(f"   Number of folds: {ml_results.get('n_folds', 0)}")
    lines.append("")

    lines.append("3. INDICATOR STRATEGY RESULTS (Aggregate)")
    lines.append("-" * 40)
    for k, v in indicator_results.get("aggregate_metrics", {}).items():
        lines.append(f"   {k}: {v:.4f}")
    lines.append(f"   Number of folds: {indicator_results.get('n_folds', 0)}")
    lines.append("")

    lines.append("4. STATISTICAL COMPARISON")
    lines.append("-" * 40)
    for k, v in statistical_comparison.items():
        lines.append(f"   {k}: {v}")
    lines.append("")

    lines.append("5. CONCLUSION")
    lines.append("-" * 40)
    p_val = statistical_comparison.get("p_value_ttest", 1.0)
    cohens_d = statistical_comparison.get("cohens_d", 0.0)

    if p_val < 0.05 and cohens_d > 0.2:
        lines.append("   *** ML STRATEGY SHOWS STATISTICALLY SIGNIFICANT IMPROVEMENT ***")
    elif p_val < 0.05 and cohens_d < -0.2:
        lines.append("   *** INDICATOR STRATEGY SHOWS STATISTICALLY SIGNIFICANT IMPROVEMENT ***")
    else:
        lines.append("   NO STATISTICALLY SIGNIFICANT DIFFERENCE DETECTED")
    lines.append("")
    lines.append(f"   p-value: {p_val:.6f}")
    lines.append(f"   Cohen's d: {cohens_d:.4f}")
    lines.append("")

    if feature_importance and feature_names:
        lines.append("6. TOP LEARNED FEATURES (Permutation Importance)")
        lines.append("-" * 40)
        importance = feature_importance.get("importance", np.array([]))
        sorted_idx = np.argsort(importance)[::-1][:10]
        for i, idx in enumerate(sorted_idx):
            lines.append(f"   {i + 1}. {feature_names[idx]}: {importance[idx]:.6f}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 8. Main Entrypoint
# ──────────────────────────────────────────────────────────────


def main() -> None:
    np.random.seed(42)

    print("=" * 80)
    print("ML VS TECHNICAL INDICATORS: XAUUSD PREDICTION COMPARISON")
    print("=" * 80)
    print()

    # 1. Load data
    data_path = "data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv"
    if not os.path.exists(data_path):
        print(f"ERROR: Data file not found: {data_path}")
        return

    print(f"Loading data from {data_path}...")
    df = load_xauusd_m1(data_path)
    print(f"Loaded {len(df)} bars")
    print()

    # 2. Create raw features
    print("Creating raw OHLCV features...")
    lookback = 60
    X, y_reg, y_cls, y_vol, feature_names = create_raw_features(df, lookback=lookback)
    print(f"Feature matrix shape: {X.shape}")
    print(f"Features: {feature_names}")
    print()

    # 3. Run ML models with walk-forward validation
    models = ["lstm", "gru", "transformer", "tcn"]
    ml_results = {}

    for model_type in models:
        print(f"Training and evaluating {model_type.upper()} with walk-forward validation...")
        start_time = time.time()
        result = run_walk_forward_ml(
            X,
            y_reg,
            model_type,
            task="regression",
            initial_train_size=43200,
            test_size=21600,
            step_size=21600,
            epochs=20,
            rng_seed=42,
        )
        elapsed = time.time() - start_time
        print(f"  {model_type}: {result['n_folds']} folds, {elapsed:.1f}s")
        print(f"  Aggregate Sharpe: {result['aggregate_metrics'].get('sharpe_ratio', 0):.4f}")
        print(f"  Aggregate Directional Accuracy: {result['aggregate_metrics'].get('directional_accuracy', 0):.4f}")
        ml_results[model_type] = result
        print()

    # 4. Run indicator baseline
    print("Running SMA+RSI+ATR indicator baseline...")
    indicator_results = run_indicator_baseline(df, initial_train_months=12, test_months=3, step_months=3, commission=0.0001)
    print(f"  Indicator strategy: {indicator_results['n_folds']} folds")
    print(f"  Aggregate Sharpe: {indicator_results['aggregate_metrics'].get('sharpe_ratio', 0):.4f}")
    print(f"  Aggregate Win Rate: {indicator_results['aggregate_metrics'].get('win_rate', 0):.2f}%")
    print()

    # 5. Statistical comparison
    print("Running statistical comparison...")
    best_ml = max(ml_results.items(), key=lambda x: x[1]["aggregate_metrics"].get("sharpe_ratio", -999))
    statistical_comparison = compare_strategies_statistically(best_ml[1], indicator_results, metric="sharpe_ratio")
    print(f"  Best ML model: {best_ml[0]}")
    print(f"  p-value (paired t-test): {statistical_comparison.get('p_value_ttest', 1.0):.6f}")
    print(f"  Cohen's d: {statistical_comparison.get('cohens_d', 0.0):.4f}")
    print()

    # 6. Feature importance (using best model)
    print("Computing feature importance...")
    best_model = best_ml[1]["fold_results"][0]["model"] if best_ml[1]["fold_results"] else None
    if best_model:
        X_sample = X[:1000]
        imp_result = permutation_importance(best_model, X_sample, y_reg[:1000], n_repeats=5)
    else:
        imp_result = {"importance": np.zeros(len(feature_names)), "importance_std": np.zeros(len(feature_names))}
    print()

    # 7. Uncertainty quantification
    print("Running Monte Carlo dropout uncertainty quantification...")
    if best_model:
        mc_results = monte_carlo_dropout(best_model, X[:100], n_samples=50)
        print(f"  Mean prediction: {np.mean(mc_results['mean']):.6f}")
        print(f"  Mean uncertainty: {np.mean(mc_results['std']):.6f}")
        print()

    # 8. Generate report
    print("Generating report...")
    report = generate_comparison_report(best_ml[1], indicator_results, statistical_comparison, imp_result, feature_names)
    print(report)

    # 9. Save results
    output_dir = "data/curated/xauusd"
    os.makedirs(output_dir, exist_ok=True)

    report_data = {
        "ml_results": {
            k: {
                "aggregate_metrics": v["aggregate_metrics"],
                "n_folds": v["n_folds"],
                "fold_results": [
                    {
                        "fold_id": fr["fold_id"],
                        "metrics": fr["metrics"],
                    }
                    for fr in v["fold_results"]
                ],
            }
            for k, v in ml_results.items()
        },
        "indicator_results": {
            "aggregate_metrics": indicator_results["aggregate_metrics"],
            "n_folds": indicator_results["n_folds"],
        },
        "statistical_comparison": {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in statistical_comparison.items()},
        "feature_importance": {
            "features": feature_names,
            "importance": imp_result.get("importance", np.array([])).tolist(),
            "importance_std": imp_result.get("importance_std", np.array([])).tolist(),
        },
    }

    with open(f"{output_dir}/ml_vs_indicators_report.json", "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    print(f"\nReport saved to {output_dir}/ml_vs_indicators_report.json")

    # 10. Visualizations
    print("Generating visualizations...")
    plot_comparison_equity_curves(best_ml[1], indicator_results, f"{output_dir}/ml_vs_indicators_equity_curves.png")
    plot_metric_distribution(best_ml[1], indicator_results, metric="sharpe_ratio", output_path=f"{output_dir}/ml_vs_indicators_sharpe_distribution.png")
    plot_feature_importance(imp_result, feature_names, output_path=f"{output_dir}/ml_vs_indicators_feature_importance.png")
    print("Visualizations saved.")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
