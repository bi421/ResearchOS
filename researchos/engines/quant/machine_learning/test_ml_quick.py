"""
Quick test for ML pipeline - imports and basic smoke test.
"""

from __future__ import annotations

import time
from typing import List

import numpy as np

from researchos.engines.quant.machine_learning.deep_models import MLPRegressor
from researchos.engines.quant.machine_learning.features import (
    compute_indicator_metrics,
    generate_features,
    generate_signals_vectorized,
)


def simulate_trades_vectorized(
    close: np.ndarray,
    signals: np.ndarray,
    commission: float = 0.0001,
) -> List[dict]:
    """Simulate trades from signals vectorized."""
    trades = []
    position = 0
    entry_price = 0.0

    for i in range(1, len(close)):
        signal = signals[i]

        if signal > 0 and position == 0:  # Buy signal
            position = 1
            entry_price = close[i]
        elif signal < 0 and position == 1:  # Sell signal
            position = 0
            exit_price = close[i]
            pnl = (exit_price - entry_price) / entry_price - commission
            trades.append(
                {
                    "entry_idx": int(np.where(signals[:i] == 1)[0][-1]) if len(np.where(signals[:i] == 1)[0]) > 0 else 0,
                    "exit_idx": i,
                    "entry_price": float(entry_price),
                    "exit_price": float(exit_price),
                    "pnl_pct": float(pnl * 100),
                    "duration": i - int(np.where(signals[:i] == 1)[0][-1]) if len(np.where(signals[:i] == 1)[0]) > 0 else 0,
                }
            )

    return trades


def run_quick_ml_test(
    close: np.ndarray,
    volumes: np.ndarray,
    lookback: int = 60,
    epochs: int = 10,
    batch_size: int = 32,
    commission: float = 0.0001,
    random_state: int = 42,
) -> dict:
    """Run a quick ML test."""
    start_time = time.time()

    # Build features
    features = generate_features(
        close=close,
        volumes=volumes,
        lookback=lookback,
    )

    # Build labels
    labels = compute_label_returns(close, forward_periods=5)

    # Mask valid rows
    valid_mask = ~(np.isnan(features).any(axis=1) | np.isnan(labels))
    X = features[valid_mask]
    y = labels[valid_mask]

    if len(X) == 0:
        raise ValueError("No valid data points after masking")

    # Simple train/test split
    split_idx = int(len(X) * 0.7)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")

    # Train MLP
    model = MLPRegressor(
        input_dim=X_train.shape[1],
        hidden_dim=64,
        output_dim=1,
        dropout_rate=0.2,
        random_state=random_state,
    )

    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)

    # Predict
    y_pred = model.forward(X_test, training=False)

    # Compute metrics
    test_mse = np.mean((y_pred.flatten() - y_test) ** 2)
    test_mae = np.mean(np.abs(y_pred.flatten() - y_test))

    # Direction accuracy
    pred_direction = (y_pred.flatten() > 0).astype(int)
    true_direction = (y_test > 0).astype(int)
    direction_accuracy = np.mean(pred_direction == true_direction)

    print(f"ML Test MSE: {test_mse:.6f}")
    print(f"ML Test MAE: {test_mae:.6f}")
    print(f"ML Direction Accuracy: {direction_accuracy:.3f}")

    # Run indicator strategy on test portion
    test_signals = generate_signals_vectorized(X_test[:, -1])  # Use last feature as proxy
    test_close = X_test[:, -1]  # Use last feature as proxy

    trades = simulate_trades_vectorized(test_close, test_signals, commission=commission)
    ind_metrics = compute_indicator_metrics(trades)

    print(f"  Trades: {ind_metrics['trade_count']}")
    print(f"  Win Rate: {ind_metrics['win_rate']:.2f}%")

    # Compare
    comparison = {
        "ml_direction_accuracy": float(direction_accuracy),
        "indicator_win_rate": float(ind_metrics["win_rate"]),
        "ml_vs_indicator_delta": float(direction_accuracy - ind_metrics["win_rate"] / 100),
    }

    timing = {
        "total_time": time.time() - start_time,
        "ml_time": time.time() - start_time,
    }

    return {
        "ml_metrics": {
            "test_mse": float(test_mse),
            "test_mae": float(test_mae),
            "direction_accuracy": float(direction_accuracy),
        },
        "indicator_metrics": ind_metrics,
        "comparison": comparison,
        "timing": timing,
    }


def compute_label_returns(
    close: np.ndarray,
    forward_periods: int = 5,
) -> np.ndarray:
    """Compute forward returns as labels."""
    returns = np.diff(np.log(close))
    forward_returns = np.zeros(len(returns))

    for i in range(len(returns) - forward_periods):
        forward_returns[i] = np.mean(returns[i : i + forward_periods])

    return forward_returns[:-forward_periods]


if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    n_days = 500
    close = 100 * np.exp(np.cumsum(np.random.randn(n_days) * 0.01))
    volumes = np.random.randint(1000000, 10000000, n_days)

    results = run_quick_ml_test(close, volumes)

    print("\n=== Quick ML Test Complete ===")
    print(results)
