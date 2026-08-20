"""
ML backtest runner with configurable parameters.
"""
import pandas as pd
import glob
import sys
import argparse
sys.path.insert(0, ".")
from researchos.ml_engine.pipeline import run_ml_backtest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="random_forest", choices=["random_forest", "xgboost"])
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--train_ratio", type=float, default=0.7)
    args = parser.parse_args()

    print("Loading data...")
    files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
    df = pd.concat([pd.read_csv(f, sep=";", header=None,
                                names=["datetime","open","high","low","close","volume"])
                    for f in files], ignore_index=True)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
    df = df.set_index("datetime")
    df_h = df.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    print(f"Data loaded: {len(df_h)} bars")

    print(f"Running ML backtest ({args.model}, threshold={args.threshold})...")
    result, metrics = run_ml_backtest(
        df_h,
        model_type=args.model,
        threshold=args.threshold,
        train_ratio=args.train_ratio
    )

    print("\n=== RESULTS ===")
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Number of Trades: {result.num_trades}")
    print(f"Model Test Accuracy: {metrics['test_accuracy']:.2%}")

if __name__ == "__main__":
    main()
