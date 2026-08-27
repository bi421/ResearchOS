"""
Load XAUUSD D1 CSV into researchos.db as a HistoricalDataset.
"""

from researchos.data_engine.csv_loader import CsvLoader
from researchos.data_engine.dataset import HistoricalDataset
from researchos.data_engine.repository import SqliteDatasetRepository

CSV_PATH = "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
SYMBOL = "XAUUSD"
TIMEFRAME = "1d"

loader = CsvLoader()
candles = loader.load_mt5_candles(CSV_PATH, symbol=SYMBOL, timeframe=TIMEFRAME)
print(f"Loaded {len(candles)} candles from CSV")

dataset = HistoricalDataset(
    symbol=SYMBOL,
    timeframe=TIMEFRAME,
    data_type="candle",
    records=candles,
    source="mt5_final_csv",
    quality="Raw",
)

repo = SqliteDatasetRepository("researchos.db")
repo.save(dataset)
print(f"Saved dataset id={dataset.id}, record_count={dataset.record_count}")

# Verify
check = repo.find_by_symbol_and_timeframe(SYMBOL, TIMEFRAME)
print("Verify:", check.symbol if check else None, check.record_count if check else None)
