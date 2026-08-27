import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, "cpp_quant")

import glob

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from researchos.quant_engine.vectorized_backtest import vectorized_backtest

print("=" * 60)
print("🚀 REGRESSION TARGET: XAUUSD 4h (FIXED)")
print("=" * 60)

# =============================================
# 1. ӨГӨГДӨЛ АЧААЛАХ
# =============================================
print("Loading XAUUSD data...")
files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
df = pd.concat(
    [pd.read_csv(f, sep=";", header=None, names=["datetime", "open", "high", "low", "close", "volume"]) for f in files],
    ignore_index=True,
)
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
df = df.set_index("datetime")
df_h = df.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
print(f"Data: {len(df_h)} bars (4h)")


# =============================================
# 2. FEATURE GENERATION
# =============================================
def add_new_features(df):
    df = df.copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else None

    # Цагийн цикл
    hour = df.index.hour
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["dayofweek_sin"] = np.sin(2 * np.pi * df.index.dayofweek / 7)
    df["dayofweek_cos"] = np.cos(2 * np.pi * df.index.dayofweek / 7)

    # 24 цагийн хамгийн их/бага
    rolling_high = high.rolling(6).max()
    rolling_low = low.rolling(6).min()
    df["price_vs_high_24h"] = close / rolling_high - 1
    df["price_vs_low_24h"] = close / rolling_low - 1

    # ATR харьцаа
    tr = np.maximum(high - low, np.maximum((high - close.shift()).abs(), (low - close.shift()).abs()))
    atr = tr.rolling(14).mean()
    df["atr_ratio"] = atr / close

    # Volume ratio
    if volume is not None:
        df["volume_ma5"] = volume.rolling(5).mean()
        df["volume_ratio"] = volume / df["volume_ma5"]
        df.drop("volume_ma5", axis=1, inplace=True)

    # Хуучин feature-үүд
    df["ret1"] = close.pct_change()
    for lag in [1, 2, 3, 5, 10, 20]:
        df[f"ret_lag_{lag}"] = df["ret1"].shift(lag)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_diff"] = df["macd"] - df["macd_signal"]
    mean = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["bb_pos"] = (close - mean + 2 * std) / (4 * std)
    df["volatility"] = df["ret1"].rolling(20).std()

    # TARGET: дараагийн 1 лааны өгөөж
    df["target"] = close.shift(-1) / close - 1

    df = df.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    return df


df_h = add_new_features(df_h)

# =============================================
# 3. TRAIN/VAL/TEST SPLIT
# =============================================
train_mask = df_h.index.year <= 2023
val_mask = df_h.index.year == 2024
test_mask = df_h.index.year >= 2025

train_df = df_h[train_mask]
val_df = df_h[val_mask]
test_df = df_h[test_mask]
print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

feature_cols = [c for c in train_df.columns if c not in ["target", "volume"]]
X_train = train_df[feature_cols].values
y_train = train_df["target"].values
X_val = val_df[feature_cols].values
y_val = val_df["target"].values
X_test = test_df[feature_cols].values
y_test = test_df["target"].values

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val)
X_test_s = scaler.transform(X_test)

# =============================================
# 4. MODEL (XGBoost Regressor)
# =============================================
model = XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
)
model.fit(X_train_s, y_train, eval_set=[(X_val_s, y_val)], verbose=False)

# =============================================
# 5. VALIDATION дээр дохио үүсгэх
# =============================================
val_preds = model.predict(X_val_s)
val_prices = val_df["close"].values.tolist()


def eval_th(th):
    signals = []
    for i, pred in enumerate(val_preds):
        price = val_prices[i]
        if pred > th:
            signals.append(("BUY", price))
        elif pred < -th:
            signals.append(("SELL", price))
    if len(signals) < 5:
        return th, {
            "trades": 0,
            "sharpe": -999,
            "total_return": 0,
            "max_drawdown": 0,
            "win_rate": 0,
        }
    res = vectorized_backtest(val_prices, signals)
    return th, {
        "trades": res["num_trades"],
        "sharpe": res["sharpe"],
        "total_return": res["total_return"],
        "max_drawdown": res["max_drawdown"],
        "win_rate": res["win_rate"],
    }


thresholds = [0.001, 0.0015, 0.002, 0.0025, 0.003, 0.004]
print("\n🔍 Validation grid search (threshold on predicted return)")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")
results = Parallel(n_jobs=-1, prefer="threads")(delayed(eval_th)(th) for th in thresholds)
best_sharpe, best_th = -999, 0.002
for th, res in results:
    if res["trades"] >= 10 and res["sharpe"] > best_sharpe:
        best_sharpe, best_th = res["sharpe"], th
    print(f"{th:6.4f}  | {res['trades']:6d} | {res['total_return']:7.2%} | {res['sharpe']:6.2f} | {res['max_drawdown']:6.2%} | {res['win_rate']:7.2%}")
print(f"Best: {best_th} (Sharpe={best_sharpe:.2f})")

# =============================================
# 6. TEST
# =============================================
test_preds = model.predict(X_test_s)
test_prices = test_df["close"].values.tolist()
test_signals = []
for i, pred in enumerate(test_preds):
    price = test_prices[i]
    if pred > best_th:
        test_signals.append(("BUY", price))
    elif pred < -best_th:
        test_signals.append(("SELL", price))

res_test = vectorized_backtest(test_prices, test_signals)
print("\n📊 OUT-OF-SAMPLE TEST (2025-2026)")
print(f"Trades: {res_test['num_trades']}")
print(f"Return: {res_test['total_return']:.2%}")
print(f"Sharpe: {res_test['sharpe']:.2f}")
print(f"Max DD: {res_test['max_drawdown']:.2%}")
print(f"Win Rate: {res_test['win_rate']:.2%}")

status = "✅ SUCCESS" if res_test["num_trades"] >= 30 and res_test["sharpe"] > 0.5 else "❌ FAILED"
print(status)
