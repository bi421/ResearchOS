import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from researchos.data_engine.dataset import HistoricalDataset
from researchos.data_engine.candle import Candle
from researchos.data_engine.repository import SqliteDatasetRepository

# Download BTCUSD data
btc = yf.download("BTC-USD", start="2023-01-01", end=datetime.now().strftime("%Y-%m-%d"))
btc = btc[["Open", "High", "Low", "Close", "Volume"]]
btc.columns = ["open", "high", "low", "close", "volume"]
btc.index.name = "timestamp"

# Create dataset
dataset = HistoricalDataset(
    symbol="BTCUSD",
    timeframe="1d",
    data_type="candle",
    source="yfinance"
)
for ts, row in btc.iterrows():
    candle = Candle(
        symbol="BTCUSD",
        timeframe="1d",
        timestamp=ts.to_pydatetime(),
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row["volume"])
    )
    dataset.add_record(candle)

# Save to repository
repo = SqliteDatasetRepository("researchos.db")
repo.save(dataset)
print(f"✅ BTCUSD saved: {dataset.record_count} records")
