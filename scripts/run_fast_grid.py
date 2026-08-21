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
df_h = df.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
print(f"Data loaded: {len(df_h)} bars")

print("Creating features (once)...")
df_feat = create_features(df_h)
if df_feat.empty:
    print("No features!")
    exit()
prices = df_h["close"].tolist()

print("Training model (once)...")
model, scaler, metrics = train_model(df_feat, model_type="random_forest", test_size=0.3)
feature_names = metrics["feature_names"]

print("Calculating probabilities (once)...")
X_all = df_feat[feature_names].values
X_scaled = scaler.transform(X_all)
probs = model.predict_proba(X_scaled)[:, 1]


# Fast strategy – кэшлэгдсэн өгөгдөл ашигладаг
class FastMLStrategy(MLStrategy):
    def generate_signals(self, prices):
        # Өгөгдсөн prices-г үл тоомсорлож, өмнө тооцоолсон df_feat болон probs-г ашиглана.
        signals = []
        for i, idx in enumerate(df_feat.index):
            if i < len(probs):
                prob = probs[i]
                price = df_feat.loc[idx, "close"]
                if prob > self.threshold:
                    signals.append(MLStrategy.Signal("BUY", price))
                elif prob < (1 - self.threshold):
                    signals.append(MLStrategy.Signal("SELL", price))
        return signals


engine = BacktestEngine()
thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]

print("\n🔥 FAST GRID SEARCH (model trained once)\n")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")

for th in thresholds:
    strategy = FastMLStrategy(model, scaler, feature_names, threshold=th)
    result = engine.run(prices, strategy)
    print(
        f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%}"
    )
