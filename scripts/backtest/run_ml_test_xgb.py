import pandas as pd
import glob
import sys

sys.path.insert(0, ".")
from researchos.engines.ml.pipeline import run_ml_backtest

print("Loading data...")
files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
df = pd.concat(
    [
        pd.read_csv(
            f, sep=";", header=None, names=["datetime", "open", "high", "low", "close", "volume"]
        )
        for f in files
    ],
    ignore_index=True,
)
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
df = df.set_index("datetime")
df_h = (
    df.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
)
print(f"Data loaded: {len(df_h)} bars")

print("Running ML backtest (XGBoost)...")
result, metrics = run_ml_backtest(df_h, model_type="xgboost", threshold=0.55, train_ratio=0.7)

print("\n=== RESULTS ===")
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Win Rate: {result.win_rate:.2%}")
print(f"Number of Trades: {result.num_trades}")
print(f"Model Test Accuracy: {metrics['test_accuracy']:.2%}")
