"""
End-to-end ML backtest pipeline.
"""

import pandas as pd

from ..quant.backtest import BacktestEngine, BacktestResult
from .features import create_features
from .model import load_model, save_model, train_model
from .strategy import MLStrategy


def run_ml_backtest(
    df: pd.DataFrame,
    model_type: str = "random_forest",
    threshold: float = 0.55,
    train_ratio: float = 0.7,
    retrain: bool = True,
) -> tuple[BacktestResult, dict]:
    df_feat = create_features(df)
    if df_feat.empty:
        raise ValueError("Feature ????????? ????? ??????? ?????? ?????.")

    if retrain:
        model, scaler, metrics = train_model(df_feat, model_type=model_type, test_size=1 - train_ratio)
        save_model(model, scaler, metrics, "ml_model.pkl")
    else:
        model, scaler, metrics = load_model("ml_model.pkl")

    feature_names = metrics["feature_names"]
    strategy = MLStrategy(model, scaler, feature_names, threshold=threshold)

    engine = BacktestEngine()
    prices = df["close"].tolist()
    result = engine.run(prices, strategy)
    return result, metrics
