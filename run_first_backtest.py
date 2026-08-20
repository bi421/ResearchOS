"""
Run first XAUUSD backtest using cpp_quant_engine.BacktestEngine
with real data from researchos.db.
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cpp_quant_engine", "python"))

from researchos.data_engine.repository import SqliteDatasetRepository

from cpp_quant_engine.backend import BacktestEngine
from cpp_quant_engine.models import MarketData, Candle as CQCandle

# 1. Load XAUUSD D1 candles from researchos.db
repo = SqliteDatasetRepository("researchos.db")
dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
print(f"Loaded {dataset.record_count} XAUUSD candles from researchos.db")

# 2. Convert researchos Candle objects -> cpp_quant_engine Candle objects
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
print(f"Converted {len(cq_candles)} candles for backtest engine")

# 3. Define a simple example signal: buy when today's close > yesterday's close
def sma_uptick_signal(bar_index, history):
    if not history:
        return {"direction": 0, "quantity": 0.0}
    last = history[-1]
    if last["close"] > last["open"]:
        return {"direction": 0, "quantity": 1.0}
    return {"direction": 0, "quantity": 0.0}

# 4. Run backtest
engine = BacktestEngine()
market_data = MarketData(symbol="XAUUSD", candles=cq_candles)
result = engine.run(market_data, signal=sma_uptick_signal, signal_reference="strategy://uptick_v1")

# 5. Show results
print()
print("=== Backtest Result: XAUUSD 2021-2025 D1 ===")
print(f"Total bars:       {result.total_bars}")
print(f"Num trades:       {result.num_trades}")
print(f"Final equity:     {result.final_equity:,.2f}")
print(f"Total return %:   {result.total_return_pct:.2f}%")
print(f"Max drawdown %:   {result.max_drawdown_pct:.2f}%")
print(f"Signal reference: {result.signal_reference}")
print(f"Input hash:       {result.input_hash}")
print(f"Result hash:      {result.result_hash}")
print(f"Engine version:   {result.engine_version}")
