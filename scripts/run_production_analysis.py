# scripts/run_production_analysis.py
"""
PRODUCTION ANALYSIS Ã¢â‚¬â€œ ÃÂÃ‘ÂÃÂ³ ÃÂºÃÂ¾ÃÂ´, ÃÂ±Ã’Â¯Ã‘â€¦ Ã‘Ë†ÃÂ¸ÃÂ½ÃÂ¶ÃÂ¸ÃÂ»ÃÂ³Ã‘ÂÃ‘Â
- Backtest (C++ + Python verification)
- Cost impact analysis
- ML Forecast (XGBoost with tuning & CV)
- Unified decision with reliability thresholds
"""
import os
import sys
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

# ============================================================
# PATH SETUP
# ============================================================
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cpp_quant_engine", "python"))

from cpp_quant_engine.backend import BacktestEngine
from cpp_quant_engine.models import Candle as CQCandle
from cpp_quant_engine.models import MarketData
from researchos.data_engine.repository import SqliteDatasetRepository

print("=" * 80)
print("Ã°Å¸Å¡â‚¬ PRODUCTION ANALYSIS")
print("   Integrated: Backtest (C++/Python) + ML Forecast + Decision")
print("=" * 80)

INITIAL_CAPITAL = 10000.0
COMMISSION_PCT = 0.001
SLIPPAGE_PCT = 0.0005

# ============================================================
# 1. Ã“Â¨Ãâ€œÃ“Â¨Ãâ€œÃâ€Ã“Â¨Ãâ€º ÃÂÃÂ§ÃÂÃÂÃâ€ºÃÂÃÂ¥
# ============================================================
print("\nÃ°Å¸â€œâ€š 1. Loading data...")
repo = SqliteDatasetRepository("researchos.db")
dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
print(f"   Loaded {dataset.record_count} XAUUSD D1 candles")

# Pandas DataFrame
df = pd.DataFrame([{"timestamp": c.timestamp, "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume if c.volume is not None else 0.0} for c in dataset._records])
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

# C++ candles
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

# ============================================================
# 2. FEATURE ENGINEERING (ML + Analysis)
# ============================================================
print("\nÃ°Å¸â€œË† 2. Feature Engineering...")


def add_technical_features(df):
    df = df.copy()
    # Returns
    for p in [1, 2, 5, 10, 20]:
        df[f"ret_{p}"] = df["close"].pct_change(p)

    # SMAs
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["sma_ratio"] = df["sma_20"] / df["sma_50"]

    # Volatility
    df["volatility"] = df["ret_1"].rolling(20).std()

    # Price features
    df["hl_ratio"] = (df["high"] - df["low"]) / df["close"]
    df["co_ratio"] = (df["close"] - df["open"]) / df["open"]

    # RSI (14)
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Bollinger Bands
    bb_mid = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_high"] = bb_mid + 2 * bb_std
    df["bb_low"] = bb_mid - 2 * bb_std
    df["bb_pct"] = (df["close"] - df["bb_low"]) / (df["bb_high"] - df["bb_low"])

    # ATR
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = ranges.rolling(14).mean()

    # Target: Next day close > open
    df["target"] = (df["close"].shift(-1) > df["open"].shift(-1)).astype(int)

    df.dropna(inplace=True)
    return df


df_ml = add_technical_features(df)
print(f"   Features ready: {len(df_ml)} rows, {len(df_ml.columns)} columns")

# Features list
FEATURES = ["ret_1", "ret_2", "ret_5", "ret_10", "ret_20", "sma_ratio", "volatility", "hl_ratio", "co_ratio", "rsi", "macd", "macd_hist", "bb_pct", "atr"]

# ============================================================
# 3. BACKTEST Ã¢â‚¬â€œ C++ ENGINE (with costs)
# ============================================================
print("\nÃ¢Å¡â„¢Ã¯Â¸Â 3. C++ Backtest (with costs)...")


def uptick_signal(bar_index, history):
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
result = engine.run(market_data, signal=uptick_signal, signal_reference="strategy://uptick_v1")

print("\nÃ°Å¸â€œÅ  C++ Backtest Results:")
print("-" * 50)
print(f"   Trades:        {result.num_trades}")
print(f"   Final Equity:  ${result.final_equity:,.2f}")
print(f"   Return:        {result.total_return_pct:.2f}%")
print(f"   Max DD:        {result.max_drawdown_pct:.2f}%")
print(f"   Result hash:   {result.result_hash}")

# ============================================================
# 4. BACKTEST Ã¢â‚¬â€œ PYTHON VERIFICATION (to see trades)
# ============================================================
print("\nÃ°Å¸ÂÂ 4. Python Backtest (Verification + Trade Log)...")


def run_python_backtest(df, signal_func, capital, comm_pct, slippage_pct):
    cash = capital
    position = 0  # number of units
    trades = []

    for i in range(1, len(df)):
        current_open = df["open"].iloc[i]

        # Signal based on previous close vs current open? Standard: previous close vs previous open?
        # Original signal uses history[-1] which is previous candle.
        # Let's simulate correctly.
        prev_candle = {"open": df["open"].iloc[i - 1], "high": df["high"].iloc[i - 1], "low": df["low"].iloc[i - 1], "close": df["close"].iloc[i - 1], "volume": df["volume"].iloc[i - 1] if "volume" in df else 0}
        sig = signal_func(i, [prev_candle])

        if sig["quantity"] > 0 and position == 0:
            # Buy at open with slippage
            entry = current_open * (1 + slippage_pct)
            # Use all cash
            shares = cash / entry
            # Commission
            cost = entry * shares * comm_pct
            cash -= cost
            position = shares
            cash = 0  # all in
            trades.append({"type": "BUY", "date": df.index[i], "price": entry, "shares": shares})

        elif sig["quantity"] == 0 and position > 0:
            # Sell at open with slippage
            exit_price = current_open * (1 - slippage_pct)
            # Commission
            cost = exit_price * position * comm_pct
            cash = position * exit_price - cost
            position = 0
            trades.append({"type": "SELL", "date": df.index[i], "price": exit_price, "shares": shares})

    # Close position at last close if still holding
    if position > 0:
        exit_price = df["close"].iloc[-1] * (1 - slippage_pct)
        cost = exit_price * position * comm_pct
        cash = position * exit_price - cost
        position = 0

    final_equity = cash
    total_return = (final_equity / capital - 1) * 100
    return trades, final_equity, total_return


py_trades, py_final, py_return = run_python_backtest(df, uptick_signal, INITIAL_CAPITAL, COMMISSION_PCT, SLIPPAGE_PCT)

print(f"   Python Trades: {len(py_trades)//2} (Buy/Sell pairs)")
print(f"   Return:        {py_return:.2f}%")

# Show first 5 trades
print("\nÃ°Å¸â€œâ€¹ Python Trade Log (first 5):")
for t in py_trades[:10]:
    print(f"   {t['date'].strftime('%Y-%m-%d')} {t['type']:4} @ {t['price']:.2f}")

# ============================================================
# 5. MACHINE LEARNING (XGBoost with Tuning & CV)
# ============================================================
print("\nÃ°Å¸Â§Â  5. ML Forecast (XGBoost)...")

try:
    import xgboost as xgb
    from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("   Ã¢ÂÅ’ XGBoost not installed.")

ML_ACCURACY = 0.0
ML_SIGNAL = "NEUTRAL"
ML_PROB = 0.5

if XGB_AVAILABLE and len(df_ml) > 100:
    X = df_ml[FEATURES]
    y = df_ml["target"]

    # TimeSeries Split (no look-ahead)
    tscv = TimeSeriesSplit(n_splits=5)

    # Hyperparameter tuning
    param_dist = {"n_estimators": [50, 100, 200], "max_depth": [2, 3, 5], "learning_rate": [0.01, 0.05, 0.1], "subsample": [0.7, 0.8, 1.0], "colsample_bytree": [0.7, 0.8, 1.0]}

    model = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric="logloss")

    # Randomized search
    search = RandomizedSearchCV(model, param_dist, n_iter=10, cv=tscv, scoring="accuracy", n_jobs=-1, random_state=42)
    search.fit(X, y)
    best_model = search.best_estimator_
    best_score = search.best_score_

    print(f"   Best CV Accuracy: {best_score:.2%}")
    print(f"   Best Params: {search.best_params_}")

    # Latest prediction
    latest = X.iloc[-1:].copy()
    prob = best_model.predict_proba(latest)[0, 1]
    pred = 1 if prob > 0.5 else 0

    ML_ACCURACY = best_score
    ML_PROB = prob
    ML_SIGNAL = "BUY" if pred == 1 else "NEUTRAL/SELL"

    # Feature importance
    imp = pd.DataFrame({"feature": FEATURES, "importance": best_model.feature_importances_}).sort_values("importance", ascending=False)
    print("\nÃ°Å¸â€œË† Feature Importance (Top 5):")
    for _, row in imp.head(5).iterrows():
        print(f"   {row['feature']}: {row['importance']:.3f}")

else:
    print("   Ã¢Å¡Â Ã¯Â¸Â XGBoost not available or insufficient data.")

# ============================================================
# 6. UNIFIED DECISION WITH RELIABILITY THRESHOLDS
# ============================================================
print("\n" + "=" * 80)
print("Ã°Å¸â€œâ€¹ 6. ÃÂÃÂ­Ãâ€œÃâ€ÃÂ¡ÃÂ­ÃÂ ÃÂ¨ÃËœÃâ„¢Ãâ€Ãâ€™ÃÂ­ÃÂ  (Unified Decision)")
print("=" * 80)

# Reliability thresholds
MIN_TRADES = 20
MIN_ML_ACC = 0.55

cpp_trades = result.num_trades
cpp_return = result.total_return_pct

is_backtest_reliable = cpp_trades >= MIN_TRADES
is_ml_reliable = ML_ACCURACY >= MIN_ML_ACC

print("\nÃ°Å¸â€Â ÃÂÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬Ã‘â€šÃÂ°ÃÂ¹ ÃÂ±ÃÂ°ÃÂ¹ÃÂ´ÃÂ»Ã‘â€¹ÃÂ½ Ã‘Ë†ÃÂ°ÃÂ»ÃÂ³ÃÂ°ÃÂ»Ã‘â€š:")
print(f"   Backtest ÃÂ°Ã‘â‚¬ÃÂ¸ÃÂ»ÃÂ³ÃÂ°ÃÂ°ÃÂ½Ã‘â€¹ Ã‘â€šÃÂ¾ÃÂ¾: {cpp_trades} (ÃÂ±ÃÂ¾Ã‘ÂÃÂ³ÃÂ¾: {MIN_TRADES}) -> {'Ã¢Å“â€¦' if is_backtest_reliable else 'Ã¢ÂÅ’'}")
print(f"   ML ÃÂ½ÃÂ°Ã‘â‚¬ÃÂ¸ÃÂ¹ÃÂ²Ã‘â€¡ÃÂ»ÃÂ°ÃÂ»: {ML_ACCURACY:.2%} (ÃÂ±ÃÂ¾Ã‘ÂÃÂ³ÃÂ¾: {MIN_ML_ACC:.0%}) -> {'Ã¢Å“â€¦' if is_ml_reliable else 'Ã¢ÂÅ’'}")

# Decision Logic
decision = "ÃÂÃ‘ÂÃÂ¼Ã‘ÂÃÂ»Ã‘â€š Ã‘Ë†ÃÂ¸ÃÂ½ÃÂ¶ÃÂ¸ÃÂ»ÃÂ³Ã‘ÂÃ‘Â Ã‘Ë†ÃÂ°ÃÂ°Ã‘â‚¬ÃÂ´ÃÂ»ÃÂ°ÃÂ³ÃÂ°Ã‘â€šÃÂ°ÃÂ¹"
action_score = 0
reason = ""

if not is_backtest_reliable and not is_ml_reliable:
    decision = "Ã¢â€ºâ€ ÃÂ¥ÃÂ£Ãâ€ÃÂÃâ€ºÃâ€ÃÂÃÂ¥Ãâ€œÃ’Â®Ãâ„¢ Ãâ€˜ÃÂÃâ„¢ÃÂ¥ (AVOID)"
    reason = "Backtest ÃÂ±ÃÂ¾ÃÂ»ÃÂ¾ÃÂ½ ML ÃÂ°ÃÂ»Ã‘Å’ ÃÂ°ÃÂ»Ã‘Å’ ÃÂ½Ã‘Å’ ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬ÃÂ³Ã’Â¯ÃÂ¹ ÃÂ±ÃÂ°ÃÂ¹ÃÂ½ÃÂ°."
elif is_backtest_reliable and is_ml_reliable:
    # Both reliable: Weighted decision
    # Backtest weight: 0.6 (since it's historical realized), ML weight: 0.4
    weighted_score = (cpp_return / 100) * 0.6 + (ML_PROB * 2 - 1) * 0.4
    if weighted_score > 0.3 and ML_PROB > 0.55:
        decision = "Ã¢Å“â€¦ ÃÂ¥ÃÂ£Ãâ€ÃÂÃâ€ºÃâ€ÃÂÃÂ¥ (BUY)"
        reason = f"Backtest ({cpp_return:.1f}%) ÃÂ±ÃÂ¾ÃÂ»ÃÂ¾ÃÂ½ ML ({ML_PROB:.0%}%) Ã‘ÂÃÂµÃ‘â‚¬Ã‘ÂÃÂ³ ÃÂ´ÃÂ¾Ã‘â€¦ÃÂ¸ÃÂ¾."
    elif weighted_score < -0.1:
        decision = "Ã¢ÂÅ’ ÃÂ¥ÃÂ£Ãâ€ÃÂÃâ€ºÃâ€ÃÂÃÂ¥Ãâ€œÃ’Â®Ãâ„¢ Ãâ€˜ÃÂÃâ„¢ÃÂ¥ (SELL/AVOID)"
        reason = "Ãâ€“ÃÂ¸ÃÂ½ÃÂ»Ã‘ÂÃ‘ÂÃ‘ÂÃÂ½ Ã’Â¯ÃÂ½Ã‘ÂÃÂ»ÃÂ³Ã‘ÂÃ‘Â Ã‘ÂÃ“Â©Ã‘â‚¬Ã“Â©ÃÂ³ ÃÂ±ÃÂ°ÃÂ¹ÃÂ½ÃÂ°."
    else:
        decision = "Ã¢ÂÂ³ ÃÂ¥Ã’Â®Ãâ€ºÃÂ­ÃÂ¥ (WAIT)"
        reason = "Ãâ€ÃÂ¾Ã‘â€¦ÃÂ¸ÃÂ¾ Ã‘â€šÃ“Â©ÃÂ²ÃÂ¸ÃÂ¹ÃÂ³ Ã‘ÂÃÂ°Ã‘â€¦ÃÂ¸Ã‘ÂÃÂ°ÃÂ½ ÃÂ±ÃÂ°ÃÂ¹ÃÂ½ÃÂ°."
elif is_backtest_reliable and not is_ml_reliable:
    # Only backtest reliable
    if cpp_return > 50:
        decision = "Ã¢Å¡Â Ã¯Â¸Â Ãâ€˜ÃÅ¾Ãâ€ºÃâ€œÃÅ¾ÃÅ¾ÃÅ“Ãâ€“ÃÂ¢ÃÅ¾Ãâ„¢ ÃÂ¥ÃÂ£Ãâ€ÃÂÃâ€ºÃâ€ÃÂÃÂ¥ (CAUTIOUS BUY)"
        reason = f"Backtest Ã“Â©ÃÂ½ÃÂ´Ã“Â©Ã‘â‚¬ Ã“Â©ÃÂ³Ã“Â©Ã“Â©ÃÂ¶Ã‘â€šÃ‘ÂÃÂ¹ ({cpp_return:.1f}%) ÃÂ±ÃÂ¾ÃÂ»ÃÂ¾ÃÂ²Ã‘â€¡ ML ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬ÃÂ³Ã’Â¯ÃÂ¹."
    else:
        decision = "Ã¢ÂÂ³ ÃÂ¥Ã’Â®Ãâ€ºÃÂ­ÃÂ¥ (WAIT)"
        reason = "Ãâ€”Ã“Â©ÃÂ²Ã‘â€¦Ã“Â©ÃÂ½ Backtest ÃÂ» ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬Ã‘â€šÃÂ°ÃÂ¹, ML ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬ÃÂ³Ã’Â¯ÃÂ¹."
else:
    # Only ML reliable
    if ML_PROB > 0.65:
        decision = "Ã¢Å¡Â Ã¯Â¸Â Ãâ€˜ÃÅ¾Ãâ€ºÃâ€œÃÅ¾ÃÅ¾ÃÅ“Ãâ€“ÃÂ¢ÃÅ¾Ãâ„¢ ÃÂ¥ÃÂ£Ãâ€ÃÂÃâ€ºÃâ€ÃÂÃÂ¥ (CAUTIOUS BUY)"
        reason = f"ML Ã“Â©ÃÂ½ÃÂ´Ã“Â©Ã‘â‚¬ ÃÂ¼ÃÂ°ÃÂ³ÃÂ°ÃÂ´ÃÂ»ÃÂ°ÃÂ»Ã‘â€šÃÂ°ÃÂ¹ ({ML_PROB:.0%}%) ÃÂ±ÃÂ¾ÃÂ»ÃÂ¾ÃÂ²Ã‘â€¡ Backtest ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬ÃÂ³Ã’Â¯ÃÂ¹."
    else:
        decision = "Ã¢ÂÂ³ ÃÂ¥Ã’Â®Ãâ€ºÃÂ­ÃÂ¥ (WAIT)"
        reason = "Ãâ€”Ã“Â©ÃÂ²Ã‘â€¦Ã“Â©ÃÂ½ ML ÃÂ» ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬Ã‘â€šÃÂ°ÃÂ¹, Backtest ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂ²ÃÂ°Ã‘â‚¬ÃÂ³Ã’Â¯ÃÂ¹."

print(f"\nÃ°Å¸Å½Â¯ ÃÂ¨ÃËœÃâ„¢Ãâ€Ãâ€™ÃÂ­ÃÂ : {decision}")
print(f"   ÃÂ¨ÃÂ°ÃÂ»Ã‘â€šÃÂ³ÃÂ°ÃÂ°ÃÂ½: {reason}")

# ============================================================
# 7. ÃÂ­ÃÂ¦ÃÂ¡ÃËœÃâ„¢ÃÂ ÃÂ¢ÃÂÃâ„¢Ãâ€ºÃÂÃÂ
# ============================================================
print("\n" + "=" * 80)
print("Ã°Å¸â€œÅ  ÃÂ­ÃÂ¦ÃÂ¡ÃËœÃâ„¢ÃÂ ÃÂ¢ÃÂÃâ„¢Ãâ€ºÃÂÃÂ")
print("=" * 80)

print(
    f"""
Ã°Å¸â€œÅ’ ÃÂ¥Ã‘Æ’Ã‘â‚¬ÃÂ°ÃÂ°ÃÂ½ÃÂ³Ã‘Æ’ÃÂ¹:
   - C++ Backtest: {cpp_trades} ÃÂ°Ã‘â‚¬ÃÂ¸ÃÂ»ÃÂ³ÃÂ°ÃÂ°, {cpp_return:.2f}% Ã“Â©ÃÂ³Ã“Â©Ã“Â©ÃÂ¶
   - Python Backtest: {len(py_trades)//2} ÃÂ°Ã‘â‚¬ÃÂ¸ÃÂ»ÃÂ³ÃÂ°ÃÂ°, {py_return:.2f}% Ã“Â©ÃÂ³Ã“Â©Ã“Â©ÃÂ¶
   - ML Accuracy: {ML_ACCURACY:.2%}
   - ML Signal: {ML_SIGNAL} (Prob: {ML_PROB:.0%})
   - Decision: {decision}

Ã°Å¸â€œâ€¹ Ãâ€”Ã“Â©ÃÂ²ÃÂ»Ã“Â©ÃÂ¼ÃÂ¶:
   {reason}
"""
)

print("=" * 80)
print("Ã¢Å“â€¦ ÃÂ¨ÃËœÃÂÃâ€“ÃËœÃâ€ºÃâ€œÃÂ­ÃÂ­ Ãâ€ÃÂ£ÃÂ£ÃÂ¡ÃÂ¡ÃÂÃÂ.")
