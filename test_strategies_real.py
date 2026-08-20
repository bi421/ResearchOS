import sys
sys.path.insert(0, '.')
import yfinance as yf
import pandas as pd
from researchos.quant_engine.strategies import RSIStrategy, MACDStrategy, BollingerStrategy
from researchos.quant_engine.backtest import BacktestEngine

print("🔄 Bitcoin (BTC-USD) бодит 1 жилийн өгөгдөл татаж байна...")
df = yf.download('BTC-USD', period='1y', progress=False)

close_col = df['Close']
if isinstance(close_col, pd.DataFrame):
    prices = close_col.iloc[:, 0].dropna().astype(float).tolist()
else:
    prices = close_col.dropna().astype(float).tolist()

print(f"✅ {len(prices)} өдрийн бодит өгөгдөл татагдлаа")
print(f"   Үнийн хүрээ: ${min(prices):,.2f} - ${max(prices):,.2f}")

engine = BacktestEngine(initial_capital=100000.0)

# 1. RSI Стратеги
rsi_strat = RSIStrategy(period=14, oversold=30, overbought=70)
rsi_result = engine.run(prices, rsi_strat)
print("\n📊 RSI Стратеги:")
print(f"   Нийт өгөөж: {rsi_result.total_return * 100:.2f}%")
print(f"   Гүйлгээний тоо: {rsi_result.num_trades}")
print(f"   Ялалтын хувь: {rsi_result.win_rate * 100:.1f}%")

# 2. MACD Стратеги
macd_strat = MACDStrategy(fast=12, slow=26, signal=9)
macd_result = engine.run(prices, macd_strat)
print("\n📊 MACD Стратеги:")
print(f"   Нийт өгөөж: {macd_result.total_return * 100:.2f}%")
print(f"   Гүйлгээний тоо: {macd_result.num_trades}")
print(f"   Ялалтын хувь: {macd_result.win_rate * 100:.1f}%")

# 3. Bollinger Bands Стратеги
bb_strat = BollingerStrategy(period=20, std_dev=2.0)
bb_result = engine.run(prices, bb_strat)
print("\n📊 Bollinger Bands Стратеги:")
print(f"   Нийт өгөөж: {bb_result.total_return * 100:.2f}%")
print(f"   Гүйлгээний тоо: {bb_result.num_trades}")
print(f"   Ялалтын хувь: {bb_result.win_rate * 100:.1f}%")

print("\n" + "=" * 60)
print("✅ Бодит өгөгдлөөр стратегиуд амжилттай ажиллаж байна!")
print("=" * 60)
