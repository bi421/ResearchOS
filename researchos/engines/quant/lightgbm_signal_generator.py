"""
LightGBM-based signal generator for XAUUSD.

Replaces the linear OLS macro-factor model with:
  - Price/volume feature engineering
  - LightGBM classifier with anti-overfitting parameters
  - Dynamic threshold based on rolling probability quantiles
  - PIT-compliant signal file output

Usage:
    python scripts/analysis/generate_signals_lightgbm.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    from lightgbm import LGBMClassifier
except ImportError:
    print("ERROR: lightgbm is required. Install with: pip install lightgbm")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GOLD_CSV = PROJECT_ROOT / "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
OUTPUT_PATH = PROJECT_ROOT / "reports/signals/lightgbm_signals.csv"


# ---------------------------------------------------------------------------
# 1. PIT-compliant feature engineering
# ---------------------------------------------------------------------------


def create_price_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create price/volume features with strict PIT compliance.

    All features use only data available UP TO the current bar.
    No future data leaks into feature calculation.

    Features:
        - rolling_5d_return: 5-day price return
        - rolling_20d_return: 20-day price return
        - rolling_20d_volatility: 20-day std of returns
        - rolling_z_score_price: 60-day z-score of close price
        - volume_ratio: current volume / 20-day average volume
    """
    df = df.copy()
    close = df["close"]
    volume = df["volume"]

    # Rolling returns (PIT: uses only past data via pandas rolling)
    df["rolling_5d_return"] = close.pct_change(5)
    df["rolling_20d_return"] = close.pct_change(20)

    # Rolling volatility (PIT: 20-day std of daily returns)
    df["rolling_20d_volatility"] = close.pct_change().rolling(20).std()

    # Rolling z-score of price (PIT: 60-day rolling mean/std)
    df["rolling_z_score_price"] = (close - close.rolling(60).mean()) / close.rolling(60).std()

    # Volume ratio (PIT: current vs 20-day average)
    df["volume_ratio"] = volume / volume.rolling(20).mean()

    # Additional features for better separation
    df["high_low_range"] = (df["high"] - df["low"]) / close
    df["close_open_ratio"] = close / df["open"]

    # Drop rows with NaN from rolling windows
    feature_cols = [
        "rolling_5d_return",
        "rolling_20d_return",
        "rolling_20d_volatility",
        "rolling_z_score_price",
        "volume_ratio",
        "high_low_range",
        "close_open_ratio",
    ]

    df = df.dropna(subset=feature_cols).reset_index(drop=True)
    return df, feature_cols


# ---------------------------------------------------------------------------
# 2. Target creation (next-day direction)
# ---------------------------------------------------------------------------


def create_target(df: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    """
    Create binary target: 1 if price goes up in next `horizon` days, 0 otherwise.

    PIT-compliant: target is created using shift(-horizon), which uses
    future data but is only used for LABELING training examples.
    At prediction time, we only use features available at time t.
    """
    df = df.copy()
    df["target"] = (df["close"].shift(-horizon) > df["close"]).astype(int)
    df = df.iloc[:-horizon].reset_index(drop=True)  # drop rows without future target
    return df


# ---------------------------------------------------------------------------
# 3. Walk-forward training with LightGBM
# ---------------------------------------------------------------------------


def walk_forward_lightgbm(
    df: pd.DataFrame,
    feature_cols: list[str],
    lookback: int = 252,
    step: int = 1,
    params: dict | None = None,
) -> tuple[pd.Series, pd.Series]:
    """
    Walk-forward LightGBM training and prediction.

    For each day t:
        - Train on data [:t] (all past data)
        - Predict probability for day t
        - Store prediction and actual

    Args:
        df: DataFrame with features and target
        feature_cols: List of feature column names
        lookback: Minimum training samples required
        step: Step size for walk-forward (1 = every day)
        params: LightGBM parameters

    Returns:
        (predictions, actuals) as pd.Series aligned by date
    """
    if params is None:
        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "num_leaves": 15,
            "max_depth": 4,
            "learning_rate": 0.05,
            "min_child_samples": 50,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
            "random_state": 42,
            "n_estimators": 200,
            "verbose": -1,
        }

    X_all = df[feature_cols].values
    y_all = df["target"].values
    dates = df["date"].values

    predictions = []
    pred_dates = []

    for i in range(lookback, len(df), step):
        X_train = X_all[:i]
        y_train = y_all[:i]
        X_test = X_all[i : i + 1]

        # Skip if any NaN in training or test
        if np.any(np.isnan(X_train)) or np.any(np.isnan(X_test)):
            continue

        model = LGBMClassifier(**params)
        model.fit(X_train, y_train)

        # Predict probability of class 1 (price going up)
        prob = model.predict_proba(X_test)[0, 1]
        predictions.append(prob)
        pred_dates.append(dates[i])

    pred_series = pd.Series(predictions, index=pred_dates, name="prediction")
    actual_series = pd.Series(y_all[lookback::step], index=pred_dates[: len(y_all[lookback::step])], name="actual")

    return pred_series, actual_series


# ---------------------------------------------------------------------------
# 4. Dynamic thresholding
# ---------------------------------------------------------------------------


def apply_dynamic_thresholds(
    predictions: pd.Series,
    window: int = 60,
    buy_quantile: float = 0.7,
    sell_quantile: float = 0.3,
) -> pd.DataFrame:
    """
    Apply dynamic thresholds based on rolling quantiles of predicted probabilities.

    BUY:  prediction > rolling(window).quantile(buy_quantile)
    SELL: prediction < rolling(window).quantile(sell_quantile)
    HOLD: otherwise

    This produces approximately:
        - BUY: ~30% of signals
        - SELL: ~30% of signals
        - HOLD: ~40% of signals
    """
    signals = []
    confidences = []

    # Compute rolling thresholds
    rolling_buy_threshold = predictions.rolling(window, min_periods=window).quantile(buy_quantile)
    rolling_sell_threshold = predictions.rolling(window, min_periods=window).quantile(sell_quantile)

    for i, (date, pred) in enumerate(predictions.items()):
        if pd.isna(pred):
            continue

        # Get thresholds for this date (use NaN if not enough history)
        buy_thresh = rolling_buy_threshold.iloc[i] if i < len(rolling_buy_threshold) else np.nan
        sell_thresh = rolling_sell_threshold.iloc[i] if i < len(rolling_sell_threshold) else np.nan

        if pd.isna(buy_thresh) or pd.isna(sell_thresh):
            # Not enough history for dynamic threshold
            signals.append(0)
            confidences.append(0.5)
            continue

        if pred > buy_thresh:
            signal = 1
            confidence = min((pred - buy_thresh) / (1.0 - buy_thresh + 1e-9), 1.0)
        elif pred < sell_thresh:
            signal = -1
            confidence = min((sell_thresh - pred) / (sell_thresh + 1e-9), 1.0)
        else:
            signal = 0
            confidence = 0.5

        signals.append(signal)
        confidences.append(max(0.0, min(1.0, confidence)))

    result = pd.DataFrame(
        {
            "timestamp": predictions.index,
            "signal": signals,
            "confidence": confidences,
            "prediction": predictions.values,
        }
    )
    return result


# ---------------------------------------------------------------------------
# 5. Main pipeline
# ---------------------------------------------------------------------------


def run_lightgbm_signal_pipeline(
    gold_csv: str | Path,
    output_path: str | Path,
    lookback: int = 252,
    threshold_window: int = 60,
) -> pd.DataFrame:
    """
    Complete LightGBM signal generation pipeline.

    Args:
        gold_csv: Path to XAUUSD daily CSV
        output_path: Where to save signal file
        lookback: Minimum training samples
        threshold_window: Rolling window for dynamic thresholds

    Returns:
        Signal DataFrame
    """
    print("=" * 70)
    print("LightGBM SIGNAL GENERATOR — XAUUSD")
    print("=" * 70)

    # 1. Load data
    print("\n[1] Loading XAUUSD data...")
    df = pd.read_csv(gold_csv)
    print(f"    Columns: {list(df.columns)}")
    print(f"    Rows: {len(df)}")

    # Robust date/close column detection
    date_col = [c for c in df.columns if c.lower() in ("date", "time", "datetime")][0]
    close_col = [c for c in df.columns if c.lower() == "close"][0]
    high_col = [c for c in df.columns if c.lower() == "high"][0]
    low_col = [c for c in df.columns if c.lower() == "low"][0]
    open_col = [c for c in df.columns if c.lower() == "open"][0]
    volume_col = [c for c in df.columns if c.lower() in ("volume", "tick_volume")][0]

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.rename(
        columns={
            date_col: "date",
            close_col: "close",
            high_col: "high",
            low_col: "low",
            open_col: "open",
            volume_col: "volume",
        }
    )
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date").reset_index(drop=True)
    print(f"    Date range: {df['date'].min()} -> {df['date'].max()}")

    # 2. Feature engineering
    print("\n[2] Creating price/volume features...")
    df, feature_cols = create_price_volume_features(df)
    print(f"    Features: {feature_cols}")
    print(f"    Rows after feature creation: {len(df)}")

    # 3. Create target
    print("\n[3] Creating target (next-day direction)...")
    df = create_target(df, horizon=1)
    print(f"    Target distribution: {df['target'].value_counts().to_dict()}")

    # 4. Walk-forward LightGBM
    print(f"\n[4] Running walk-forward LightGBM (lookback={lookback})...")
    predictions, actuals = walk_forward_lightgbm(df, feature_cols, lookback=lookback)
    print(f"    Predictions generated: {len(predictions)}")

    # 5. Dynamic thresholds
    print(f"\n[5] Applying dynamic thresholds (window={threshold_window})...")
    signals_df = apply_dynamic_thresholds(predictions, window=threshold_window)

    # Print distribution
    buy_count = (signals_df["signal"] == 1).sum()
    sell_count = (signals_df["signal"] == -1).sum()
    hold_count = (signals_df["signal"] == 0).sum()
    total = len(signals_df)
    print(f"    BUY:  {buy_count} ({buy_count/total*100:.1f}%)")
    print(f"    SELL: {sell_count} ({sell_count/total*100:.1f}%)")
    print(f"    HOLD: {hold_count} ({hold_count/total*100:.1f}%)")

    # 6. Merge with actuals for accuracy calculation
    signals_df = signals_df.set_index("timestamp")
    actuals_aligned = actuals.reindex(signals_df.index)
    signals_df["actual"] = actuals_aligned.values

    # 7. Add metadata columns
    signals_df["factors_used"] = json.dumps(sorted(feature_cols))
    signals_df["data_available_at"] = signals_df.index.strftime("%Y-%m-%d")
    signals_df["calculation_version"] = "signal/v2"
    signals_df["engine_version"] = "researchos/1.0.0"

    # Compute input hashes
    signals_df["input_hash"] = signals_df.apply(
        lambda row: _compute_input_hash(
            {
                "timestamp": str(row.name),
                "prediction": round(row["prediction"], 6),
                "signal": int(row["signal"]),
                "factors": sorted(feature_cols),
            }
        ),
        axis=1,
    )
    signals_df["notes"] = f"LightGBM with {len(feature_cols)} price/volume features"

    # 8. Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Reorder columns to match schema
    output_cols = [
        "timestamp",
        "signal",
        "confidence",
        "factors_used",
        "data_available_at",
        "prediction",
        "calculation_version",
        "engine_version",
        "input_hash",
        "notes",
    ]
    signals_df = signals_df.reset_index()
    signals_df["timestamp"] = signals_df["timestamp"].astype(str)
    signals_df[output_cols].to_csv(output_path, index=False)

    print(f"\n[6] Signal file saved: {output_path}")
    print(f"    Total signals: {len(signals_df)}")

    # 9. Accuracy
    valid_mask = signals_df["actual"].notna()
    if valid_mask.sum() > 0:
        valid_df = signals_df.loc[valid_mask].copy()

        # Corrected accuracy: exclude HOLD, map signal to direction
        trade_mask = valid_df["signal"] != 0
        if trade_mask.sum() > 0:
            trade_df = valid_df[trade_mask].copy()
            trade_df["signal_direction"] = (trade_df["signal"] == 1).astype(int)
            model_acc = (trade_df["signal_direction"] == trade_df["actual"]).mean()
            baseline_acc = max(trade_df["actual"].mean(), 1 - trade_df["actual"].mean())

            buy_df = trade_df[trade_df["signal"] == 1]
            sell_df = trade_df[trade_df["signal"] == -1]
            buy_acc = (buy_df["signal_direction"] == buy_df["actual"]).mean() if len(buy_df) > 0 else 0.0
            sell_acc = (sell_df["signal_direction"] == sell_df["actual"]).mean() if len(sell_df) > 0 else 0.0

            print("\n[7] OUT-OF-SAMPLE ACCURACY (directional, HOLD excluded):")
            print(f"    Model accuracy:    {model_acc:.4f}")
            print(f"    Baseline accuracy: {baseline_acc:.4f}")
            print(f"    Improvement:       {model_acc - baseline_acc:+.4f}")
            print(f"    BUY accuracy:      {buy_acc:.4f} (n={len(buy_df)})")
            print(f"    SELL accuracy:     {sell_acc:.4f} (n={len(sell_df)})")
        else:
            print("\n[7] No BUY/SELL signals generated, cannot compute accuracy.")

    return signals_df


# ---------------------------------------------------------------------------
# 6. Deterministic hashing (same as signal_file.py)
# ---------------------------------------------------------------------------


def _compute_input_hash(data: dict) -> str:
    """Compute deterministic SHA-256 hash of input data."""
    import hashlib
    import json

    def stable_float(value: float) -> str:
        if value == 0.0:
            return "0.0"
        return repr(value)

    def canonicalize(value):
        if isinstance(value, dict):
            return {str(k): canonicalize(v) for k, v in sorted(value.items(), key=str)}
        if isinstance(value, (list, tuple)):
            return [canonicalize(v) for v in value]
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return stable_float(value)
        if value is None or isinstance(value, str):
            return value
        return str(value)

    canonical = canonicalize(data)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 7. Validation (PIT compliance)
# ---------------------------------------------------------------------------


def validate_signal_file(signal_path: str | Path) -> dict:
    """Validate signal file for PIT compliance."""
    from researchos.engines.quant.signal_file import validate_signal_file as _validate

    return _validate(signal_path)


# ---------------------------------------------------------------------------
# 8. Entry point
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LightGBM signal generator for XAUUSD")
    parser.add_argument("--input", default=str(GOLD_CSV), help="Input gold CSV path")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output signal file path")
    parser.add_argument("--lookback", type=int, default=252, help="Training lookback window")
    parser.add_argument("--threshold-window", type=int, default=60, help="Dynamic threshold window")
    parser.add_argument("--validate", action="store_true", help="Validate output file")
    args = parser.parse_args()

    run_lightgbm_signal_pipeline(
        gold_csv=args.input,
        output_path=args.output,
        lookback=args.lookback,
        threshold_window=args.threshold_window,
    )

    if args.validate:
        print("\n[8] Validating signal file...")
        report = validate_signal_file(args.output)
        print(f"     Valid: {report['valid']}")
        if report["errors"]:
            print(f"     Errors: {report['errors']}")
        if report["warnings"]:
            print(f"     Warnings: {report['warnings']}")
        print(f"     Stats: {report['stats']}")


if __name__ == "__main__":
    main()
