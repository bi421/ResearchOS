import sys

sys.path.insert(0, ".")
import yfinance as yf
import pandas as pd
from researchos.quant_engine.ensemble_strategy import EnsembleStrategy
from researchos.quant_engine.advanced_backtest import AdvancedBacktestEngine

print("🔄 Bitcoin (BTC-USD) бодит 1 жилийн өгөгдөл татаж байна...")
df = yf.download("BTC-USD", period="1y", progress=False)

close_col = df["Close"]
if isinstance(close_col, pd.DataFrame):
    prices = close_col.iloc[:, 0].dropna().astype(float).tolist()
else:
    prices = close_col.dropna().astype(float).tolist()

print(f"✅ {len(prices)} өдрийн бодит өгөгдөл татагдлаа")

# Стратеги
strategy = EnsembleStrategy(min_confidence=0.60)

# Engine: 15% Stop Loss, 30% Take Profit, 30 хоног дээд хугацаа
engine = AdvancedBacktestEngine(
    initial_capital=100000.0, stop_loss=0.15, take_profit=0.30, max_hold_days=30
)

result = engine.run(prices, strategy)

print("\n" + "=" * 70)
print("  RISK MANAGEMENT-ТЭЙ СТРАТЕГИЙН ҮР ДҮН")
print("=" * 70)
print(f"  Гүйлгээний тоо          : {result.num_trades}")
print(f"  Нийт өгөөж              : {result.total_return * 100:>8.2f}%")
print(f"  Жилийн дундаж өгөөж     : {result.annualised_return * 100:>8.2f}%")
print(f"  Sharpe Ratio            : {result.sharpe_ratio:>8.2f}")
print(f"  Max Drawdown            : {result.max_drawdown * 100:>8.2f}%")
print(f"  Ялалтын хувь            : {result.win_rate * 100:>8.1f}%")
print(f"  Profit Factor           : {result.profit_factor:>8.2f}")
print(f"  Дундаж ялалт           : {result.avg_win * 100:>8.2f}%")
print(f"  Дундаж алдагдал        : {result.avg_loss * 100:>8.2f}%")
print(f"  Дараалсан алдагдал     : {result.max_consecutive_losses:>8d}")
print(f"  Нийт комисс            : ${result.total_commission:>10.2f}")
print(f"  Нийт slippage          : ${result.total_slippage:>10.2f}")
print("=" * 70)

if result.num_trades > 0:
    print("✅ Систем гүйлгээг амжилттай нээж, Risk Management-ийн дүрмээр хааж байна!")
else:
    print("⚠️ Гүйлгээ хийгдсэнгүй.")
