import sys

sys.path.insert(0, ".")
import pandas as pd
import yfinance as yf

from researchos.quant_engine.advanced_backtest import AdvancedBacktestEngine
from researchos.quant_engine.ensemble_strategy import EnsembleStrategy

print("🔄 Bitcoin (BTC-USD) бодит 1 жилийн өгөгдөл татаж байна...")
df = yf.download("BTC-USD", period="1y", progress=False)

close_col = df["Close"]
if isinstance(close_col, pd.DataFrame):
    prices = close_col.iloc[:, 0].dropna().astype(float).tolist()
else:
    prices = close_col.dropna().astype(float).tolist()

print(f"✅ {len(prices)} өдрийн бодит өгөгдөл татагдлаа")

# Стратеги болон Engine-г эхлүүлэх
strategy = EnsembleStrategy(min_confidence=0.60)  # 60% босго
engine = AdvancedBacktestEngine(initial_capital=100000.0)

print("\n🔍 СТРАТЕГИЙН ОЛСОН ДОХИОНУУД (Эхний 5):")
signals = strategy.generate_signals(prices)
for i, sig in enumerate(signals[:5]):
    print(f"  Өдөр {sig.day_index}: {sig.action} @ ${sig.price:,.2f} (Confidence: {sig.confidence * 100:.0f}%)")
    for reason in sig.reasons:
        print(f"    -> {reason}")
print(f"  ... Нийт {len(signals)} дохио олдсон.\n")

# Backtest гүйцэтгэх
result = engine.run(prices, strategy)

print("=" * 70)
print("  ЗАСВАРЛАГСАН НЭГТГЭСЭН СТРАТЕГИЙН ҮР ДҮН")
print("=" * 70)
print(f"  Гүйлгээний тоо          : {result.num_trades}")
print(f"  Нийт өгөөж              : {result.total_return * 100:>8.2f}%")
print(f"  Sharpe Ratio            : {result.sharpe_ratio:>8.2f}")
print(f"  Max Drawdown            : {result.max_drawdown * 100:>8.2f}%")
print(f"  Ялалтын хувь            : {result.win_rate * 100:>8.1f}%")
print(f"  Profit Factor           : {result.profit_factor:>8.2f}")
print(f"  Нийт комисс            : ${result.total_commission:>10.2f}")
print(f"  Нийт slippage          : ${result.total_slippage:>10.2f}")
print("=" * 70)

if result.num_trades > 0:
    print("✅ Одоо систем бодитой ажиллаж, гүйлгээ хийж байна!")
else:
    print("⚠️ Өгөгдлийн онцлогоос шалтгаалан дохио үүсээгүй байна.")
