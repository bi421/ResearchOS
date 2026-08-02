"""
Tests for DatasetStatistics and compute_dataset_statistics.

Verifies:
    - record count, missing percentage, duplicate count, gap count
    - average spread and average volume
    - first/last timestamp
    - daily coverage and trading days
    - completeness
    - determinism and serialization
"""

from datetime import datetime, timedelta, timezone

import pytest

from researchos.data_engine import (
    Candle,
    HistoricalDataset,
    Quote,
    Tick,
    DatasetStatistics,
    compute_dataset_statistics,
)

BASE = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)


def _candle(hour, symbol="XAU/USD", spread=None, volume=1000.0):
    return Candle(
        symbol=symbol,
        timeframe="1h",
        timestamp=BASE + timedelta(hours=hour),
        open=2000.0, high=2010.0, low=1995.0, close=2005.0,
        volume=volume, spread=spread,
    )


def _dataset(candles):
    ds = HistoricalDataset(
        symbol="XAU/USD", timeframe="1h", data_type="candle",
        records=candles,
    )
    return ds


class TestDatasetStatisticsEmpty:
    def test_empty_dataset(self):
        stats = compute_dataset_statistics(_dataset([]))
        assert stats.record_count == 0
        assert stats.missing_percentage == 0.0
        assert stats.duplicate_count == 0
        assert stats.gap_count == 0
        assert stats.average_spread == 0.0
        assert stats.average_volume == 0.0
        assert stats.first_timestamp is None
        assert stats.last_timestamp is None
        assert stats.daily_coverage == 0.0
        assert stats.trading_days == 0
        assert stats.completeness == 0.0

    def test_empty_dataset_serialization(self):
        stats = compute_dataset_statistics(_dataset([]))
        data = stats.to_dict()
        restored = DatasetStatistics.from_dict(data)
        assert restored.record_count == 0
        assert restored.to_dict() == data


class TestDatasetStatisticsBasics:
    def test_record_count(self):
        candles = [_candle(i) for i in range(10)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.record_count == 10

    def test_consecutive_hourly_complete(self):
        candles = [_candle(i) for i in range(10)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.record_count == 10
        assert stats.missing_percentage == 0.0
        assert stats.gap_count == 0
        assert stats.duplicate_count == 0
        assert stats.completeness == 1.0

    def test_average_volume(self):
        candles = [_candle(i, volume=1000.0 + i * 100.0) for i in range(10)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.average_volume == pytest.approx(1450.0, abs=0.001)

    def test_average_spread_candles(self):
        candles = [_candle(i, spread=10.0 + i) for i in range(5)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.average_spread == pytest.approx(12.0, abs=0.001)

    def test_no_spread_candles(self):
        candles = [_candle(i) for i in range(5)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.average_spread == 0.0

    def test_first_last_timestamp(self):
        candles = [_candle(2), _candle(5), _candle(9)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.first_timestamp == (BASE + timedelta(hours=2)).isoformat()
        assert stats.last_timestamp == (BASE + timedelta(hours=9)).isoformat()

    def test_single_record(self):
        stats = compute_dataset_statistics(_dataset([_candle(0)]))
        assert stats.record_count == 1
        assert stats.missing_percentage == 0.0
        assert stats.gap_count == 0
        assert stats.completeness == 1.0
        assert stats.trading_days == 1
        assert stats.daily_coverage == 1.0

    def test_invalid_gap_tolerance(self):
        with pytest.raises(ValueError):
            compute_dataset_statistics(_dataset([_candle(0)]), gap_tolerance_factor=0)


class TestDatasetStatisticsGaps:
    def test_gap_count_single_missing(self):
        candles = [_candle(0), _candle(2)]  # 1 missing hour
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.gap_count == 1
        assert stats.missing_percentage == pytest.approx(33.3333, abs=0.01)

    def test_missing_percentage_span(self):
        candles = [_candle(0), _candle(5)]  # 5h span, 2 records, 6 expected
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.completeness == pytest.approx(2 / 6, abs=0.001)
        assert stats.missing_percentage == pytest.approx(4 / 6 * 100, abs=0.01)
        assert stats.gap_count == 1

    def test_two_gaps(self):
        candles = [_candle(0), _candle(3), _candle(7)]  # gaps at 0->3 and 3->7
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.gap_count == 2

    def test_no_gaps_with_tolerance_factor(self):
        candles = [_candle(0), _candle(1)]
        stats = compute_dataset_statistics(_dataset(candles), gap_tolerance_factor=2.0)
        assert stats.gap_count == 0


class TestDatasetStatisticsDuplicates:
    def test_duplicate_count(self):
        c0 = _candle(0)
        candles = [c0, _candle(1), _candle(0)]  # duplicate of hour 0
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.duplicate_count == 1
        assert stats.completeness < 1.0

    def test_two_duplicates(self):
        c0 = _candle(0)
        candles = [c0, _candle(1), _candle(0), _candle(2), _candle(1)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.duplicate_count == 2


class TestDatasetStatisticsCoverage:
    def test_daily_coverage_two_of_three_days(self):
        candles = [
            _candle(0),  # Jan 1
            _candle(24),  # Jan 2
            _candle(72),  # Jan 4 (skips Jan 3)
        ]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.trading_days == 3
        assert stats.daily_coverage == pytest.approx(3 / 4, abs=0.001)

    def test_daily_coverage_single_day(self):
        candles = [_candle(0), _candle(1), _candle(2)]
        stats = compute_dataset_statistics(_dataset(candles))
        assert stats.trading_days == 1
        assert stats.daily_coverage == 1.0


class TestDatasetStatisticsRecordTypes:
    def test_tick_dataset_no_interval(self):
        ticks = [
            Tick(symbol="XAU/USD", timestamp=BASE + timedelta(seconds=i),
                 price=2000.0, volume=1.0, bid=1999.0, ask=2001.0)
            for i in range(5)
        ]
        ds = HistoricalDataset(symbol="XAU/USD", timeframe="tick", records=ticks)
        stats = compute_dataset_statistics(ds)
        assert stats.record_count == 5
        assert stats.missing_percentage == 0.0
        assert stats.gap_count == 0
        assert stats.completeness == 1.0
        assert stats.average_spread == pytest.approx(2.0, abs=0.001)

    def test_quote_dataset_spread(self):
        quotes = [
            Quote(symbol="XAU/USD", timestamp=BASE + timedelta(seconds=i),
                  bid=2000.0 + i, ask=2001.0 + i)
            for i in range(4)
        ]
        ds = HistoricalDataset(symbol="XAU/USD", timeframe="tick", records=quotes)
        stats = compute_dataset_statistics(ds)
        assert stats.average_spread == pytest.approx(1.0, abs=0.001)
        assert stats.duplicate_count == 0

    def test_tick_average_volume(self):
        ticks = [
            Tick(symbol="XAU/USD", timestamp=BASE + timedelta(seconds=i),
                 price=2000.0, volume=2.0)
            for i in range(3)
        ]
        ds = HistoricalDataset(symbol="XAU/USD", timeframe="tick", records=ticks)
        stats = compute_dataset_statistics(ds)
        assert stats.average_volume == pytest.approx(2.0, abs=0.001)

    def test_unknown_timeframe(self):
        candles = [_candle(i) for i in range(4)]
        ds = HistoricalDataset(symbol="XAU/USD", timeframe="1x", records=candles)
        stats = compute_dataset_statistics(ds)
        assert stats.missing_percentage == 0.0
        assert stats.gap_count == 0
        assert stats.completeness == 1.0


class TestDatasetStatisticsDeterminism:
    def test_deterministic(self):
        candles = [_candle(i) for i in range(10)]
        ds1 = _dataset(candles)
        ds2 = _dataset([_candle(i) for i in range(10)])
        s1 = compute_dataset_statistics(ds1)
        s2 = compute_dataset_statistics(ds2)
        assert s1.to_dict() == s2.to_dict()

    def test_pure_no_mutation(self):
        candles = [_candle(i) for i in range(10)]
        ds = _dataset(candles)
        before = [c.id for c in ds._records]
        compute_dataset_statistics(ds)
        after = [c.id for c in ds._records]
        assert before == after

    def test_serialization_roundtrip(self):
        candles = [_candle(i, spread=5.0) for i in range(6)]
        stats = compute_dataset_statistics(_dataset(candles))
        data = stats.to_dict()
        restored = DatasetStatistics.from_dict(data)
        assert restored.to_dict() == data
        assert restored.record_count == 6
        assert restored.average_spread == pytest.approx(5.0, abs=0.001)

    def test_statistics_feed_metadata(self):
        candles = [_candle(i) for i in range(4)]
        ds = _dataset(candles)
        stats = compute_dataset_statistics(ds)
        meta = {
            "record_count": stats.record_count,
            "completeness": stats.completeness,
            "trading_days": stats.trading_days,
        }
        assert meta["record_count"] == 4
        assert meta["completeness"] == 1.0
        assert meta["trading_days"] == 1
