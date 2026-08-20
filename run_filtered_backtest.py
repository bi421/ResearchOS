import pandas as pd
import numpy as np
import glob
import sys
sys.path.insert(0, ".")
from researchos.ml_engine.features import create_features
from researchos.ml_engine.filters import apply_noise_filter
from researchos.quant_engine.backtest import BacktestEngine
from researchos.ml_engine.strategy import MLStrategy, Signal
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

print("Loading data...")
files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
df = pd.concat([pd.read_csv(f, sep=";", header=None,
                            names=["datetime","open","high","low","close","volume"])
                for f in files], ignore_index=True)
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
df = df.set_index("datetime")

# Resample to 4h
df_h = df.resample("4h").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
print(f"Data loaded: {len(df_h)} bars (4h)")

# ⭐ ШИНЭ: Noise Filter хэрэглэх
df_h = apply_noise_filter(df_h)
print(f"Trending & Low Volatility periods: {df_h['valid_trade'].sum()} / {len(df_h)} ({df_h['valid_trade'].mean():.2%})")

# Filter-үүдийг feature болгон нэмэх (adx, price_vs_trend, valid_trade гэх мэт)
# Valid_trade нь стратегид дохио өгөх эсэхийг шалгах gate болно.

# Train/Val/Test split (time order)
dates = df_h.index
split1 = int(len(dates) * 0.7)
split2 = int(len(dates) * 0.85)
train_df = df_h.iloc[:split1]
val_df = df_h.iloc[split1:split2]
test_df = df_h.iloc[split2:]

def prepare_features(df):
    # create_features дуудаж, дараа нь filter-үүдийг нэмэх
    df_feat = create_features(df)
    if df_feat.empty:
        return None
    # Filter-үүдийг feature болгон нэмэх
    df_feat["adx"] = df["adx"]
    df_feat["price_vs_trend"] = df["price_vs_trend"]
    df_feat["valid_trade"] = df["valid_trade"].astype(int)  # Boolean-ыг int болгох
    return df_feat

train_feat = prepare_features(train_df)
val_feat = prepare_features(val_df)
test_feat = prepare_features(test_df)

feature_cols = [col for col in train_feat.columns if col not in ["target", "datetime"]]
X_train, y_train = train_feat[feature_cols].values, train_feat["target"].values
X_val, y_val = val_feat[feature_cols].values, val_feat["target"].values
X_test, y_test = test_feat[feature_cols].values, test_feat["target"].values

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val)
X_test_s = scaler.transform(X_test)

model = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=6, random_state=42, use_label_encoder=False, eval_metric='logloss')
model.fit(X_train_s, y_train)
print(f"Train Acc: {model.score(X_train_s, y_train):.2%}, Val Acc: {model.score(X_val_s, y_val):.2%}")

# ⭐ ШИНЭ: Гагнуурын дохио үүсгэх функц (Noise Filter gate нэмсэн)
def get_signals(df, probs, threshold):
    signals = []
    # valid_trade нь True байх ёстой, ADX > 25, Volatility хэвийн байх ёстой
    for i, idx in enumerate(df.index):
        if i < len(probs):
            prob = probs[i]
            price = df.loc[idx, 'close']
            valid = df.loc[idx, 'valid_trade']  # Noise Filter gate
            if valid and prob > threshold:
                signals.append(Signal("BUY", price))
            elif valid and prob < (1 - threshold):
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

# Test
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
