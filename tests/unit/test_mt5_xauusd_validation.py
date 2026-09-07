from datetime import datetime, timezone

from researchos.data_engine.mt5_xauusd_validation import validate_m1_rows


def row(ts: int, **overrides):
    value = {
        "time": ts,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "tick_volume": 10,
        "spread": 5,
        "real_volume": 0,
    }
    value.update(overrides)
    return value


def test_valid_m1_rows_pass_without_forcing_24_7_continuity():
    start = int(datetime(2025, 1, 2, tzinfo=timezone.utc).timestamp())
    rows = [row(start), row(start + 60), row(start + 3600)]
    report = validate_m1_rows(rows, start_epoch=start, end_epoch=start + 3600)

    assert report.passed_integrity
    assert report.rows == 3
    assert report.duplicate_timestamps == 0
    assert report.gap_count_over_60s == 1
    assert report.max_gap_seconds == 3540


def test_duplicate_timestamp_is_integrity_failure():
    start = 1_735_779_600
    report = validate_m1_rows(
        [row(start), row(start)], start_epoch=start, end_epoch=start + 60
    )
    assert report.duplicate_timestamps == 1
    assert not report.passed_integrity


def test_invalid_ohlc_is_rejected():
    start = 1_735_779_600
    report = validate_m1_rows(
        [row(start, high=98.0)], start_epoch=start, end_epoch=start
    )
    assert report.invalid_ohlc_rows == 1
    assert not report.passed_integrity


def test_negative_volume_and_spread_are_rejected():
    start = 1_735_779_600
    report = validate_m1_rows(
        [row(start, tick_volume=-1, spread=-2)], start_epoch=start, end_epoch=start
    )
    assert report.invalid_volume_rows == 1
    assert report.negative_spread_rows == 1
    assert not report.passed_integrity


def test_out_of_requested_range_is_rejected():
    start = 1_735_779_600
    report = validate_m1_rows(
        [row(start - 60)], start_epoch=start, end_epoch=start + 60
    )
    assert report.out_of_range_rows == 1
    assert not report.passed_integrity
