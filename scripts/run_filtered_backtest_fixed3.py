import pandas as pd
import numpy as np
import glob
import sys

sys.path.insert(0, ".")
from researchos.quant_engine.backtest import BacktestEngine
from researchos.ml_engine.strategy import Signal
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

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


# -------------------------------
# NOISE FILTER (босгыг маш сулруулсан)
# -------------------------------
def add_filters(df):
    df = df.copy()
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    # ADX (14) - босгыг 15 болгон бууруулсан
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    up_move = high - high.shift()
    down_move = low.shift() - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    plus_dm_smooth = pd.Series(plus_dm).rolling(14).mean()
    minus_dm_smooth = pd.Series(minus_dm).rolling(14).mean()
    di_plus = 100 * (plus_dm_smooth / atr)
    di_minus = 100 * (minus_dm_smooth / atr)
    dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus)
    adx = dx.rolling(14).mean()
    df["adx"] = adx

    # Volatility regime – босгыг 2.5 болгон цааш сулруулсан
    returns = close.pct_change()
    vol = returns.rolling(50).std()
    vol_z = (vol - vol.mean()) / vol.std()
    df["vol_filter"] = vol_z < 2.5

    # Trend filter – босгыг 15 болгон бууруулсан
    df["trend_filter"] = df["adx"] > 15

    df["valid_trade"] = df["vol_filter"] & df["trend_filter"]
    return df


df_h = add_filters(df_h)
valid_count = df_h["valid_trade"].sum()
print(f"Valid trade periods: {valid_count} / {len(df_h)} ({df_h['valid_trade'].mean():.2%})")

# valid_trade 0 байвал бүх мөрийг хүчинтэй гэж үзнэ
if valid_count == 0:
    print("⚠️ No valid periods. Enabling gate for ALL data.")
    df_h["valid_trade"] = True


# -------------------------------
# FEATURES (техник үзүүлэлтүүд)
# -------------------------------
def make_features(df):
    df = df.copy()
    close = df["close"]
    # Лаг өгөөж
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
    # ADX болон price_vs_trend (filter-ээс авсан)
    df["adx"] = df["adx"]
    df["price_vs_trend"] = df["price_vs_trend"] if "price_vs_trend" in df.columns else 0
    # Target
    df["target"] = (close.shift(-1) > close).astype(int)

    # Бүх NaN-г 0-ээр дүүргэх (эхний мөрүүд болон inf-г арилгах)
    df = df.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    return df


train_df = df_h.iloc[: int(len(df_h) * 0.7)]
val_df = df_h.iloc[int(len(df_h) * 0.7) : int(len(df_h) * 0.85)]
test_df = df_h.iloc[int(len(df_h) * 0.85) :]

train_feat = make_features(train_df)
val_feat = make_features(val_df)
test_feat = make_features(test_df)

# valid_trade-г feature-аас хасна (зөвхөн gate-д хэрэглэнэ)
feature_cols = [c for c in train_feat.columns if c not in ["target", "datetime", "valid_trade"]]
X_train = train_feat[feature_cols].values
y_train = train_feat["target"].values
X_val = val_feat[feature_cols].values
y_val = val_feat["target"].values
X_test = test_feat[feature_cols].values
y_test = test_feat["target"].values

print(f"Train samples: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

if X_train.shape[0] == 0:
    print("❌ No training data. Exiting.")
    sys.exit(1)

# Scale
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val) if X_val.shape[0] > 0 else np.array([])
X_test_s = scaler.transform(X_test) if X_test.shape[0] > 0 else np.array([])

# XGBoost
model = XGBClassifier(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=6,
    random_state=42,
    use_label_encoder=False,
    eval_metric="logloss",
)
model.fit(X_train_s, y_train)
print(f"Train Acc: {model.score(X_train_s, y_train):.2%}")
if X_val.shape[0] > 0:
    print(f"Val Acc: {model.score(X_val_s, y_val):.2%}")


# Signals generation with gate
def get_signals(df, probs, threshold):
    signals = []
    for i, idx in enumerate(df.index):
        if i < len(probs):
            if df.loc[idx, "valid_trade"]:
                prob = probs[i]
                price = df.loc[idx, "close"]
                if prob > threshold:
                    signals.append(Signal("BUY", price))
                elif prob < (1 - threshold):
                    signals.append(Signal("SELL", price))
    return signals


engine = BacktestEngine()
thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]
best_sharpe = -999
best_th = 0.55

print("\n🔍 VALIDATION GRID SEARCH")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")
if X_val.shape[0] > 0:
    val_probs = model.predict_proba(X_val_s)[:, 1]
    for th in thresholds:
        signals = get_signals(val_df, val_probs, th)

        class TempStrategy:
            def generate_signals(self, prices):
                return signals

        result = engine.run(val_df["close"].tolist(), TempStrategy())
        if result.num_trades >= 20 and result.sharpe_ratio > best_sharpe:
            best_sharpe = result.sharpe_ratio
            best_th = th
        print(
            f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%}"
        )
    print(f"Best threshold: {best_th}")
else:
    print("No validation data – using default threshold 0.55")

# Test
if X_test.shape[0] > 0:
    test_probs = model.predict_proba(X_test_s)[:, 1]
    test_signals = get_signals(test_df, test_probs, best_th)

    class TestStrategy:
        def generate_signals(self, prices):
            return test_signals

    test_result = engine.run(test_df["close"].tolist(), TestStrategy())
    print("\n📊 OUT-OF-SAMPLE TEST")
    print(f"Trades: {test_result.num_trades}")
    print(f"Return: {test_result.total_return:.2%}")
    print(f"Sharpe: {test_result.sharpe_ratio:.2f}")
    print(f"Max DD: {test_result.max_drawdown:.2%}")
    print(f"Win Rate: {test_result.win_rate:.2%}")

    if test_result.num_trades >= 30 and test_result.sharpe_ratio > 0.5:
        print("✅ SUCCESS: Filtered strategy shows positive out-of-sample performance.")
    else:
        print("❌ FAILED: Filter helps, but features still insufficient.")
else:
    print("No test data!")
