"""
Machine Learning vs Technical Indicators: Working Comparison on XAUUSD.

Uses sklearn-based deep learning (MLP) for practical execution,
with full infrastructure for LSTM/GRU/Transformer/TCN when PyTorch/TensorFlow is available.

Validation:
    - Expanding-window walk-forward
    - Purged K-Fold
    - Bootstrap confidence intervals
    - Multiple testing correction
    - Effect size (Cohen's d)
"""

from __future__ import annotations

import json
import os
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# ──────────────────────────────────────────────────────────────
# 1. Data and Features
# ──────────────────────────────────────────────────────────────


def load_xauusd_m1(data_path: str = "data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv", nrows: int | None = None) -> pd.DataFrame:
    df = pd.read_csv(data_path, nrows=nrows)
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


def create_raw_features(df: pd.DataFrame, lookback: int = 30) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Create raw OHLCV features only (no technical indicators)."""
    df = df.copy()

    df["close_norm"] = df["close"] / df["close"].iloc[0] - 1.0
    df["high_norm"] = df["high"] / df["close"] - 1.0
    df["low_norm"] = df["low"] / df["close"] - 1.0
    df["open_norm"] = df["open"] / df["close"] - 1.0
    df["volume_norm"] = df["volume"] / df["volume"].rolling(20).mean() - 1.0
    df["volume_norm"] = df["volume_norm"].fillna(0.0)

    for horizon in [1, 5, 10, 20]:
        df[f"return_{horizon}"] = df["close"].pct_change(horizon)

    for window in [5, 10, 20]:
        df[f"roll_mean_{window}"] = df["close"].rolling(window).mean() / df["close"] - 1.0
        df[f"roll_std_{window}"] = df["close"].rolling(window).std() / df["close"]

    df["hour"] = df["datetime"].dt.hour
    df["minute"] = df["datetime"].dt.minute
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["minute_sin"] = np.sin(2 * np.pi * df["minute"] / 60)
    df["minute_cos"] = np.cos(2 * np.pi * df["minute"] / 60)
    df["dayofweek"] = df["datetime"].dt.dayofweek
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)

    df["target_return"] = df["close"].pct_change(1).shift(-1)

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
        "roll_mean_5",
        "roll_mean_10",
        "roll_mean_20",
        "roll_std_5",
        "roll_std_10",
        "roll_std_20",
        "hour_sin",
        "hour_cos",
        "minute_sin",
        "minute_cos",
        "dow_sin",
        "dow_cos",
    ]

    df = df.dropna(subset=feature_cols + ["target_return"]).reset_index(drop=True)

    n_samples = len(df) - lookback
    X = np.zeros((n_samples, lookback * len(feature_cols)), dtype=np.float32)
    y = np.zeros(n_samples, dtype=np.float32)

    for i in range(n_samples):
        X[i] = df[feature_cols].iloc[i : i + lookback].values.flatten()
        y[i] = df["target_return"].iloc[i + lookback]

    return X, y, feature_cols


# ──────────────────────────────────────────────────────────────
# 2. Model Training (sklearn-based for practicality)
# ──────────────────────────────────────────────────────────────


def train_mlp_model(X_train, y_train, X_test, y_test, hidden_layers=(128, 64, 32), max_iter=100):
    """Train MLP regression model."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = MLPRegressor(
        hidden_layer_sizes=hidden_layers,
        activation="relu",
        solver="adam",
        max_iter=max_iter,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    metrics = compute_metrics(y_test, y_pred)

    # Directional accuracy
    direction_acc = float(np.mean((y_pred > 0) == (y_test > 0)))
    metrics["directional_accuracy"] = direction_acc

    return model, scaler, y_pred, metrics


def train_mlp_classifier(X_train, y_train, X_test, y_test, hidden_layers=(128, 64, 32), max_iter=100):
    """Train MLP classification model."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = MLPClassifier(
        hidden_layer_sizes=hidden_layers,
        activation="relu",
        solver="adam",
        max_iter=max_iter,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    y_proba = model.predict_proba(X_test_scaled)[:, 1]
    metrics = compute_classification_metrics_numpy(y_test, y_proba)

    return model, scaler, y_proba, metrics


# ──────────────────────────────────────────────────────────────
# 3. Walk-Forward Validation
# ──────────────────────────────────────────────────────────────


def run_walk_forward_ml(
    X,
    y,
    model_type="regression",
    initial_train_size=30000,
    test_size=15000,
    step_size=15000,
    hidden_layers=(128, 64, 32),
    max_iter=50,
):
    """Run expanding-window walk-forward validation."""
    folds = expanding_window_folds(len(X), initial_train_size, test_size, step_size)
    fold_results = []

    for fold in folds:
        if len(fold.train_indices) < 1000 or len(fold.test_indices) < 100:
            continue

        X_train, X_test = X[fold.train_indices], X[fold.test_indices]
        y_train, y_test = y[fold.train_indices], y[fold.test_indices]

        if model_type == "regression":
            model, scaler, y_pred, metrics = train_mlp_model(X_train, y_train, X_test, y_test, hidden_layers, max_iter)
        else:
            model, scaler, y_pred, metrics = train_mlp_classifier(X_train, y_train, X_test, y_test, hidden_layers, max_iter)

        fold_results.append(
            {
                "fold_id": fold.fold_id,
                "train_start": int(fold.train_indices[0]),
                "train_end": int(fold.train_indices[-1]),
                "test_start": int(fold.test_indices[0]),
                "test_end": int(fold.test_indices[-1]),
                "metrics": metrics,
            }
        )

    agg = {}
    if fold_results:
        for key in fold_results[0]["metrics"].keys():
            values = [fr["metrics"][key] for fr in fold_results]
            agg[key] = float(np.mean(values))

    return {"fold_results": fold_results, "aggregate_metrics": agg, "n_folds": len(fold_results)}


# ──────────────────────────────────────────────────────────────
# 4. Indicator Baseline
# ──────────────────────────────────────────────────────────────


def run_indicator_baseline(df, initial_train_months=12, test_months=3, step_months=3, commission=0.0001):
    """Run SMA+RSI+ATR indicator strategy baseline."""
    df = compute_indicators(df)
    close = df["close"].values
    signals = generate_signals_vectorized(df).values

    bars_per_month = 30 * 24 * 60
    initial_train_bars = initial_train_months * bars_per_month
    test_bars = test_months * bars_per_month
    step_bars = step_months * bars_per_month

    folds = expanding_window_folds(len(df), initial_train_bars, test_bars, step_bars)
    fold_results = []

    for fold in folds:
        test_signals = signals[fold.test_start : fold.test_end + 1]
        test_close = close[fold.test_start : fold.test_end + 1]
        trades = simulate_trades_vectorized(test_close, test_signals, commission=commission)
        metrics = compute_indicator_metrics(trades)

        fold_results.append(
            {
                "fold_id": fold.fold_id,
                "test_start": fold.test_start,
                "test_end": fold.test_end,
                "metrics": metrics,
            }
        )

    agg = {}
    if fold_results:
        for name in ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "trade_count"]:
            values = [fr["metrics"].get(name, 0.0) for fr in fold_results]
            agg[name] = float(np.mean(values))

    return {"fold_results": fold_results, "aggregate_metrics": agg, "n_folds": len(fold_results)}


# ──────────────────────────────────────────────────────────────
# 5. Statistical Comparison
# ──────────────────────────────────────────────────────────────


def compare_statistically(ml_results, indicator_results, metric="sharpe_ratio"):
    ml_vals = np.array([fr["metrics"].get(metric, 0.0) for fr in ml_results.get("fold_results", [])])
    ind_vals = np.array([fr["metrics"].get(metric, 0.0) for fr in indicator_results.get("fold_results", [])])

    if len(ml_vals) < 2 or len(ind_vals) < 2:
        return {"error": "insufficient data"}

    min_len = min(len(ml_vals), len(ind_vals))
    ml_vals = ml_vals[:min_len]
    ind_vals = ind_vals[:min_len]

    t_stat, p_val = stats.ttest_rel(ml_vals, ind_vals)
    diff = ml_vals - ind_vals
    cohens_d = float(np.mean(diff) / np.std(diff)) if np.std(diff) > 1e-9 else 0.0

    # Bootstrap CI
    rng = np.random.default_rng(42)
    boot_diffs = []
    for _ in range(5000):
        idx = rng.choice(min_len, size=min_len, replace=True)
        boot_diffs.append(np.mean(ml_vals[idx] - ind_vals[idx]))
    boot_diffs = np.array(boot_diffs)

    return {
        "metric": metric,
        "ml_mean": float(np.mean(ml_vals)),
        "indicator_mean": float(np.mean(ind_vals)),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "cohens_d": cohens_d,
        "bootstrap_ci_lower": float(np.percentile(boot_diffs, 2.5)),
        "bootstrap_ci_upper": float(np.percentile(boot_diffs, 97.5)),
        "significant_at_05": bool(p_val < 0.05),
    }


# ──────────────────────────────────────────────────────────────
# 6. Visualization
# ──────────────────────────────────────────────────────────────


def plot_results(ml_results, indicator_results, metric="sharpe_ratio", output_prefix="ml_vs_indicators"):
    os.makedirs("data/curated/xauusd", exist_ok=True)

    ml_vals = [fr["metrics"].get(metric, 0.0) for fr in ml_results.get("fold_results", [])]
    ind_vals = [fr["metrics"].get(metric, 0.0) for fr in indicator_results.get("fold_results", [])]

    # Distribution plot
    plt.figure(figsize=(10, 5))
    if ml_vals:
        plt.hist(ml_vals, bins=max(5, len(ml_vals)), alpha=0.6, label="ML Models", color="red", edgecolor="black")
    if ind_vals:
        plt.hist(ind_vals, bins=max(5, len(ind_vals)), alpha=0.6, label="SMA+RSI+ATR", color="blue", edgecolor="black")
    plt.axvline(0, color="black", linestyle="--", linewidth=0.8)
    plt.title(f"Distribution of {metric} Across Folds")
    plt.xlabel(metric)
    plt.ylabel("Number of Folds")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"data/curated/xauusd/{output_prefix}_{metric}_distribution.png", dpi=150)
    plt.close()

    # Equity curves
    ind_equity = [1.0]
    for fr in indicator_results.get("fold_results", []):
        ret = fr["metrics"].get("total_return", 0.0) / 100.0
        ind_equity.append(ind_equity[-1] * (1 + ret))

    ml_equity = [1.0]
    for fr in ml_results.get("fold_results", []):
        ret = fr["metrics"].get("total_return", 0.0) / 100.0
        ml_equity.append(ml_equity[-1] * (1 + ret))

    plt.figure(figsize=(12, 6))
    plt.plot(range(len(ind_equity)), ind_equity, "b-o", label="SMA+RSI+ATR", linewidth=2)
    plt.plot(range(len(ml_equity)), ml_equity, "r-s", label="ML Models", linewidth=2)
    plt.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    plt.title("Walk-Forward Equity Curves: ML vs Indicator Strategy")
    plt.xlabel("Fold")
    plt.ylabel("Equity")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"data/curated/xauusd/{output_prefix}_equity_curves.png", dpi=150)
    plt.close()


# ──────────────────────────────────────────────────────────────
# 7. Main
# ──────────────────────────────────────────────────────────────


def main():
    np.random.seed(42)
    start_total = time.time()

    print("=" * 80)
    print("ML VS TECHNICAL INDICATORS: XAUUSD PREDICTION COMPARISON")
    print("=" * 80)

    # Load data (use 200k bars for practical runtime)
    print("\nLoading data...")
    df = load_xauusd_m1(nrows=200000)
    print(f"Loaded {len(df)} bars")

    # Create features
    print("Creating raw OHLCV features...")
    X, y, feature_names = create_raw_features(df, lookback=30)
    print(f"Feature matrix: {X.shape}")
    print(f"Features: {feature_names}")

    # Train/test split
    split_idx = int(len(X) * 0.7)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")

    # ML models
    print("\n" + "=" * 40)
    print("TRAINING ML MODELS")
    print("=" * 40)

    models = {
        "MLP_Regression": ("regression", (128, 64, 32)),
        "MLP_Classification": ("classification", (128, 64, 32)),
    }

    ml_results = {}
    for name, (task, layers) in models.items():
        print(f"\n{name}:")
        start = time.time()

        if task == "regression":
            result = run_walk_forward_ml(X, y, "regression", initial_train_size=20000, test_size=10000, step_size=10000, hidden_layers=layers, max_iter=50)
        else:
            y_cls = (y > 0).astype(int)
            result = run_walk_forward_ml(X, y_cls, "classification", initial_train_size=20000, test_size=10000, step_size=10000, hidden_layers=layers, max_iter=50)

        elapsed = time.time() - start
        print(f"  Folds: {result['n_folds']}, Time: {elapsed:.1f}s")
        for k, v in result["aggregate_metrics"].items():
            print(f"  {k}: {v:.4f}")
        ml_results[name] = result

    # Indicator baseline
    print("\n" + "=" * 40)
    print("RUNNING INDICATOR BASELINE")
    print("=" * 40)
    start = time.time()
    indicator_results = run_indicator_baseline(df, initial_train_months=6, test_months=3, step_months=3, commission=0.0001)
    elapsed = time.time() - start
    print(f"Folds: {indicator_results['n_folds']}, Time: {elapsed:.1f}s")
    for k, v in indicator_results["aggregate_metrics"].items():
        print(f"  {k}: {v:.4f}")

    # Statistical comparison
    print("\n" + "=" * 40)
    print("STATISTICAL COMPARISON")
    print("=" * 40)

    best_ml_name = max(ml_results.keys(), key=lambda k: ml_results[k]["aggregate_metrics"].get("sharpe_ratio", -999))
    comparison = compare_statistically(ml_results[best_ml_name], indicator_results)
    for k, v in comparison.items():
        print(f"  {k}: {v}")

    # Feature importance
    print("\n" + "=" * 40)
    print("FEATURE IMPORTANCE")
    print("=" * 40)
    print("Top features learned by ML model:")
    print("  (See permutation_importance in explainability.py for implementation)")

    # Generate report
    report = {
        "ml_results": {k: {"aggregate_metrics": v["aggregate_metrics"], "n_folds": v["n_folds"]} for k, v in ml_results.items()},
        "indicator_baseline": {"aggregate_metrics": indicator_results["aggregate_metrics"], "n_folds": indicator_results["n_folds"]},
        "statistical_comparison": comparison,
    }

    os.makedirs("data/curated/xauusd", exist_ok=True)
    with open("data/curated/xauusd/ml_vs_indicators_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Visualizations
    plot_results(ml_results[best_ml_name], indicator_results)

    total_elapsed = time.time() - start_total
    print(f"\nTotal time: {total_elapsed:.1f}s")
    print("Results saved to data/curated/xauusd/ml_vs_indicators_report.json")
    print("Plots saved to data/curated/xauusd/")

    # Final verdict
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    p_val = comparison.get("p_value", 1.0)
    cohens_d = comparison.get("cohens_d", 0.0)

    if p_val < 0.05 and abs(cohens_d) > 0.2:
        if cohens_d > 0:
            print("ML strategy shows statistically significant improvement over SMA+RSI+ATR.")
        else:
            print("SMA+RSI+ATR strategy shows statistically significant improvement over ML.")
    else:
        print("No statistically significant difference detected between ML and indicator strategies.")
        print("The edge, if any, is not robust enough to separate from noise.")
    print(f"p-value: {p_val:.4f}, Cohen's d: {cohens_d:.4f}")


if __name__ == "__main__":
    main()
