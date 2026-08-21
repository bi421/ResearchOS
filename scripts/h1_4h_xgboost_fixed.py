import pandas as pd
import glob
import sys

sys.path.insert(0, ".")
from researchos.ml_engine.features import create_features
from researchos.quant_engine.backtest import BacktestEngine
from researchos.ml_engine.strategy import Signal  # Signal-г импортлох
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

# 4h resample
df_h = (
    df.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
)
print(f"Data loaded: {len(df_h)} bars (4h)")

# Цагийн шинжүүд
df_h["hour"] = df_h.index.hour
df_h["dayofweek"] = df_h.index.dayofweek
df_h["month"] = df_h.index.month

# Train/val/test split
dates = df_h.index
split1 = int(len(dates) * 0.7)
split2 = int(len(dates) * 0.85)
train_df = df_h.iloc[:split1]
val_df = df_h.iloc[split1:split2]
test_df = df_h.iloc[split2:]

print(f"Train: {len(train_df)} bars, Val: {len(val_df)}, Test: {len(test_df)}")


# Features generation
def prepare_features(df):
    df_feat = create_features(df)
    if df_feat.empty:
        return None
    # Цагийн шинжүүдийг нэмэх
    df_feat["hour"] = df["hour"]
    df_feat["dayofweek"] = df["dayofweek"]
    df_feat["month"] = df["month"]
    return df_feat


train_feat = prepare_features(train_df)
val_feat = prepare_features(val_df)
test_feat = prepare_features(test_df)

if train_feat is None or train_feat.empty:
    print("Train features empty! Check create_features.")
    sys.exit(1)

# Feature болон target-г ялгах
feature_cols = [col for col in train_feat.columns if col not in ["target", "datetime"]]
X_train = train_feat[feature_cols].values
y_train = train_feat["target"].values

X_val = val_feat[feature_cols].values if val_feat is not None else None
y_val = val_feat["target"].values if val_feat is not None else None

X_test = test_feat[feature_cols].values if test_feat is not None else None
y_test = test_feat["target"].values if test_feat is not None else None

# StandardScaler (fit on train only)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
if X_val is not None:
    X_val_scaled = scaler.transform(X_val)
if X_test is not None:
    X_test_scaled = scaler.transform(X_test)

# XGBoost модел сургах
model = XGBClassifier(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=6,
    random_state=42,
    use_label_encoder=False,
    eval_metric="logloss",
)
model.fit(X_train_scaled, y_train)

train_acc = model.score(X_train_scaled, y_train)
if X_val is not None:
    val_acc = model.score(X_val_scaled, y_val)
else:
    val_acc = None
print(
    f"Train accuracy: {train_acc:.2%}, Val accuracy: {val_acc:.2%}"
    if val_acc
    else f"Train accuracy: {train_acc:.2%}"
)


# Дохио үүсгэх функц (Signal-г шууд ашиглана)
def get_signals_from_probs(df, probs, threshold):
    signals = []
    for i, idx in enumerate(df.index):
        if i < len(probs):
            prob = probs[i]
            price = df.loc[idx, "close"]
            if prob > threshold:
                signals.append(Signal("BUY", price))
            elif prob < (1 - threshold):
                signals.append(Signal("SELL", price))
    return signals


# Validation дээр grid search
thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]
engine = BacktestEngine()
best_sharpe = -999
best_th = 0.55

if X_val is not None:
    val_probs = model.predict_proba(X_val_scaled)[:, 1]
    print("\n🔍 VALIDATION GRID SEARCH")
    print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
    print("----------|--------|---------|--------|--------|--------")
    for th in thresholds:
        signals = get_signals_from_probs(val_df, val_probs, th)

        class TempStrategy:
            def generate_signals(self, prices):
                return signals

        result = engine.run(val_df["close"].tolist(), TempStrategy())
        if result.num_trades >= 30 and result.sharpe_ratio > best_sharpe:
            best_sharpe = result.sharpe_ratio
            best_th = th
        print(
            f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%}"
        )
    print(f"\n✅ Best threshold: {best_th} (Sharpe={best_sharpe:.2f})")
else:
    best_th = 0.55

# Test дээр эцсийн шалгалт
test_probs = model.predict_proba(X_test_scaled)[:, 1]
signals_test = get_signals_from_probs(test_df, test_probs, best_th)


class FinalStrategy:
    def generate_signals(self, prices):
        return signals_test


test_result = engine.run(test_df["close"].tolist(), FinalStrategy())

print("\n📊 OUT-OF-SAMPLE TEST PERFORMANCE")
print(f"Threshold: {best_th}")
print(f"Trades: {test_result.num_trades}")
print(f"Return: {test_result.total_return:.2%}")
print(f"Sharpe: {test_result.sharpe_ratio:.2f}")
print(f"Max DD: {test_result.max_drawdown:.2%}")
print(f"Win Rate: {test_result.win_rate:.2%}")

print("\n==================================================")
if test_result.num_trades >= 30 and test_result.sharpe_ratio > 0.5:
    print("✅ Strategy shows positive out-of-sample performance with sufficient trades.")
else:
    print("❌ Strategy failed out-of-sample test – likely overfitting.")
