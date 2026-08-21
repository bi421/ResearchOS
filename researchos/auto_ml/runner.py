import glob
import sys

import optuna
import pandas as pd

sys.path.insert(0, ".")
from researchos.auto_ml.objective import Objective


def run_auto_ml(n_trials=50):
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
    df_h = df.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    print(f"Data: {len(df_h)} bars (4h)")

    # 2021-2024 train, 2025 val, 2026 test
    dates = df_h.index
    split1 = int(len(dates) * 0.7)
    split2 = int(len(dates) * 0.85)
    train_df = df_h.iloc[:split1]
    val_df = df_h.iloc[split1:split2]
    test_df = df_h.iloc[split2:]
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    objective = Objective(df_h, train_df, val_df, test_df, [])
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print("\n" + "=" * 50)
    print("🏆 BEST PARAMETERS FOUND")
    print("=" * 50)
    best = study.best_params
    for key, value in best.items():
        print(f"{key}: {value}")
    print(f"Best Validation Sharpe: {study.best_value:.4f}")

    return study


if __name__ == "__main__":
    run_auto_ml(n_trials=50)
