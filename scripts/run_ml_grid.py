"""
Grid search over thresholds to find optimal performance.
"""

import pandas as pd
import glob
import sys

sys.path.insert(0, ".")
from researchos.ml_engine.pipeline import run_ml_backtest


def main():
    print("Loading data...")
    files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
    df = pd.concat(
        [
            pd.read_csv(
                f,
                sep=";",
                header=None,
                names=["datetime", "open", "high", "low", "close", "volume"],
            )
            for f in files
        ],
        ignore_index=True,
    )
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
    df = df.set_index("datetime")
    df_h = (
        df.resample("1h")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna()
    )
    print(f"Data loaded: {len(df_h)} bars")

    thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]
    model_type = "random_forest"  # or "xgboost"

    print(f"\n🔍 Grid search for {model_type}...")
    print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate | Accuracy")
    print("----------|--------|---------|--------|--------|---------|---------")

    for th in thresholds:
        result, metrics = run_ml_backtest(
            df_h, model_type=model_type, threshold=th, train_ratio=0.7, retrain=True
        )
        print(
            f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%} | {metrics['test_accuracy']:7.2%}"
        )


if __name__ == "__main__":
    main()
