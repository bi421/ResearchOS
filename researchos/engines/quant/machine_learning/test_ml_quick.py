"""
Quick validation test for ML vs Indicators comparison.

Uses a smaller dataset and reduced parameters to verify the pipeline works.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    compute_metrics,
)
from researchos.engines.quant.validation.walk_forward_strategy_validation import (
    compute_indicators,
    generate_signals_vectorized,
    simulate_trades_vectorized,
)


def load_sample_data(n_bars: int = 100000) -> pd.DataFrame:
    """Load a sample of XAUUSD data for quick testing."""
    data_path = "data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv"
    df = pd.read_csv(data_path, nrows=n_bars)
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
    """Create raw OHLCV features only."""
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
    X = np.zeros((n_samples, lookback, len(feature_cols)), dtype=np.float32)
    y = np.zeros(n_samples, dtype=np.float32)

    for i in range(n_samples):
        X[i] = df[feature_cols].iloc[i : i + lookback].values
        y[i] = df["target_return"].iloc[i + lookback]

    return X, y, feature_cols


def train_and_evaluate(model_type, X_train, y_train, X_test, y_test, epochs=10):
    """Train and evaluate a model."""
    input_dim = X_train.shape[-1]
    seq_len = X_train.shape[1]

    model = SequenceModel(model_type, input_dim, seq_len, hidden_dim=32, rng_seed=42)
    trainer = SimpleTrainer(model, learning_rate=1e-3)

    y_mean = np.mean(y_train)
    y_std = np.std(y_train)
    if y_std > 1e-9:
        y_train_norm = (y_train - y_mean) / y_std
        y_test_norm = (y_test - y_mean) / y_std
    else:
        y_train_norm = y_train
        y_test_norm = y_test

    history = trainer.fit(X_train, y_train_norm, X_test, y_test_norm, epochs=epochs, batch_size=64, patience=3)

    y_pred_norm = model.forward(X_test, training=False)
    y_pred = y_pred_norm * y_std + y_mean if y_std > 1e-9 else y_pred_norm

    metrics = compute_metrics(y_test, y_pred)
    metrics["directional_accuracy"] = directional_accuracy(y_pred, y_test)

    return model, y_pred, metrics


def main():
    np.random.seed(42)

    print("Loading sample data (100k bars)...")
    df = load_sample_data(100000)
    print(f"Loaded {len(df)} bars")

    print("Creating raw features...")
    X, y, feature_names = create_raw_features(df, lookback=30)
    print(f"Feature matrix shape: {X.shape}")

    # Use last 20% as final test
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")

    models = ["lstm", "gru", "transformer", "tcn"]
    results = {}

    for model_type in models:
        print(f"\nTraining {model_type.upper()}...")
        start = time.time()
        model, y_pred, metrics = train_and_evaluate(model_type, X_train, y_train, X_test, y_test, epochs=10)
        elapsed = time.time() - start
        print(f"  Time: {elapsed:.1f}s")
        print(f"  MSE: {metrics['mse']:.8f}")
        print(f"  Directional Accuracy: {metrics['directional_accuracy']:.4f}")
        print(f"  Sharpe: {metrics['sharpe_ratio']:.4f}")

        # Uncertainty
        mc = monte_carlo_dropout(model, X_test[:200], n_samples=20)
        print(f"  Mean Uncertainty: {np.mean(mc['std']):.8f}")

        results[model_type] = {"model": model, "predictions": y_pred, "metrics": metrics}

    # Indicator baseline on test period
    print("\nRunning indicator baseline on test period...")
    test_df = df.iloc[split_idx + 30 :].reset_index(drop=True)
    test_df = compute_indicators(test_df)
    close = test_df["close"].values
    signals = generate_signals_vectorized(test_df).values
    trades = simulate_trades_vectorized(close, signals, commission=0.0001)
    ind_metrics = compute_indicator_metrics(trades)
    print(f"  Trades: {ind_metrics['trade_count']}")
    print(f"  Win Rate: {ind_metrics['win_rate']:.2f}%")
    print(f"  Sharpe: {ind_metrics['sharpe_ratio']:.4f}")
    print(f"  Total Return: {ind_metrics['total_return']:.2f}%")

    # Statistical comparison
    print("\nStatistical comparison (ML vs Indicator):")
    ml_sharpes = [results[m]["metrics"]["sharpe_ratio"] for m in models]
    ind_sharpe = ind_metrics["sharpe_ratio"]
    ml_mean = np.mean(ml_sharpes)
    print(f"  ML mean Sharpe: {ml_mean:.4f}")
    print(f"  Indicator Sharpe: {ind_sharpe:.4f}")

    t_stat, p_val = stats.ttest_rel(np.array(ml_sharpes), np.array([ind_sharpe] * len(ml_sharpes)))
    print(f"  t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

    # Feature importance (best model)
    best_model_name = max(results.items(), key=lambda x: x[1]["metrics"].sharpe_ratio)[0]
    best_model = results[best_model_name]["model"]
    print(f"\nFeature importance ({best_model_name}):")
    imp = permutation_importance(best_model, X_test[:500], y_test[:500], n_repeats=3)
    sorted_idx = np.argsort(imp["importance"])[::-1][:10]
    for i, idx in enumerate(sorted_idx):
        print(f"  {i + 1}. {feature_names[idx]}: {imp['importance'][idx]:.6f}")

    # Save results
    output = {
        "models": {m: {"metrics": {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in r["metrics"].items()}} for m, r in results.items()},
        "indicator_baseline": {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in ind_metrics.items()},
        "statistical_comparison": {
            "ml_mean_sharpe": float(ml_mean),
            "indicator_sharpe": float(ind_sharpe),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
        },
        "feature_importance": {
            "features": feature_names,
            "importance": imp["importance"].tolist(),
        },
    }

    os.makedirs("data/curated/xauusd", exist_ok=True)
    with open("data/curated/xauusd/ml_quick_test_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print("\nResults saved to data/curated/xauusd/ml_quick_test_results.json")
    print("\nDone.")


if __name__ == "__main__":
    main()
