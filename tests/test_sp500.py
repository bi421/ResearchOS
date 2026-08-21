import sys

sys.path.insert(0, ".")
import pandas as pd
import yfinance as yf

from researchos.quant_engine.advanced_backtest import AdvancedBacktestEngine
from researchos.quant_engine.ensemble_strategy import EnsembleStrategy

print("🔄 S&P 500 (^GSPC) бодит 1 жилийн өгөгдөл татаж байна...")
df = yf.download("^GSPC", period="1y", progress=False)

close_col = df["Close"]
if isinstance(close_col, pd.DataFrame):
    prices = close_col.iloc[:, 0].dropna().astype(float).tolist()
else:
    prices = close_col.dropna().astype(float).tolist()

print(f"✅ {len(prices)} өдрийн бодит өгөгдөл татагдлаа")
print(f"   Үнийн хүрээ: ${min(prices):,.2f} - ${max(prices):,.2f}")

# Яг ижил стратеги, ижил Risk Management
strategy = EnsembleStrategy(min_confidence=0.60)
engine = AdvancedBacktestEngine(initial_capital=100000.0, stop_loss=0.15, take_profit=0.30, max_hold_days=30)

result = engine.run(prices, strategy)

print("\n" + "=" * 70)
print("  S&P 500 ДЭЭРХ ИЖИЛ СТРАТЕГИЙН ҮР ДҮН")
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
print(f"  Нийт комисс            : ${result.total_commission:>10.2f}")
print(f"  Нийт slippage          : ${result.total_slippage:>10.2f}")
print("=" * 70)

if result.total_return > 0:
    print("✅ Стратеги S&P 500 дээр ашигтай ажиллаж байна! (Зах зээлийн нийцэл батлагдлаа)")
else:
    print("⚠️ Энэ стратеги S&P 500 дээр ч алдагдалтай байна. Параметр оновчлол (Optimization) хийх шаардлагатай.")
