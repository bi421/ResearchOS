"""
ResearchOS Data Engine — deterministic market data loading, storage, and querying.

Phase 1 of the Data Engine implementation provides:
    - Candle, Tick, Quote, Trade, OrderBook data models
    - HistoricalDataset with metadata
    - CSV Loader for importing market data
    - DatasetValidator with gap/duplicate/outlier detection
    - DatasetRepository (in-memory and SQLite)
    - HistoricalIterator for chronological iteration
    - RangeQuery and MultiSymbolQuery
    - Timezone normalization
    - Dataset hashing and versioning
"""

from researchos.data_engine.candle import Candle
from researchos.data_engine.contracts import (
    CandleField,
    DataQuality,
    DatasetStatus,
    DatasetType,
    DataSource,
    LoaderConfig,
    QuoteSide,
    Timeframe,
    TradeSide,
    ValidationReport,
)
from researchos.data_engine.dataset import DataRecord, HistoricalDataset
from researchos.data_engine.hashing import (
    compute_candle_hash,
    compute_dataset_hash,
    compute_range_hash,
    compute_record_hash,
    verify_dataset_integrity,
)
from researchos.data_engine.iterator import HistoricalIterator
from researchos.data_engine.loader import CsvLoader
from researchos.data_engine.metadata import DatasetMetadata
from researchos.data_engine.orderbook import OrderBook, OrderBookLevel
from researchos.data_engine.query import MultiSymbolQuery, RangeQuery
from researchos.data_engine.quote import Quote
from researchos.data_engine.repository import DatasetRepository, SqliteDatasetRepository
from researchos.data_engine.statistics import DatasetStatistics, compute_dataset_statistics
from researchos.data_engine.tick import Tick
from researchos.data_engine.timezone import (
    convert_timezone,
    format_iso,
    normalize_timestamp,
    parse_iso,
)
from researchos.data_engine.trade import Trade
from researchos.data_engine.validator import (
    DatasetValidator,
    DuplicateDetector,
    GapDetector,
    MissingCandleDetector,
    OutlierDetector,
)
from researchos.data_engine.versioning import DatasetVersion, bump_dataset_version

__all__ = [
    "Candle",
    "Tick",
    "Quote",
    "Trade",
    "OrderBook",
    "OrderBookLevel",
    "HistoricalDataset",
    "DataRecord",
    "DatasetMetadata",
    "CsvLoader",
    "DatasetStatistics",
    "compute_dataset_statistics",
    "DatasetValidator",
    "GapDetector",
    "MissingCandleDetector",
    "DuplicateDetector",
    "OutlierDetector",
    "DatasetRepository",
    "SqliteDatasetRepository",
    "HistoricalIterator",
    "RangeQuery",
    "MultiSymbolQuery",
    "normalize_timestamp",
    "convert_timezone",
    "format_iso",
    "parse_iso",
    "compute_dataset_hash",
    "compute_candle_hash",
    "compute_record_hash",
    "verify_dataset_integrity",
    "compute_range_hash",
    "DatasetVersion",
    "bump_dataset_version",
    "Timeframe",
    "DataSource",
    "DataQuality",
    "DatasetStatus",
    "DatasetType",
    "QuoteSide",
    "TradeSide",
    "CandleField",
    "LoaderConfig",
    "ValidationReport",
]
