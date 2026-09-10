from datetime import datetime, timezone

from researchos.experiments.phase52.timestamp_adapter import normalize_epoch_timestamp_csv


def test_normalize_epoch_milliseconds_to_utc_iso():
    text = "timestamp,open,high,low,close,volume\n1609718400000,1,2,0,1,10\n1609804800000,1,2,0,1,11\n"

    normalized = normalize_epoch_timestamp_csv(text)

    assert "2021-01-04T00:00:00Z" in normalized
    assert "2021-01-05T00:00:00Z" in normalized
    assert "1609718400000" not in normalized


def test_seconds_and_iso_timestamps_are_supported():
    text = (
        "time,open,high,low,close,volume\n"
        "1609718400,1,2,0,1,10\n"
        "2021-01-05T00:00:00Z,1,2,0,1,11\n"
    )

    normalized = normalize_epoch_timestamp_csv(text)

    assert "2021-01-04T00:00:00Z" in normalized
    assert "2021-01-05T00:00:00Z" in normalized


def test_non_timestamp_csv_is_unchanged():
    text = "date,open,high,low,close\n2021-01-04,1,2,0,1\n"

    assert normalize_epoch_timestamp_csv(text) == text


def test_millisecond_conversion_matches_expected_datetime():
    text = "timestamp,open,high,low,close\n1609718400000,1,2,0,1\n"
    normalized = normalize_epoch_timestamp_csv(text)
    timestamp = normalized.splitlines()[1].split(",", 1)[0]

    assert datetime.fromisoformat(timestamp.replace("Z", "+00:00")) == datetime(2021, 1, 4, tzinfo=timezone.utc)
