"""
Extended Data Engine tests.

Covers Phase 2 additions:
    - DatasetType enum
    - DatasetMetadata timezone / date_range
    - MT5, TradingView, and Generic CSV loader profiles + auto-detection
    - Repository date-range lookup and indexes
    - Iterator no-lookahead (as_of) guarantee
    - Hashing extended stability
    - End-to-end determinism
    - queries module re-export
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from researchos.engines.data import (
    Candle,
    CsvLoader,
    DatasetMetadata,
    DatasetRepository,
    DatasetType,
    DuplicateDetector,
    GapDetector,
    HistoricalDataset,
    HistoricalIterator,
    SqliteDatasetRepository,
    verify_dataset_integrity,
)
from researchos.engines.data.queries import MultiSymbolQuery, RangeQuery

BASE = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)

MT5_CSV = """Date,Time,Open,High,Low,Close,Volume
2024.01.01,09:00,2000.00,2010.00,1995.00,2005.00,1000
2024.01.01,10:00,2005.00,2015.00,2000.00,2010.00,1500
2024.01.01,11:00,2010.00,2020.00,2005.00,2015.00,2000"""

MT5_EXT_CSV = """Date,Time,Open,High,Low,Close,tick_volume,real_volume,spread
2024.01.01,09:00,2000.00,2010.00,1995.00,2005.00,1000,80.5,12
2024.01.01,10:00,2005.00,2015.00,2000.00,2010.00,1500,90.0,15"""

TRADINGVIEW_CSV = """time,open,high,low,close,volume
1704096000,2000.0,2010.0,1995.0,2005.0,1000.0
1704099600,2005.0,2015.0,2000.0,2010.0,1500.0
1704103200,2010.0,2020.0,2005.0,2015.0,2000.0"""

TRADINGVIEW_ISO_CSV = """time,open,high,low,close,volume
2024-01-01T09:00:00Z,2000.0,2010.0,1995.0,2005.0,1000.0
2024-01-01T10:00:00Z,2005.0,2015.0,2000.0,2010.0,1500.0"""

GENERIC_CSV = """timestamp,open,high,low,close,volume
2024-01-01 09:00:00,2000.0,2010.0,1995.0,2005.0,1000.0
2024-01-01 10:00:00,2005.0,2015.0,2000.0,2010.0,1500.0"""


def _candle(hour):
    return Candle(
        symbol="XAU/USD",
        timeframe="1h",
        timestamp=BASE + timedelta(hours=hour),
        open=2000.0,
        high=2010.0,
        low=1995.0,
        close=2005.0,
        volume=1000.0,
    )


class TestDatasetType:
    def test_values(self):
        assert DatasetType.CANDLE.value == "candle"
        assert DatasetType.TICK.value == "tick"
        assert DatasetType.QUOTE.value == "quote"
        assert DatasetType.TRADE.value == "trade"
        assert DatasetType.ORDERBOOK.value == "orderbook"

    def test_from_string(self):
        assert DatasetType.from_string("candle") == DatasetType.CANDLE
        assert DatasetType.from_string("OHLCV") == DatasetType.CANDLE
        assert DatasetType.from_string("ticks") == DatasetType.TICK
        assert DatasetType.from_string("Bar") == DatasetType.CANDLE
        assert DatasetType.from_string("order_book") == DatasetType.ORDERBOOK

    def test_invalid(self):
        with pytest.raises(ValueError):
            DatasetType.from_string("nonsense")

    def test_matches(self):
        assert DatasetType.CANDLE.matches("candle") is True
        assert DatasetType.CANDLE.matches("Candle") is True
        assert DatasetType.TICK.matches("candle") is False

    def test_is_str_enum(self):
        assert isinstance(DatasetType.CANDLE, str)


class TestMetadataExtended:
    def test_timezone_default(self):
        meta = DatasetMetadata(dataset_id="x", symbol="XAU/USD", timeframe="1h")
        assert meta.timezone == "UTC"

    def test_timezone_set(self):
        meta = DatasetMetadata(
            dataset_id="x",
            symbol="XAU/USD",
            timeframe="1h",
            timezone="EST",
        )
        assert meta.timezone == "EST"

    def test_date_range(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        meta = DatasetMetadata(
            dataset_id="x",
            symbol="XAU/USD",
            timeframe="1h",
            start_time=start,
            end_time=end,
        )
        assert meta.date_range == (start, end)

    def test_date_range_none(self):
        meta = DatasetMetadata(dataset_id="x", symbol="XAU/USD", timeframe="1h")
        assert meta.date_range is None

    def test_serialization_roundtrip(self):
        meta = DatasetMetadata(
            dataset_id="x",
            symbol="XAU/USD",
            timeframe="1h",
            timezone="EST",
            start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )
        data = meta.to_dict()
        meta2 = DatasetMetadata.from_dict(data)
        assert meta2.timezone == "EST"
        assert meta2.date_range == meta.date_range
        assert data["date_range"] is not None

    def test_timezone_in_hash(self):
        m1 = DatasetMetadata(dataset_id="x", symbol="XAU/USD", timeframe="1h", timezone="EST")
        m2 = DatasetMetadata(dataset_id="x", symbol="XAU/USD", timeframe="1h", timezone="UTC")
        assert m1.hash != m2.hash


class TestCsvLoaderMt5:
    def test_load_mt5(self):
        loader = CsvLoader()
        candles = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD")
        assert len(candles) == 3
        assert candles[0].open == 2000.0
        assert candles[0].timeframe == "1h"
        assert candles[0].timestamp.tzinfo is not None

    def test_mt5_utc_timestamp(self):
        loader = CsvLoader()
        candles = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        assert candles[0].timestamp.hour == 9

    def test_mt5_timezone_normalization(self):
        loader = CsvLoader()
        candles = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="EST")
        assert candles[0].timestamp.hour == 14  # 09:00 EST == 14:00 UTC

    def test_mt5_extended_columns(self):
        loader = CsvLoader()
        candles = loader.load_mt5_candles_from_text(MT5_EXT_CSV, "XAU/USD", timeframe="1h")
        c = candles[0]
        assert c.tick_volume == 1000.0
        assert c.real_volume == 80.5
        assert c.spread == 12.0
        assert c.volume == 1000.0

    def test_mt5_detect_timeframe(self):
        loader = CsvLoader()
        candles = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        assert candles[0].timeframe == "1h"

    def test_mt5_deterministic_ids(self):
        loader = CsvLoader()
        c1 = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        c2 = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        assert [c.id for c in c1] == [c.id for c in c2]

    def test_mt5_missing_columns(self):
        loader = CsvLoader()
        with pytest.raises(ValueError):
            loader.load_mt5_candles_from_text("Date,Time,Open\n2024.01.01,09:00,2000", "XAU/USD")

    def test_mt5_detect_format(self):
        loader = CsvLoader()
        assert (
            loader.detect_format(["Date", "Time", "Open", "High", "Low", "Close", "Volume"])
            == "mt5"
        )


class TestCsvLoaderTradingView:
    def test_load_tradingview_unix_time(self):
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(TRADINGVIEW_CSV, "XAU/USD")
        assert len(candles) == 3
        assert candles[0].timestamp == datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)

    def test_load_tradingview_iso_time(self):
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(TRADINGVIEW_ISO_CSV, "XAU/USD")
        assert len(candles) == 2
        assert candles[0].timestamp.hour == 9

    def test_tradingview_detect_timeframe(self):
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(TRADINGVIEW_CSV, "XAU/USD")
        assert candles[0].timeframe == "1h"

    def test_tradingview_duplicate_removal(self):
        dup_csv = TRADINGVIEW_CSV + "\n1704096000,2000.0,2010.0,1995.0,2005.0,1000.0"
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(dup_csv, "XAU/USD")
        assert len(candles) == 3

    def test_tradingview_keep_duplicates(self):
        dup_csv = TRADINGVIEW_CSV + "\n1704096000,2000.0,2010.0,1995.0,2005.0,1000.0"
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(
            dup_csv, "XAU/USD", remove_duplicates=False
        )
        assert len(candles) == 4

    def test_tradingview_symbol_column(self):
        csv_text = "time,symbol,open,high,low,close,volume\n" + "\n".join(
            f"{t},XAU/USD,2000.0,2010.0,1995.0,2005.0,1000.0" for t in (1704096000, 1704099600)
        )
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(csv_text, "XAU/USD")
        assert all(c.symbol == "XAU/USD" for c in candles)

    def test_tradingview_missing_columns(self):
        loader = CsvLoader()
        with pytest.raises(ValueError):
            loader.load_tradingview_candles_from_text("time,open\n1704096000,2000", "XAU/USD")


class TestCsvLoaderAuto:
    def test_auto_mt5(self):
        loader = CsvLoader()
        candles = loader.load_candles_auto_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        assert len(candles) == 3
        assert candles[0].timeframe == "1h"

    def test_auto_tradingview(self):
        loader = CsvLoader()
        candles = loader.load_candles_auto_from_text(TRADINGVIEW_CSV, "XAU/USD")
        assert len(candles) == 3
        assert candles[0].timeframe == "1h"

    def test_auto_generic(self):
        loader = CsvLoader()
        candles = loader.load_candles_auto_from_text(GENERIC_CSV, "XAU/USD")
        assert len(candles) == 2
        assert candles[0].open == 2000.0

    def test_auto_generic_timeframe(self):
        loader = CsvLoader()
        candles = loader.load_candles_auto_from_text(GENERIC_CSV, "XAU/USD")
        assert candles[0].timeframe == "1h"

    def test_detect_format_generic(self):
        loader = CsvLoader()
        assert (
            loader.detect_format(["timestamp", "open", "high", "low", "close", "volume"])
            == "generic"
        )

    def test_detect_columns_aliases(self):
        loader = CsvLoader()
        mapping = loader.detect_candle_columns(["Date", "O", "H", "L", "C", "V"])
        assert mapping.timestamp == "Date"
        assert mapping.open == "O"
        assert mapping.close == "C"
        assert mapping.volume == "V"

    def test_auto_timeframe_requires_two_rows(self):
        loader = CsvLoader()
        with pytest.raises(ValueError):
            loader.detect_timeframe([BASE])

    def test_detect_timeframe_from_list(self):
        loader = CsvLoader()
        assert loader.detect_timeframe([BASE, BASE + timedelta(hours=1)]) == "1h"


class TestIteratorNoLookahead:
    def _ds(self):
        ds = HistoricalDataset(symbol="XAU/USD", timeframe="1h")
        ds.add_records([_candle(i) for i in range(10)])
        ds.mark_ready()
        return ds

    def test_as_of_filters_future(self):
        it = HistoricalIterator(self._ds(), as_of=BASE + timedelta(hours=4))
        records = list(it)
        assert len(records) == 5
        assert all(r.timestamp <= BASE + timedelta(hours=4) for r in records)

    def test_as_of_boundary_inclusive(self):
        it = HistoricalIterator(self._ds(), as_of=BASE + timedelta(hours=3))
        records = list(it)
        assert records[-1].timestamp == BASE + timedelta(hours=3)

    def test_no_lookahead_without_as_of(self):
        it = HistoricalIterator(self._ds())
        records = list(it)
        assert len(records) == 10

    def test_as_of_with_windows(self):
        it = HistoricalIterator(self._ds(), as_of=BASE + timedelta(hours=5))
        for window in it.windows(window_size=3, step=1):
            assert all(r.timestamp <= BASE + timedelta(hours=5) for r in window)

    def test_as_of_deterministic(self):
        a = list(HistoricalIterator(self._ds(), as_of=BASE + timedelta(hours=6)))
        b = list(HistoricalIterator(self._ds(), as_of=BASE + timedelta(hours=6)))
        assert [r.id for r in a] == [r.id for r in b]

    def test_as_of_len(self):
        it = HistoricalIterator(self._ds(), as_of=BASE + timedelta(hours=2))
        assert len(it) == 3

    def test_as_of_combined_with_range(self):
        it = HistoricalIterator(
            self._ds(),
            start_time=BASE + timedelta(hours=1),
            end_time=BASE + timedelta(hours=8),
            as_of=BASE + timedelta(hours=4),
        )
        records = list(it)
        assert len(records) == 4  # hours 1..4

    def test_as_of_reverse(self):
        it = HistoricalIterator(self._ds(), reverse=True, as_of=BASE + timedelta(hours=4))
        records = list(it)
        assert records[0].timestamp == BASE + timedelta(hours=4)


class TestRepositoryDateRange:
    def _ds(self, day_offset=0, symbol="XAU/USD"):
        candles = [
            _candle(0 + 24 * day_offset),
            _candle(1 + 24 * day_offset),
            _candle(2 + 24 * day_offset),
        ]
        ds = HistoricalDataset(symbol=symbol, timeframe="1h", records=candles)
        ds.mark_ready()
        return ds

    def test_in_memory_find_by_date_range(self):
        repo = DatasetRepository()
        repo.save(self._ds())
        results = repo.find_by_date_range(
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 23, 0, tzinfo=timezone.utc),
        )
        assert len(results) == 1

    def test_in_memory_no_overlap(self):
        repo = DatasetRepository()
        repo.save(self._ds())
        results = repo.find_by_date_range(
            datetime(2024, 2, 1, tzinfo=timezone.utc),
            datetime(2024, 2, 2, tzinfo=timezone.utc),
        )
        assert len(results) == 0

    def test_in_memory_symbol_filter(self):
        repo = DatasetRepository()
        repo.save(self._ds(symbol="XAU/USD"))
        repo.save(self._ds(symbol="XAG/USD"))
        results = repo.find_by_date_range(
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            symbol="XAG/USD",
        )
        assert len(results) == 1
        assert results[0].symbol == "XAG/USD"

    def test_sqlite_find_by_date_range(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            repo = SqliteDatasetRepository(path)
            repo.save(self._ds())
            results = repo.find_by_date_range(
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 23, 0, tzinfo=timezone.utc),
            )
            assert len(results) == 1
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_sqlite_date_range_no_match(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            repo = SqliteDatasetRepository(path)
            repo.save(self._ds())
            results = repo.find_by_date_range(
                datetime(2024, 3, 1, tzinfo=timezone.utc),
                datetime(2024, 3, 2, tzinfo=timezone.utc),
            )
            assert len(results) == 0
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_sqlite_indexes_exist(self):
        import sqlite3

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            SqliteDatasetRepository(path)
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {r[0] for r in cur.fetchall()}
            conn.close()
            assert "idx_metadata_symbol_timeframe" in indexes
            assert "idx_metadata_start_time" in indexes
            assert "idx_metadata_end_time" in indexes
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestQueriesModule:
    def test_range_query_reexport(self):
        q = RangeQuery(symbol="XAU/USD", timeframe="1h")
        assert q.symbol == "XAU/USD"

    def test_multi_symbol_reexport(self):
        q = MultiSymbolQuery(symbols=["XAU/USD"], timeframe="1h")
        assert q.symbols == ["XAU/USD"]

    def test_queries_module_is_same_object(self):
        from researchos.engines.data import RangeQuery as RootRangeQuery

        assert RootRangeQuery is RangeQuery


class TestHashingExtended:
    def test_candle_hash_changes_with_spread(self):
        c1 = _candle(0)
        c2 = Candle(
            symbol="XAU/USD",
            timeframe="1h",
            timestamp=c1.timestamp,
            open=2000.0,
            high=2010.0,
            low=1995.0,
            close=2005.0,
            volume=1000.0,
            spread=3.0,
        )
        assert c1.hash != c2.hash

    def test_candle_hash_with_tick_volume(self):
        c1 = _candle(0)
        c2 = Candle(
            symbol="XAU/USD",
            timeframe="1h",
            timestamp=c1.timestamp,
            open=2000.0,
            high=2010.0,
            low=1995.0,
            close=2005.0,
            volume=1000.0,
            tick_volume=500.0,
        )
        assert c1.hash != c2.hash

    def test_dataset_hash_deterministic_reload(self):
        ds1 = HistoricalDataset(symbol="XAU/USD", timeframe="1h")
        ds1.add_records([_candle(i) for i in range(10)])
        ds1.mark_ready()
        ds2 = HistoricalDataset(symbol="XAU/USD", timeframe="1h")
        ds2.add_records([_candle(i) for i in range(10)])
        ds2.mark_ready()
        assert ds1.dataset_hash == ds2.dataset_hash
        assert verify_dataset_integrity(ds1)
        assert verify_dataset_integrity(ds2)

    def test_range_hash_deterministic(self):
        from researchos.engines.data import compute_range_hash

        candles = [_candle(i) for i in range(5)]
        h1 = compute_range_hash(candles)
        h2 = compute_range_hash([_candle(i) for i in range(5)])
        assert h1 == h2


class TestEndToEndDeterminism:
    def test_same_csv_same_objects(self):
        loader = CsvLoader()
        a = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        b = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        assert [c.id for c in a] == [c.id for c in b]
        assert [c.hash for c in a] == [c.hash for c in b]

    def test_same_csv_same_dataset_hash(self):
        loader = CsvLoader()
        for _ in range(2):
            candles = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
            ds = HistoricalDataset(symbol="XAU/USD", timeframe="1h", records=candles)
            ds.mark_ready()
            h = ds.dataset_hash
            break
        candles2 = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
        ds2 = HistoricalDataset(symbol="XAU/USD", timeframe="1h", records=candles2)
        ds2.mark_ready()
        assert h == ds2.dataset_hash

    def test_same_csv_same_repository_records(self):
        loader = CsvLoader()
        repo1 = DatasetRepository()
        repo2 = DatasetRepository()
        for repo in (repo1, repo2):
            candles = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="UTC")
            ds = HistoricalDataset(symbol="XAU/USD", timeframe="1h", records=candles)
            ds.mark_ready()
            repo.save(ds)
        assert repo1.get_all()[0].dataset_hash == repo2.get_all()[0].dataset_hash

    def test_utc_normalization_deterministic(self):
        loader = CsvLoader()
        a = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="EST")
        b = loader.load_mt5_candles_from_text(MT5_CSV, "XAU/USD", timezone="EST")
        assert [c.timestamp for c in a] == [c.timestamp for c in b]

    def test_duplicate_detection_after_tradingview_load(self):
        dup_csv = TRADINGVIEW_CSV + "\n1704096000,2000.0,2010.0,1995.0,2005.0,1000.0"
        loader = CsvLoader()
        candles = loader.load_tradingview_candles_from_text(
            dup_csv, "XAU/USD", remove_duplicates=False
        )
        detector = DuplicateDetector()
        assert len(detector.detect(candles)) == 1

    def test_gap_detection_after_load(self):
        loader = CsvLoader()
        candles = loader.load_mt5_candles_from_text(
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2024.01.01,09:00,2000,2010,1995,2005,1000\n"
            "2024.01.01,14:00,2010,2020,2005,2015,1000\n",
            "XAU/USD",
            timeframe="1h",
            timezone="UTC",
        )
        detector = GapDetector()
        gaps = detector.detect(candles, "1h")
        assert len(gaps) == 1
