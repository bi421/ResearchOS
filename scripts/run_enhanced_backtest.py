# scripts/run_enhanced_backtest.py
"""
Enhanced Backtest with Commission, Slippage + ML Forecast
"""
import os
import sys
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cpp_quant_engine", "python"))

from cpp_quant_engine.backend import BacktestEngine
from cpp_quant_engine.models import Candle as CQCandle
from cpp_quant_engine.models import MarketData
from researchos.data_engine.repository import SqliteDatasetRepository

print("=" * 80)
print("ðŸš€ ENHANCED BACKTEST + ML FORECAST")
print("   XAUUSD D1 | Commission: 0.1% | Slippage: 0.05%")
print("=" * 80)

# ============================================================
# 1. Ó¨Ð“Ó¨Ð“Ð”Ó¨Ð› ÐÐ§ÐÐÐ›ÐÐ¥
# ============================================================
print("\nðŸ“‚ 1. Loading data...")
repo = SqliteDatasetRepository("researchos.db")
dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
print(f"   Loaded {dataset.record_count} XAUUSD D1 candles")

# Convert to DataFrame for ML
df = pd.DataFrame([{"timestamp": c.timestamp, "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume if c.volume is not None else 0.0} for c in dataset._records])
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

# Convert to C++ candles
cq_candles = []
for c in dataset._records:
    cq_candles.append(
        CQCandle(
            timestamp=c.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume if c.volume is not None else 0.0,
            timeframe="D1",
        )
    )
print(f"   Converted {len(cq_candles)} candles for backtest engine")

# ============================================================
# 2. BACKTEST WITH COMMISSION & SLIPPAGE
# ============================================================
print("\nðŸ“Š 2. Running backtest with costs...")

INITIAL_CAPITAL = 10000.0
COMMISSION_PCT = 0.001  # 0.1%
SLIPPAGE_PCT = 0.0005  # 0.05%


def sma_uptick_signal(bar_index, history):
    if not history:
        return {"direction": 0, "quantity": 0.0}
    last = history[-1]
    if last["close"] > last["open"]:
        return {"direction": 0, "quantity": 1.0}
    return {"direction": 0, "quantity": 0.0}


engine = BacktestEngine(
    initial_capital=INITIAL_CAPITAL,
    commission_pct=COMMISSION_PCT,
    slippage_pct=SLIPPAGE_PCT,
)
market_data = MarketData(symbol="XAUUSD", candles=cq_candles)
result = engine.run(market_data, signal=sma_uptick_signal, signal_reference="strategy://uptick_v1_cost")

print("\nðŸ“ˆ BACKTEST RESULTS (with costs):")
print("-" * 50)
print(f"   Initial capital:    ${INITIAL_CAPITAL:,.2f}")
print(f"   Commission:         {COMMISSION_PCT*100:.2f}%")
print(f"   Slippage:           {SLIPPAGE_PCT*100:.2f}%")
print("-" * 50)
print(f"   Total bars:         {result.total_bars}")
print(f"   Num trades:         {result.num_trades}")
print(f"   Final equity:       ${result.final_equity:,.2f}")
print(f"   Total return:       {result.total_return_pct:.2f}%")
print(f"   Max drawdown:       {result.max_drawdown_pct:.2f}%")
print(f"   Result hash:        {result.result_hash}")

# Compare with no-cost version (baseline)
baseline_return = 138.80
cost_impact = baseline_return - result.total_return_pct
print(f"\nðŸ“‰ Cost impact:         -{cost_impact:.2f}% vs baseline (no cost)")

# ============================================================
# 3. MACHINE LEARNING FORECAST (XGBoost)
# ============================================================
print("\nðŸ§  3. ML Forecast (XGBoost)")

# Feature engineering
df["return_1"] = df["close"].pct_change()
df["return_2"] = df["close"].pct_change(2)
df["return_5"] = df["close"].pct_change(5)
df["return_10"] = df["close"].pct_change(10)
df["sma_20"] = df["close"].rolling(20).mean()
df["sma_50"] = df["close"].rolling(50).mean()
df["sma_ratio"] = df["sma_20"] / df["sma_50"]
df["volatility"] = df["return_1"].rolling(20).std()
df["high_low"] = (df["high"] - df["low"]) / df["close"]
df["close_open"] = (df["close"] - df["open"]) / df["open"]
df["target"] = (df["close"].shift(-1) > df["open"].shift(-1)).astype(int)
df.dropna(inplace=True)

print(f"   Features generated: {len(df)} rows")

try:
    import xgboost as xgb
    from sklearn.metrics import accuracy_score

    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("   âš ï¸ XGBoost not installed. Install with: pip install xgboost")

if XGB_AVAILABLE and len(df) > 50:
    features = ["return_1", "return_2", "return_5", "return_10", "sma_ratio", "volatility", "high_low", "close_open"]
    split = int(len(df) * 0.8)
    train, test = df.iloc[:split], df.iloc[split:]

    model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42, use_label_encoder=False, eval_metric="logloss")
    model.fit(train[features], train["target"])
    y_pred = model.predict(test[features])
    accuracy = accuracy_score(test["target"], y_pred)

    print("\nðŸ“Š ML Model Performance:")
    print(f"   Accuracy:     {accuracy:.2%}")
    print(f"   Test samples: {len(test)}")

    # Feature importance
    imp = pd.DataFrame({"feature": features, "importance": model.feature_importances_}).sort_values("importance", ascending=False)
    print("\nðŸ“ˆ Feature Importance:")
    for _, row in imp.iterrows():
        print(f"   {row['feature']}: {row['importance']:.3f}")

    # Latest forecast
    latest = df.iloc[-1:]
    latest_prob = model.predict_proba(latest[features])[0, 1]
    latest_pred = 1 if latest_prob > 0.5 else 0
    signal = "BUY" if latest_pred == 1 else "SELL/NEUTRAL"

    print("\nðŸŽ¯ Latest Forecast (next day):")
    print(f"   UP probability: {latest_prob:.1%}")
    print(f"   Signal:         {signal}")

    # SMA signal for comparison
    sma_signal = 1 if df["sma_20"].iloc[-1] > df["sma_50"].iloc[-1] else 0
    print(f"\nðŸ“Š SMA(20,50) signal: {'BUY' if sma_signal == 1 else 'SELL/NEUTRAL'}")

else:
    print("   âŒ XGBoost not available or insufficient data")

# ============================================================
# 4. ÐÐ­Ð“Ð”Ð¡Ð­Ð Ð”Ò®Ð“ÐÐ­Ð›Ð¢
# ============================================================
print("\n" + "=" * 80)
print("ðŸ“‹ ÐÐ­Ð“Ð”Ð¡Ð­Ð Ð”Ò®Ð“ÐÐ­Ð›Ð¢")
print("=" * 80)

print(
    f"""
âœ… Backtest with costs:
   - Return: {result.total_return_pct:.2f}%
   - Trades: {result.num_trades}
   - Cost impact: -{cost_impact:.2f}%

âœ… ML Forecast:
   - Accuracy: {accuracy:.2%} (if XGB available)
   - Next day signal: {signal if XGB_AVAILABLE else 'N/A'}

ðŸ“Œ Recommendation:
   Based on the combination of backtest and ML forecast,
   consider {'BUY' if latest_pred == 1 and result.total_return_pct > 0 else 'AVOID/WAIT'}.
"""
)
