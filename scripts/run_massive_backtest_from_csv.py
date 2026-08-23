# scripts/run_massive_backtest_from_csv.py
import glob
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

print("=" * 100)
print("🚀 MASSIVE BACKTEST – 6 Strategies × 7 Timeframes (from 1-min CSV)")
print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 100)

# 1. CSV-ээс 1-min өгөгдөл ачаалах
print("\n📂 Loading 1-min CSV files...")
all_dfs = []
csv_files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
if not csv_files:
    print("❌ No CSV files found. Check path: data/raw/histdata/xauusd/")
    sys.exit(1)

for f in csv_files:
    df = pd.read_csv(
        f,
        sep=";",
        header=None,
        names=["datetime", "open", "high", "low", "close", "volume"],
        dtype={"datetime": str},
    )
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S", errors="coerce")
    df = df.dropna(subset=["datetime"])
    df.set_index("datetime", inplace=True)
    all_dfs.append(df)
    print(f"   Loaded {len(df)} rows from {os.path.basename(f)}")

df = pd.concat(all_dfs).sort_index()
print(f"✅ Total 1-min candles: {len(df):,}")
print(f"   From {df.index[0]} to {df.index[-1]}")

# 2. Timeframes
TIMEFRAMES = [
    ("15min", "15min"),
    ("30min", "30min"),
    ("1h", "1h"),
    ("4h", "4h"),
    ("1D", "1D"),
    ("W", "W"),
    ("M", "ME"),
]


# 3. Стратегийн функцууд
def sma_signal(df, fast=10, slow=30):
    fast_ma = df["close"].rolling(fast).mean()
    slow_ma = df["close"].rolling(slow).mean()
    return pd.Series(np.where(fast_ma > slow_ma, 1, 0), index=df.index).fillna(0)


def rsi_signal(df, period=14, oversold=30, overbought=70):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    signal = np.where(rsi < oversold, 1, 0)
    signal = np.where(rsi > overbought, 0, signal)
    return pd.Series(signal, index=df.index).fillna(0)


def macd_signal(df, fast=12, slow=26, signal_period=9):
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal_period, adjust=False).mean()
    return pd.Series(np.where(macd > signal_line, 1, 0), index=df.index).fillna(0)


def bb_signal(df, period=20, std_dev=2):
    bb_mid = df["close"].rolling(period).mean()
    bb_std = df["close"].rolling(period).std()
    bb_high = bb_mid + std_dev * bb_std
    bb_low = bb_mid - std_dev * bb_std
    signal = np.where(df["close"] < bb_low, 1, 0)
    signal = np.where(df["close"] > bb_high, 0, signal)
    return pd.Series(signal, index=df.index).fillna(0)


def stochastic_signal(df, k_period=14, d_period=3, oversold=20, overbought=80):
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min)
    d = k.rolling(d_period).mean()
    signal = np.where((k < oversold) & (d < oversold), 1, 0)
    signal = np.where((k > overbought) & (d > overbought), 0, signal)
    return pd.Series(signal, index=df.index).fillna(0)


def atr_signal(df, period=14, multiplier=1.5):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = ranges.rolling(period).mean()
    sma = df["close"].rolling(50).mean()
    signal = np.where(df["close"] > sma + multiplier * atr, 1, 0)
    signal = np.where(df["close"] < sma - multiplier * atr, 0, signal)
    return pd.Series(signal, index=df.index).fillna(0)


STRATEGIES = {
    "SMA(10,30)": sma_signal,
    "RSI(14,30,70)": rsi_signal,
    "MACD(12,26,9)": macd_signal,
    "Bollinger(20,2)": bb_signal,
    "Stochastic(14,3)": stochastic_signal,
    "ATR(14,1.5)": atr_signal,
}


# 4. Backtest функц
def run_backtest(df, signal_func, **kwargs):
    signals = signal_func(df, **kwargs)
    signal = signals.shift(1).fillna(0)
    daily_returns = df["close"].pct_change().fillna(0)
    strategy_returns = daily_returns * signal
    equity_curve = (1 + strategy_returns).cumprod()
    total_return = (equity_curve.iloc[-1] - 1) * 100
    sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252) if strategy_returns.std() != 0 else 0.0
    position_changes = signal.diff().fillna(0)
    trades_df = df[position_changes != 0].copy()
    trades_df["position"] = position_changes[position_changes != 0]
    trades = []
    entry_price = None
    for idx, row in trades_df.iterrows():
        if row["position"] == 1:
            entry_price = row["close"]
        elif row["position"] == -1 and entry_price is not None:
            trades.append((row["close"] - entry_price) / entry_price)
            entry_price = None
    if entry_price is not None:
        trades.append((df["close"].iloc[-1] - entry_price) / entry_price)
    num_trades = len(trades)
    if num_trades == 0:
        return {"trades": 0, "winrate": 0.0, "total_return": total_return, "sharpe": sharpe}
    wins = [t for t in trades if t > 0]
    winrate = len(wins) / num_trades * 100
    return {"trades": num_trades, "winrate": winrate, "total_return": total_return, "sharpe": sharpe}


# 5. Бүх timeframes дээр бүх стратегийг ажиллуулах
print("\n📊 Running backtests...\n")
results = []

for label, rule in TIMEFRAMES:
    print(f"⏳ {label}...")
    df_res = df.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    if len(df_res) < 30:
        print(f"   ⚠️ Not enough data for {label}, skipping.")
        continue
    for name, func in STRATEGIES.items():
        metrics = run_backtest(df_res, func)
        results.append(
            {
                "Timeframe": label,
                "Strategy": name,
                "Candles": len(df_res),
                "Trades": metrics["trades"],
                "Winrate": metrics["winrate"],
                "Return": metrics["total_return"],
                "Sharpe": metrics["sharpe"],
            }
        )
    print(f"   ✅ {len(df_res):,} candles, {len(STRATEGIES)} strategies done.")

# 6. Хүснэгт
df_results = pd.DataFrame(results).round(2)
print("\n" + "=" * 120)
print("📊 FULL RESULTS TABLE")
print("=" * 120)
print(df_results.to_string(index=False))

# 7. Хамгийн их арилгаатай стратегиуд
print("\n" + "=" * 120)
print("🏆 TOP STRATEGIES BY TRADES (>100 trades)")
print("=" * 120)
top_trades = df_results[df_results["Trades"] > 100].sort_values("Trades", ascending=False)
if not top_trades.empty:
    print(top_trades.to_string(index=False))
else:
    print("No strategy with >100 trades found.")

print("\n" + "=" * 120)
print("✅ Done.")
