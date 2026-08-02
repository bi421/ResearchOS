"""
Performance benchmarks for the Data Engine.

Measures load, validation, hashing, repository insert/lookup, and iterator
scan across 100k and 1M candle datasets.

Gated by the RESEARCHOS_PERF=1 environment variable to keep the default
regression suite fast. Ceilings are set generously to remain stable on
noisy development machines.
"""

import os
import tempfile
import time
from datetime import datetime, timedelta, timezone

import pytest

from researchos.data_engine import (
    CsvLoader,
    DatasetValidator,
    HistoricalDataset,
    HistoricalIterator,
    SqliteDatasetRepository,
)

RESEARCHOS_PERF = os.environ.get("RESEARCHOS_PERF", "") == "1"

pytestmark = pytest.mark.skipif(
    not RESEARCHOS_PERF,
    reason="perf benchmarks require RESEARCHOS_PERF=1",
)

BASE = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _write_candle_csv(path: str, count: int, timeframe_seconds: int = 60) -> str:
    """Write a deterministic OHLCV CSV file with `count` rows."""
    with open(path, "w") as f:
        f.write("timestamp,open,high,low,close,volume\n")
        for i in range(count):
            ts = BASE + timedelta(seconds=i * timeframe_seconds)
            f.write(
                f"{ts.isoformat()},2000.0,2010.0,1995.0,2005.0,1000.0\n"
            )
    return path


def _measure_stages(count: int, timeframe: str) -> dict:
    """Generate data and measure each pipeline stage."""
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = os.path.join(tmp, "candles.csv")
        db_path = os.path.join(tmp, "repo.db")
        results: dict = {}

        t0 = time.perf_counter()
        _write_candle_csv(csv_path, count)
        results["csv_write"] = time.perf_counter() - t0

        loader = CsvLoader()
        t0 = time.perf_counter()
        candles = loader.load_candles(csv_path, symbol="XAU/USD", timeframe=timeframe)
        results["load"] = time.perf_counter() - t0
        results["records"] = len(candles)

        validator = DatasetValidator()
        t0 = time.perf_counter()
        validator.validate(candles, timeframe, symbol="XAU/USD")
        results["validate"] = time.perf_counter() - t0

        dataset = HistoricalDataset(
            symbol="XAU/USD", timeframe=timeframe, data_type="candle",
            records=candles, source="bench",
        )
        t0 = time.perf_counter()
        dataset.mark_ready()
        results["hash"] = time.perf_counter() - t0
        results["dataset_hash"] = dataset.dataset_hash

        repo = SqliteDatasetRepository(db_path)
        t0 = time.perf_counter()
        repo.save(dataset)
        results["repo_insert"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        found = repo.find_by_symbol_and_timeframe("XAU/USD", timeframe)
        results["repo_lookup"] = time.perf_counter() - t0
        results["lookup_found"] = found is not None

        iterator = HistoricalIterator(dataset)
        t0 = time.perf_counter()
        n = 0
        for _ in iterator:
            n += 1
        results["iterator_scan"] = time.perf_counter() - t0
        results["scanned"] = n

    return results


class TestBenchmark100k:
    def test_pipeline(self):
        results = _measure_stages(100_000, "1m")
        assert results["records"] == 100_000
        assert results["scanned"] == 100_000
        assert results["lookup_found"] is True
        assert len(results["dataset_hash"]) == 64
        assert results["load"] < 20.0
        assert results["validate"] < 40.0
        assert results["hash"] < 20.0
        assert results["repo_insert"] < 60.0
        assert results["repo_lookup"] < 3.0
        assert results["iterator_scan"] < 15.0
        print(f"\n100k: {results}")


class TestBenchmark1M:
    def test_pipeline(self):
        results = _measure_stages(1_000_000, "1m")
        assert results["records"] == 1_000_000
        assert results["scanned"] == 1_000_000
        assert results["lookup_found"] is True
        assert len(results["dataset_hash"]) == 64
        assert results["load"] < 240.0
        assert results["validate"] < 300.0
        assert results["hash"] < 180.0
        assert results["repo_insert"] < 360.0
        assert results["repo_lookup"] < 5.0
        assert results["iterator_scan"] < 120.0
        print(f"\n1M: {results}")
