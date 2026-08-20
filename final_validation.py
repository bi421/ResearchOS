import sys
sys.path.insert(0, '.')
import yfinance as yf
import pandas as pd
from researchos.quant_engine.ensemble_strategy import EnsembleStrategy
from researchos.quant_engine.advanced_backtest import AdvancedBacktestEngine

print("="*70)
print("  RESEARCHOS: БҮРЭН END-TO-END БАТАЛГААЖУУЛАЛТ")
print("="*70)

print("\n[1/4] Өгөгдөл татаж байна...")
df = yf.download('BTC-USD', period='6mo', progress=False)
close_col = df['Close']
prices = close_col.iloc[:, 0].dropna().astype(float).tolist() if isinstance(close_col, pd.DataFrame) else close_col.dropna().astype(float).tolist()
print(f"    ✅ {len(prices)} өдрийн өгөгдөл бэлэн.")

print("\n[2/4] Стратеги тохируулж байна...")
strategy = EnsembleStrategy(min_confidence=0.60)
print("    ✅ Ensemble Strategy (RSI + MACD + BB) бэлэн.")

print("\n[3/4] Risk Management тохируулж байна...")
engine = AdvancedBacktestEngine(
    initial_capital=100000.0,
    commission=0.001,
    slippage=0.0005,
    stop_loss=0.15,
    take_profit=0.30,
    max_hold_days=30
)
print("    ✅ Stop Loss (15%), Take Profit (30%), Max Hold (30 days) бэлэн.")

print("\n[4/4] Симуляци гүйцэтгэж байна...")
result = engine.run(prices, strategy)

print("\n" + "="*70)
print("  ЭЦСИЙН ҮР ДҮН")
print("="*70)
print(f"  Гүйлгээний тоо          : {result.num_trades}")
print(f"  Нийт өгөөж              : {result.total_return*100:>8.2f}%")
print(f"  Sharpe Ratio            : {result.sharpe_ratio:>8.2f}")
print(f"  Max Drawdown            : {result.max_drawdown*100:>8.2f}%")
print(f"  Ялалтын хувь            : {result.win_rate*100:>8.1f}%")
print(f"  Нийт зардал (Comm+Slip) : ${result.total_commission + result.total_slippage:>8.2f}")
print("="*70)

if result.num_trades > 0:
    print("\n🎉 ЗАМ B БАТАЛГААЖУУЛАЛТ АМЖИЛТТАЙ!")
else:
    print("\n⚠️ ЗАМ B ХЭСЭГЧЛЭН АМЖИЛТТАЙ.")
print("="*70)
