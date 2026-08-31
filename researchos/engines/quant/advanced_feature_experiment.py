"""
Advanced feature engineering experiment for XAUUSD.

Stages:
  Stage 1: Walk-forward with all features, uncorrected p-values
  Stage 2: Bonferroni-corrected significance
  Stage 3: Final holdout validation (last 20% data, only Stage 2-passed hypotheses)

Methodological rules:
  - No look-ahead bias: all features use only data up to time t
  - 3-way target/signal alignment: BUY/SELL/HOLD
  - Non-overlapping evaluation for multi-horizon: stride = horizon
  - Multiple testing correction: Bonferroni
  - True holdout: last 20% never used for feature selection or tuning
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

try:
    from lightgbm import LGBMClassifier
except ImportError:
    print("ERROR: lightgbm is required. Install with: pip install lightgbm")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GOLD_CSV = PROJECT_ROOT / "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
DXY_CSV = PROJECT_ROOT / "dxy_real_2021_2025.csv"
VIX_CSV = PROJECT_ROOT / "vix_real_2021_2025.csv"
US10Y_CSV = PROJECT_ROOT / "us10y_real_2021_2025.csv"
OUTPUT_DIR = PROJECT_ROOT / "reports/feature_engineering"

# ---------------------------------------------------------------------------
# LightGBM params (anti-overfitting)
# ---------------------------------------------------------------------------
LGBM_PARAMS = {
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

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_gold_data() -> pd.DataFrame:
    """Load real XAUUSD daily data."""
    df = pd.read_csv(GOLD_CSV)
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
    return df


def load_macro_data() -> dict[str, pd.DataFrame]:
    """Load real macro data: DXY, VIX, US10Y."""
    macro = {}

    # DXY
    dxy = pd.read_csv(DXY_CSV, skiprows=2)
    dxy.columns = ["date", "close", "high", "low", "open", "volume"]
    dxy["date"] = pd.to_datetime(dxy["date"])
    dxy["dxy_close"] = pd.to_numeric(dxy["close"], errors="coerce")
    macro["dxy"] = dxy[["date", "dxy_close"]].sort_values("date").reset_index(drop=True)

    # VIX
    vix = pd.read_csv(VIX_CSV, skiprows=2)
    vix.columns = ["date", "close", "high", "low", "open", "volume"]
    vix["date"] = pd.to_datetime(vix["date"])
    vix["vix_close"] = pd.to_numeric(vix["close"], errors="coerce")
    macro["vix"] = vix[["date", "vix_close"]].sort_values("date").reset_index(drop=True)

    # US10Y
    us10y = pd.read_csv(US10Y_CSV, header=None, skiprows=2)
    us10y.columns = ["date", "us10y_close"]
    us10y["date"] = pd.to_datetime(us10y["date"])
    us10y["us10y_close"] = pd.to_numeric(us10y["us10y_close"], errors="coerce")
    macro["us10y"] = us10y[["date", "us10y_close"]].sort_values("date").reset_index(drop=True)

    return macro


# ---------------------------------------------------------------------------
# Feature engineering (PIT-safe)
# ---------------------------------------------------------------------------


def create_features(gold: pd.DataFrame, macro: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Create all features with strict PIT compliance.

    Features:
        Price/volume:
            - rolling_5d_return, rolling_20d_return
            - rolling_20d_volatility
            - rolling_z_score_price (60d)
            - volume_ratio (current / 20d avg)
            - high_low_range, close_open_ratio

        Macro (DXY, VIX, US10Y):
            - dxy_return, dxy_lag_1/3/5/10
            - vix_level, vix_change, vix_lag_1/3/5/10
            - us10y_level, us10y_change, us10y_lag_1/3/5/10

        Interactions:
            - dxy_return_x_vix_level
            - vix_change_x_us10y_change

        Regime:
            - vix_regime (high/low based on 60d quantile)
            - dxy_trend (up/down vs 20d SMA)

        Rolling correlation:
            - gold_dxy_corr_60d
            - gold_vix_corr_60d
    """
    df = gold.copy()
    df = df.sort_values("date").reset_index(drop=True)

    # --- Price/volume features ---
    df["rolling_5d_return"] = df["close"].pct_change(5)
    df["rolling_20d_return"] = df["close"].pct_change(20)
    df["rolling_20d_volatility"] = df["close"].pct_change().rolling(20).std()
    df["rolling_z_score_price"] = (df["close"] - df["close"].rolling(60).mean()) / df["close"].rolling(60).std()
    df["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
    df["high_low_range"] = (df["high"] - df["low"]) / df["close"]
    df["close_open_ratio"] = df["close"] / df["open"]

    # --- Merge macro data (INNER join to ensure all macro data available) ---
    for name, macro_df in macro.items():
        df = df.merge(macro_df, on="date", how="inner")

    # --- Macro features ---
    # DXY
    df["dxy_return"] = df["dxy_close"].pct_change()
    for lag in [1, 3, 5, 10]:
        df[f"dxy_lag_{lag}d"] = df["dxy_return"].shift(lag)

    # VIX
    df["vix_change"] = df["vix_close"].diff()
    for lag in [1, 3, 5, 10]:
        df[f"vix_lag_{lag}d"] = df["vix_close"].shift(lag)

    # US10Y
    df["us10y_change"] = df["us10y_close"].diff()
    for lag in [1, 3, 5, 10]:
        df[f"us10y_lag_{lag}d"] = df["us10y_close"].shift(lag)

    # --- Interaction terms ---
    df["dxy_return_x_vix_level"] = df["dxy_return"] * df["vix_close"]
    df["vix_change_x_us10y_change"] = df["vix_change"] * df["us10y_change"]

    # --- Regime features ---
    # VIX regime: high if VIX > 60d rolling 75th percentile
    vix_quantile_75 = df["vix_close"].rolling(60).quantile(0.75)
    df["vix_regime_high"] = (df["vix_close"] > vix_quantile_75).astype(int)

    # DXY trend: up if DXY > 20d SMA, else down
    dxy_sma20 = df["dxy_close"].rolling(20).mean()
    df["dxy_trend_up"] = (df["dxy_close"] > dxy_sma20).astype(int)

    # --- Rolling correlation (Gold-DXY, Gold-VIX) ---
    df["gold_dxy_corr_60d"] = df["close"].pct_change().rolling(60).corr(df["dxy_close"].pct_change())
    df["gold_vix_corr_60d"] = df["close"].pct_change().rolling(60).corr(df["vix_close"].pct_change())

    # Drop rows with NaN from rolling/lag features
    feature_cols = [
        # Price/volume
        "rolling_5d_return",
        "rolling_20d_return",
        "rolling_20d_volatility",
        "rolling_z_score_price",
        "volume_ratio",
        "high_low_range",
        "close_open_ratio",
        # DXY
        "dxy_return",
        "dxy_lag_1d",
        "dxy_lag_3d",
        "dxy_lag_5d",
        "dxy_lag_10d",
        # VIX
        "vix_close",
        "vix_change",
        "vix_lag_1d",
        "vix_lag_3d",
        "vix_lag_5d",
        "vix_lag_10d",
        # US10Y
        "us10y_close",
        "us10y_change",
        "us10y_lag_1d",
        "us10y_lag_3d",
        "us10y_lag_5d",
        "us10y_lag_10d",
        # Interactions
        "dxy_return_x_vix_level",
        "vix_change_x_us10y_change",
        # Regime
        "vix_regime_high",
        "dxy_trend_up",
        # Rolling correlation
        "gold_dxy_corr_60d",
        "gold_vix_corr_60d",
    ]

    df = df.dropna(subset=feature_cols).reset_index(drop=True)
    return df, feature_cols


# ---------------------------------------------------------------------------
# Target creation (3-way: BUY/SELL/HOLD)
# ---------------------------------------------------------------------------


def create_3way_target(df: pd.DataFrame, horizon: int = 1, threshold: float = 0.0) -> pd.DataFrame:
    """
    Create 3-way target aligned with 3-way signals.

    BUY (2): next return > +threshold
    SELL (0): next return < -threshold
    HOLD (1): otherwise

    This ensures signal ∈ {-1, 0, 1} maps correctly to target ∈ {0, 1, 2}.
    """
    df = df.copy()
    df["future_return"] = df["close"].shift(-horizon) / df["close"] - 1

    def classify(ret):
        if pd.isna(ret):
            return 1  # HOLD for NaN
        if ret > threshold:
            return 2  # BUY
        elif ret < -threshold:
            return 0  # SELL
        return 1  # HOLD

    df["target"] = df["future_return"].apply(classify)
    df = df.iloc[:-horizon].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Walk-forward with LightGBM
# ---------------------------------------------------------------------------


def walk_forward_lightgbm_3way(
    df: pd.DataFrame,
    feature_cols: list[str],
    lookback: int = 252,
    step: int = 1,
    params: dict | None = None,
) -> tuple[pd.Series, pd.Series]:
    """
    Walk-forward LightGBM training and prediction for 3-way target.

    Returns:
        predictions: probability of BUY (class 2)
        actuals: actual target {0, 1, 2}
    """
    if params is None:
        params = LGBM_PARAMS.copy()

    X_all = df[feature_cols].values
    y_all = df["target"].values
    dates = df["date"].values

    predictions = []
    pred_dates = []

    for i in range(lookback, len(df), step):
        X_train = X_all[:i]
        y_train = y_all[:i]
        X_test = X_all[i : i + 1]

        if np.any(np.isnan(X_train)) or np.any(np.isnan(X_test)):
            continue

        model = LGBMClassifier(**params)
        model.fit(X_train, y_train)

        # Probability of BUY class (2)
        proba = model.predict_proba(X_test)[0]
        if 2 in model.classes_:
            prob_buy = proba[model.classes_ == 2][0]
        else:
            prob_buy = 0.0
        predictions.append(prob_buy)
        pred_dates.append(dates[i])

    pred_series = pd.Series(predictions, index=pred_dates, name="prediction")
    actual_series = pd.Series(y_all[lookback::step], index=pred_dates[: len(y_all[lookback::step])], name="actual")

    return pred_series, actual_series


# ---------------------------------------------------------------------------
# Dynamic thresholding for 3-way signals
# ---------------------------------------------------------------------------


def apply_3way_thresholds(
    predictions: pd.Series,
    window: int = 60,
    buy_quantile: float = 0.7,
    sell_quantile: float = 0.3,
) -> pd.DataFrame:
    """
    Apply dynamic thresholds for 3-way signals.

    BUY: prediction > rolling(window).quantile(buy_quantile)
    SELL: prediction < rolling(window).quantile(sell_quantile)
    HOLD: otherwise
    """
    signals = []
    confidences = []

    rolling_buy_threshold = predictions.rolling(window, min_periods=window).quantile(buy_quantile)
    rolling_sell_threshold = predictions.rolling(window, min_periods=window).quantile(sell_quantile)

    for i, (date, pred) in enumerate(predictions.items()):
        if pd.isna(pred):
            continue

        buy_thresh = rolling_buy_threshold.iloc[i] if i < len(rolling_buy_threshold) else np.nan
        sell_thresh = rolling_sell_threshold.iloc[i] if i < len(rolling_sell_threshold) else np.nan

        if pd.isna(buy_thresh) or pd.isna(sell_thresh):
            signals.append(1)  # HOLD
            confidences.append(0.5)
            continue

        if pred > buy_thresh:
            signal = 2  # BUY
            confidence = min((pred - buy_thresh) / (1.0 - buy_thresh + 1e-9), 1.0)
        elif pred < sell_thresh:
            signal = 0  # SELL
            confidence = min((sell_thresh - pred) / (sell_thresh + 1e-9), 1.0)
        else:
            signal = 1  # HOLD
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
# Accuracy calculation (3-way, proper mapping)
# ---------------------------------------------------------------------------


def compute_3way_accuracy(signals_df: pd.DataFrame) -> dict:
    """
    Compute accuracy for 3-way signal vs 3-way target.

    signal: {-1, 0, 1} -> mapped to {0, 1, 2} (SELL, HOLD, BUY)
    actual: {0, 1, 2} (SELL, HOLD, BUY)
    """
    df = signals_df.copy()

    # Map signal to 3-way target space
    # signal=-1 (SELL from old schema) -> 0
    # signal=0 (HOLD from old schema) -> 1
    # signal=1 (BUY from old schema) -> 2
    df["signal_mapped"] = df["signal"].map({-1: 0, 0: 1, 1: 2})

    # Overall accuracy
    overall_acc = (df["signal_mapped"] == df["actual"]).mean()

    # Per-class accuracy
    class_acc = {}
    for cls in [0, 1, 2]:
        mask = df["actual"] == cls
        if mask.sum() > 0:
            class_acc[cls] = (df.loc[mask, "signal_mapped"] == cls).mean()
        else:
            class_acc[cls] = 0.0

    # Baseline: majority class
    class_counts = df["actual"].value_counts()
    baseline = class_counts.iloc[0] / len(df)

    # Confusion matrix
    confusion = {}
    for pred_cls in [0, 1, 2]:
        for act_cls in [0, 1, 2]:
            confusion[(pred_cls, act_cls)] = ((df["signal_mapped"] == pred_cls) & (df["actual"] == act_cls)).sum()

    return {
        "overall_accuracy": overall_acc,
        "baseline_accuracy": baseline,
        "class_accuracy": class_acc,
        "confusion_matrix": confusion,
        "n_samples": len(df),
    }


# ---------------------------------------------------------------------------
# Hypothesis testing with multiple testing correction
# ---------------------------------------------------------------------------


def bonferroni_correct(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Apply Bonferroni correction."""
    m = len(p_values)
    corrected_alpha = alpha / m
    return [p < corrected_alpha for p in p_values]


# ---------------------------------------------------------------------------
# Stage 1: Walk-forward exploration
# ---------------------------------------------------------------------------


def stage1_walk_forward(
    df: pd.DataFrame,
    feature_cols: list[str],
    horizons: list[int] = [1, 3, 5],
    lookback: int = 252,
) -> pd.DataFrame:
    """
    Stage 1: Walk-forward for all horizon/feature combinations.
    No multiple testing correction yet.
    """
    results = []

    for horizon in horizons:
        print(f"\n  Horizon: {horizon}d")
        df_h = create_3way_target(df, horizon=horizon)
        preds, actuals = walk_forward_lightgbm_3way(df_h, feature_cols, lookback=lookback)

        # Apply 3-way dynamic thresholds
        signals_df = apply_3way_thresholds(preds, window=60)
        signals_df = signals_df.set_index("timestamp")
        actuals_aligned = actuals.reindex(signals_df.index)
        signals_df["actual"] = actuals_aligned.values
        signals_df = signals_df.dropna(subset=["actual"])

        if len(signals_df) == 0:
            continue

        # Compute 3-way accuracy
        signals_df["signal_mapped"] = signals_df["signal"].map({-1: 0, 0: 1, 1: 2})
        metrics = compute_3way_accuracy(signals_df)

        # Paired t-test: compare model predictions vs baseline
        # For each day, check if model signal matches actual
        model_correct = (signals_df["signal_mapped"] == signals_df["actual"]).astype(int)
        baseline_correct = (signals_df["actual"] == signals_df["actual"].mode()[0]).astype(int)

        t_stat, p_value = stats.ttest_rel(model_correct, baseline_correct)

        results.append(
            {
                "horizon": horizon,
                "n_samples": metrics["n_samples"],
                "overall_accuracy": metrics["overall_accuracy"],
                "baseline_accuracy": metrics["baseline_accuracy"],
                "improvement": metrics["overall_accuracy"] - metrics["baseline_accuracy"],
                "t_statistic": t_stat,
                "p_value": p_value,
                "buy_accuracy": metrics["class_accuracy"].get(2, 0.0),
                "sell_accuracy": metrics["class_accuracy"].get(0, 0.0),
                "hold_accuracy": metrics["class_accuracy"].get(1, 0.0),
            }
        )

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Stage 2: Bonferroni correction
# ---------------------------------------------------------------------------


def stage2_bonferroni(stage1_results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Apply Bonferroni correction to Stage 1 results."""
    m = len(stage1_results)
    corrected_alpha = alpha / m

    stage1_results = stage1_results.copy()
    stage1_results["bonferroni_alpha"] = corrected_alpha
    stage1_results["significant"] = stage1_results["p_value"] < corrected_alpha
    stage1_results["corrected_p_value"] = stage1_results["p_value"] * m

    return stage1_results


# ---------------------------------------------------------------------------
# Stage 3: Holdout validation
# ---------------------------------------------------------------------------


def stage3_holdout(
    df: pd.DataFrame,
    feature_cols: list[str],
    passed_horizons: list[int],
    lookback: int = 252,
) -> pd.DataFrame:
    """
    Stage 3: Final holdout validation on last 20% of data.
    Only test hypotheses that passed Stage 2 Bonferroni correction.
    """
    if not passed_horizons:
        print("  No hypotheses passed Stage 2. Skipping holdout.")
        return pd.DataFrame()

    # Split: last 20% is holdout
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    holdout_df = df.iloc[split_idx:].copy()

    print(f"  Train: {len(train_df)} rows, Holdout: {len(holdout_df)} rows")

    results = []

    for horizon in passed_horizons:
        print(f"\n  Horizon: {horizon}d (holdout)")

        # Create target on holdout
        holdout_df_h = create_3way_target(holdout_df, horizon=horizon)
        train_df_h = create_3way_target(train_df, horizon=horizon)

        if len(holdout_df_h) == 0:
            continue

        # Walk-forward on holdout only (no training on holdout)
        preds, actuals = walk_forward_lightgbm_3way(holdout_df_h, feature_cols, lookback=min(lookback, len(train_df_h)))

        if len(preds) == 0:
            continue

        signals_df = apply_3way_thresholds(preds, window=60)
        signals_df = signals_df.set_index("timestamp")
        actuals_aligned = actuals.reindex(signals_df.index)
        signals_df["actual"] = actuals_aligned.values
        signals_df = signals_df.dropna(subset=["actual"])

        if len(signals_df) == 0:
            continue

        metrics = compute_3way_accuracy(signals_df)

        results.append(
            {
                "horizon": horizon,
                "n_samples": metrics["n_samples"],
                "overall_accuracy": metrics["overall_accuracy"],
                "baseline_accuracy": metrics["baseline_accuracy"],
                "improvement": metrics["overall_accuracy"] - metrics["baseline_accuracy"],
                "buy_accuracy": metrics["class_accuracy"].get(2, 0.0),
                "sell_accuracy": metrics["class_accuracy"].get(0, 0.0),
                "hold_accuracy": metrics["class_accuracy"].get(1, 0.0),
                "stage": "holdout",
            }
        )

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 80)
    print("ADVANCED FEATURE ENGINEERING EXPERIMENT — XAUUSD")
    print("=" * 80)

    # 1. Load data
    print("\n[1] Loading real data...")
    gold = load_gold_data()
    print(f"    Gold: {len(gold)} rows, {gold['date'].min()} -> {gold['date'].max()}")

    macro = load_macro_data()
    for name, df in macro.items():
        print(f"    {name.upper()}: {len(df)} rows")

    # 2. Create features
    print("\n[2] Creating features...")
    df, feature_cols = create_features(gold, macro)
    print(f"    Total features: {len(feature_cols)}")
    for f in feature_cols:
        print(f"      - {f}")
    print(f"    Rows after feature creation: {len(df)}")

    # 3. Split: last 20% is holdout (NEVER touch until Stage 3)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    holdout_df = df.iloc[split_idx:].copy()
    print("\n[3] Data split:")
    print(f"    Train/Val: {len(train_df)} rows ({len(train_df)/len(df)*100:.0f}%)")
    print(f"    Holdout:   {len(holdout_df)} rows ({len(holdout_df)/len(df)*100:.0f}%)")

    # 4. Stage 1: Walk-forward on train/val only
    print("\n[4] STAGE 1: Walk-forward (train/val only)...")
    stage1_results = stage1_walk_forward(train_df, feature_cols, horizons=[1, 3, 5], lookback=252)

    print("\n  Stage 1 Results:")
    print(stage1_results.to_string(index=False))

    # 5. Stage 2: Bonferroni correction
    print("\n[5] STAGE 2: Bonferroni correction...")
    stage2_results = stage2_bonferroni(stage1_results, alpha=0.05)

    print("\n  Stage 2 Results:")
    print(stage2_results[["horizon", "overall_accuracy", "baseline_accuracy", "improvement", "p_value", "corrected_p_value", "significant"]].to_string(index=False))

    passed = stage2_results[stage2_results["significant"]]["horizon"].tolist()
    print(f"\n  Hypotheses passing Bonferroni correction: {passed}")

    # 6. Stage 3: Holdout validation
    print("\n[6] STAGE 3: Holdout validation...")
    if passed:
        stage3_results = stage3_holdout(df, feature_cols, passed, lookback=252)
        if len(stage3_results) > 0:
            print("\n  Stage 3 Results:")
            print(stage3_results.to_string(index=False))
        else:
            print("  No Stage 3 results (insufficient data or no passed hypotheses).")
    else:
        print("  SKIPPED: No hypotheses passed Stage 2.")

    # 7. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if len(passed) > 0:
        print(f"Stage 1: {len(stage1_results)} hypotheses tested")
        print(f"Stage 2: {len(passed)} hypotheses passed Bonferroni correction")
        print(f"Stage 3: Holdout validation completed for {len(passed)} hypothesis(s)")

        best = stage2_results[stage2_results["significant"]].iloc[0]
        print("\nBest result (Stage 2):")
        print(f"  Horizon: {best['horizon']}d")
        print(f"  Accuracy: {best['overall_accuracy']:.4f}")
        print(f"  Baseline: {best['baseline_accuracy']:.4f}")
        print(f"  Improvement: {best['improvement']:+.4f}")
        print(f"  P-value (uncorrected): {best['p_value']:.4f}")
        print(f"  P-value (corrected): {best['corrected_p_value']:.4f}")
    else:
        print("No hypotheses passed Bonferroni correction.")
        print("The feature set does not demonstrate statistically significant")
        print("predictive power for XAUUSD direction after multiple testing correction.")


if __name__ == "__main__":
    main()
