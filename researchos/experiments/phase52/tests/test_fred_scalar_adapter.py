from datetime import timezone

from researchos.experiments.phase52.timestamp_adapter import (
    load_fred_scalar_series_from_text,
)


def test_fred_scalar_series_parses_date_and_value_without_ohlc_fabrication():
    text = "observation_date,DGS10\n2021-01-04,0.93\n2021-01-05,0.94\n"

    observations = load_fred_scalar_series_from_text(text)

    assert observations is not None
    assert len(observations) == 2
    assert observations[0].timestamp.isoformat() == "2021-01-04T00:00:00+00:00"
    assert observations[0].timestamp.tzinfo == timezone.utc
    assert observations[0].close == 0.93
    assert observations[1].close == 0.94


def test_fred_scalar_series_excludes_missing_marker_without_repair():
    text = "observation_date,VIXCLS\n2021-01-04,25.67\n2021-01-05,.\n2021-01-06,26.12\n"

    observations = load_fred_scalar_series_from_text(text)

    assert observations is not None
    assert [item.close for item in observations] == [25.67, 26.12]
    assert [item.timestamp.isoformat() for item in observations] == [
        "2021-01-04T00:00:00+00:00",
        "2021-01-06T00:00:00+00:00",
    ]


def test_non_fred_ohlc_csv_is_not_claimed_as_scalar_series():
    text = "timestamp,open,high,low,close\n2021-01-04,1,2,0,1.5\n"

    assert load_fred_scalar_series_from_text(text) is None
