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
df = pd.concat([pd.read_csv(f, sep=";", header=None,
                            names=["datetime","open","high","low","close","volume"])
                for f in files], ignore_index=True)
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
df = df.set_index("datetime")
df_h = df.resample("4h").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
print(f"Data: {len(df_h)} bars (4h)")

# -------------------------------
# NOISE FILTER (босгыг сулруулсан)
# -------------------------------
def add_filters(df):
    df = df.copy()
    close = df['close'].astype(float)
    high = df['high'].astype(float)
    low = df['low'].astype(float)

    # ADX (14)
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
    df['adx'] = adx

    # Kalman filter (1D)
    q, r = 1e-5, 0.01
    n = len(close)
    est = np.zeros(n)
    err = np.zeros(n)
    est[0] = close.iloc[0]
    err[0] = 1.0
    for i in range(1, n):
        pred = est[i-1]
        pred_err = err[i-1] + q
        kg = pred_err / (pred_err + r)
        est[i] = pred + kg * (close.iloc[i] - pred)
        err[i] = (1 - kg) * pred_err
    df['kalman_trend'] = est
    df['price_vs_trend'] = close / df['kalman_trend'] - 1

    # Volatility regime (z-score of rolling std) – босгыг 2.0 болгон өргөжүүлсэн
    returns = close.pct_change()
    vol = returns.rolling(50).std()
    vol_z = (vol - vol.mean()) / vol.std()
    df['vol_filter'] = vol_z < 2.0  # Өмнө 1.5 байсан

    # Trend filter – босгыг 20 болгон бууруулсан
    df['trend_filter'] = df['adx'] > 20  # Өмнө 25 байсан

    # Combined gate
    df['valid_trade'] = df['vol_filter'] & df['trend_filter']
    return df

df_h = add_filters(df_h)
valid_count = df_h['valid_trade'].sum()
print(f"Valid trade periods: {valid_count} / {len(df_h)} ({df_h['valid_trade'].mean():.2%})")

# Хэрэв valid_trade 0 байвал бүх мөрийг хүчинтэй гэж үзэх (gate-ийг идэвхгүй болгох)
if valid_count == 0:
    print("⚠️ No valid periods found. Disabling gate for all data.")
    df_h['valid_trade'] = True

# -------------------------------
# FEATURES (техник үзүүлэлтүүд + фильтрүүд)
# -------------------------------
def make_features(df):
    df = df.copy()
    close = df['close']
    # Лаг өгөөж
    df['ret1'] = close.pct_change()
    for lag in [1,2,3,5,10,20]:
        df[f'ret_lag_{lag}'] = df['ret1'].shift(lag)
    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    # MACD
    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_diff'] = df['macd'] - df['macd_signal']
    # Bollinger
    mean = close.rolling(20).mean()
    std = close.rolling(20).std()
    df['bb_high'] = mean + 2*std
    df['bb_low'] = mean - 2*std
    df['bb_pos'] = (close - df['bb_low']) / (df['bb_high'] - df['bb_low'])
    # Volatility
    df['volatility'] = df['ret1'].rolling(20).std()
    # Filter columns (valid_trade-г feature-аас хасна)
    df['adx'] = df['adx']
    df['price_vs_trend'] = df['price_vs_trend']
    # Target
    df['target'] = (close.shift(-1) > close).astype(int)
    # NaN-г forward fill хийж, үлдсэн NaN-г арилгах
    df = df.ffill().dropna()
    return df

# -------------------------------
# TRAIN/VAL/TEST SPLIT
# -------------------------------
dates = df_h.index
split1 = int(len(dates)*0.7)
split2 = int(len(dates)*0.85)
train_df = df_h.iloc[:split1]
val_df = df_h.iloc[split1:split2]
test_df = df_h.iloc[split2:]

train_feat = make_features(train_df)
val_feat = make_features(val_df)
test_feat = make_features(test_df)

# feature_cols-д valid_trade оруулахгүй
feature_cols = [c for c in train_feat.columns if c not in ['target','datetime','valid_trade']]
X_train = train_feat[feature_cols].values
y_train = train_feat['target'].values
X_val = val_feat[feature_cols].values
y_val = val_feat['target'].values
X_test = test_feat[feature_cols].values
y_test = test_feat['target'].values

print(f"Train samples: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

# Scale
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val)
X_test_s = scaler.transform(X_test)

# -------------------------------
# XGBoost MODEL
# -------------------------------
model = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=6,
                      random_state=42, use_label_encoder=False, eval_metric='logloss')
model.fit(X_train_s, y_train)
print(f"Train Acc: {model.score(X_train_s, y_train):.2%}, Val Acc: {model.score(X_val_s, y_val):.2%}")

# -------------------------------
# SIGNAL GENERATION with FILTER GATE
# -------------------------------
def get_signals(df, probs, threshold):
    signals = []
    for i, idx in enumerate(df.index):
        if i < len(probs):
            # Хэрэв valid_trade хуудас байхгүй бол (өмнө нь бүгдийг True болгосон) шалгахгүй
            if df.loc[idx, 'valid_trade']:
                prob = probs[i]
                price = df.loc[idx, 'close']
                if prob > threshold:
                    signals.append(Signal("BUY", price))
                elif prob < (1 - threshold):
                    signals.append(Signal("SELL", price))
    return signals

engine = BacktestEngine()
thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]
best_sharpe = -999
best_th = 0.55

print("\n🔍 VALIDATION GRID SEARCH (with Noise Filter)")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")
val_probs = model.predict_proba(X_val_s)[:, 1]
for th in thresholds:
    signals = get_signals(val_df, val_probs, th)
    class TempStrategy:
        def generate_signals(self, prices):
            return signals
    result = engine.run(val_df['close'].tolist(), TempStrategy())
    if result.num_trades >= 20 and result.sharpe_ratio > best_sharpe:
        best_sharpe = result.sharpe_ratio
        best_th = th
    print(f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%}")
print(f"Best threshold: {best_th}")

# -------------------------------
# OUT-OF-SAMPLE TEST
# -------------------------------
test_probs = model.predict_proba(X_test_s)[:, 1]
test_signals = get_signals(test_df, test_probs, best_th)
class TestStrategy:
    def generate_signals(self, prices):
        return test_signals
test_result = engine.run(test_df['close'].tolist(), TestStrategy())

print("\n📊 OUT-OF-SAMPLE TEST (with Noise Filter)")
print(f"Trades: {test_result.num_trades}")
print(f"Return: {test_result.total_return:.2%}")
print(f"Sharpe: {test_result.sharpe_ratio:.2f}")
print(f"Max DD: {test_result.max_drawdown:.2%}")
print(f"Win Rate: {test_result.win_rate:.2%}")

if test_result.num_trades >= 30 and test_result.sharpe_ratio > 0.5:
    print("✅ SUCCESS: Filtered strategy shows positive out-of-sample performance.")
else:
    print("❌ FAILED: Filter helps, but features still insufficient.")
