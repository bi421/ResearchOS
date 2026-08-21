import glob
import sys

import pandas as pd

sys.path.insert(0, ".")
from researchos.ml_engine.features import create_features
from researchos.ml_engine.model import train_model
from researchos.ml_engine.strategy import MLStrategy
from researchos.quant_engine.backtest import BacktestEngine

print("Loading data...")
files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
df = pd.concat(
    [pd.read_csv(f, sep=";", header=None, names=["datetime", "open", "high", "low", "close", "volume"]) for f in files],
    ignore_index=True,
)
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
df = df.set_index("datetime")
df_h = df.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
print(f"Data: {len(df_h)} bars (4h)")

# 2026 оныг test гэж тусгаарлах
test_mask = df_h.index.year == 2026
train_mask = df_h.index.year < 2025
val_mask = df_h.index.year == 2025

train_df = df_h[train_mask]
val_df = df_h[val_mask]
test_df = df_h[test_mask]

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Feature generation
train_feat = create_features(train_df)
val_feat = create_features(val_df)
test_feat = create_features(test_df)

if train_feat.empty or val_feat.empty or test_feat.empty:
    print("Empty features!")
    sys.exit(1)

# Train model (Random Forest - өмнөх туршлагаас хамгийн сайн)
model, scaler, metrics = train_model(
    train_feat,
    model_type="random_forest",
    test_size=0.0,  # Validation-д тусад нь хадгалсан
)

# Validation дээр threshold сонгох (0.55, 0.58, 0.60)
feature_names = metrics["feature_names"]
thresholds = [0.55, 0.58, 0.60]
engine = BacktestEngine()
best_sharpe = -999
best_th = 0.55

print("\n🔍 Validation grid search (3 thresholds)")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")
for th in thresholds:
    strategy = MLStrategy(model, scaler, feature_names, threshold=th)
    val_prices = val_df["close"].tolist()
    result = engine.run(val_prices, strategy)
    if result.num_trades >= 20 and result.sharpe_ratio > best_sharpe:
        best_sharpe = result.sharpe_ratio
        best_th = th
    print(f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%}")
print(f"Best threshold: {best_th}")

# 2026 оны тест
print("\n📊 2026 OUT-OF-SAMPLE TEST")
strategy_final = MLStrategy(model, scaler, feature_names, threshold=best_th)
test_prices = test_df["close"].tolist()
test_result = engine.run(test_prices, strategy_final)

print(f"Trades: {test_result.num_trades}")
print(f"Return: {test_result.total_return:.2%}")
print(f"Sharpe: {test_result.sharpe_ratio:.2f}")
print(f"Max DD: {test_result.max_drawdown:.2%}")
print(f"Win Rate: {test_result.win_rate:.2%}")

if test_result.num_trades >= 30 and test_result.sharpe_ratio > 0.5:
    print("✅ SUCCESS! Strategy works on 2026 out-of-sample.")
else:
    print("❌ FAILED. Strategy does not work on 2026 data.")
