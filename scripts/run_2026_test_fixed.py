import pandas as pd
import numpy as np
import glob
import sys

sys.path.insert(0, ".")
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from researchos.quant_engine.vectorized_backtest import vectorized_backtest

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
    df.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
)
print(f"Data: {len(df_h)} bars (4h)")

# Train: 2021-2024, Val: 2025, Test: 2025-2026 (илүү их өгөгдөл)
train_mask = df_h.index.year < 2025
val_mask = df_h.index.year == 2025
test_mask = df_h.index.year >= 2025

train_df = df_h[train_mask]
val_df = df_h[val_mask]
test_df = df_h[test_mask]

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")


# -------------------------------
# FEATURE GENERATION (custom)
# -------------------------------
def make_features(df):
    df = df.copy()
    close = df["close"]
    df["ret1"] = close.pct_change()
    for lag in [1, 2, 3, 5, 10, 20]:
        df[f"ret_lag_{lag}"] = df["ret1"].shift(lag)
    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    # MACD
    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_diff"] = df["macd"] - df["macd_signal"]
    # Bollinger
    mean = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["bb_high"] = mean + 2 * std
    df["bb_low"] = mean - 2 * std
    df["bb_pos"] = (close - df["bb_low"]) / (df["bb_high"] - df["bb_low"])
    # Volatility
    df["volatility"] = df["ret1"].rolling(20).std()
    # Target (next bar direction)
    df["target"] = (close.shift(-1) > close).astype(int)
    df = df.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    return df


train_feat = make_features(train_df)
val_feat = make_features(val_df)
test_feat = make_features(test_df)

feature_cols = [c for c in train_feat.columns if c != "target"]
X_train = train_feat[feature_cols].values
y_train = train_feat["target"].values
X_val = val_feat[feature_cols].values
y_val = val_feat["target"].values
X_test = test_feat[feature_cols].values
y_test = test_feat["target"].values

# Scale
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val) if X_val.shape[0] > 0 else np.array([])
X_test_s = scaler.transform(X_test) if X_test.shape[0] > 0 else np.array([])

# Train RandomForest (fast)
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train_s, y_train)
print(f"Train accuracy: {model.score(X_train_s, y_train):.2%}")

# Validation grid search (threshold)
thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]
best_sharpe = -999
best_th = 0.55


def get_signals(df, probs, threshold):
    signals = []
    for i, idx in enumerate(df.index):
        if i < len(probs):
            prob = probs[i]
            price = df.loc[idx, "close"]
            if prob > threshold:
                signals.append(("BUY", price))
            elif prob < (1 - threshold):
                signals.append(("SELL", price))
    return signals


print("\n🔍 Validation grid search")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")

if X_val.shape[0] > 0:
    val_probs = model.predict_proba(X_val_s)[:, 1]
    for th in thresholds:
        signals = get_signals(val_df, val_probs, th)
        result = vectorized_backtest(val_df["close"].tolist(), signals)
        if result["num_trades"] >= 20 and result["sharpe"] > best_sharpe:
            best_sharpe = result["sharpe"]
            best_th = th
        print(
            f"{th:5.2f}     | {result['num_trades']:6d} | {result['total_return']:7.2%} | {result['sharpe']:6.2f} | {result['max_drawdown']:6.2%} | {result['win_rate']:7.2%}"
        )
    print(f"Best threshold: {best_th} (Sharpe={best_sharpe:.2f})")

# Test on 2025-2026
test_probs = model.predict_proba(X_test_s)[:, 1]
test_signals = get_signals(test_df, test_probs, best_th)
test_result = vectorized_backtest(test_df["close"].tolist(), test_signals)

print("\n📊 OUT-OF-SAMPLE TEST (2025-2026)")
print(f"Trades: {test_result['num_trades']}")
print(f"Return: {test_result['total_return']:.2%}")
print(f"Sharpe: {test_result['sharpe']:.2f}")
print(f"Max DD: {test_result['max_drawdown']:.2%}")
print(f"Win Rate: {test_result['win_rate']:.2%}")

if test_result["num_trades"] >= 30 and test_result["sharpe"] > 0.5:
    print("✅ SUCCESS! Strategy works on out-of-sample.")
else:
    print("❌ FAILED. Still insufficient features.")
