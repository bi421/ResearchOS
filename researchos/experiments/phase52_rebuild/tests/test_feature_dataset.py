from datetime import date, timedelta

from researchos.experiments.phase52_rebuild.daily_dataset import DailyObservation
from researchos.experiments.phase52_rebuild.feature_contract import Phase52FeatureContract
from researchos.experiments.phase52_rebuild.feature_dataset import build_feature_dataset


def _observations(n: int = 70) -> tuple[DailyObservation, ...]:
    start = date(2021, 1, 1)
    return tuple(
        DailyObservation(
            day=(start + timedelta(days=i)).isoformat(),
            timestamp=f"{(start + timedelta(days=i)).isoformat()}T00:00:00Z",
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.0 + i,
            tick_volume=1000.0 + i,
            spread=1.0,
            real_volume=2000.0 + i,
            vwap=100.0 + i + 0.25,
            dxy=90.0 + i * 0.1,
            us10y=1.0 + i * 0.01,
            vix=20.0 + i * 0.05,
            m1_rows=1440,
        )
        for i in range(n)
    )


def test_feature_dataset_accounting_and_prediction_timing() -> None:
    contract = Phase52FeatureContract(train_size=50, validation_size=20)
    dataset = build_feature_dataset(_observations(), "PRICE_ALL", contract)

    assert dataset.sample_count == 5
    assert dataset.feature_count == 28
    assert dataset.source_days[0] == "2021-03-02"
    assert dataset.source_days[-1] == "2021-03-06"
    assert dataset.prediction_timestamps[0] == "2021-03-03T00:00:00Z"
    assert dataset.prediction_timestamps[-1] == "2021-03-07T00:00:00Z"
    assert dataset.metadata["prediction_timing"] == "after_utc_day_close"
    assert (
        dataset.metadata["macro_timing_contract"]
        == "same_day_eod_observation_consumed_after_day_close"
    )
    assert dataset.rows[0][13] == 160.25


def test_future_observation_cannot_change_an_earlier_feature_row() -> None:
    contract = Phase52FeatureContract(train_size=50, validation_size=20)
    base = _observations()
    changed = list(base)
    changed[-1] = DailyObservation(
        day=changed[-1].day,
        timestamp=changed[-1].timestamp,
        open=999999.0,
        high=999999.0,
        low=999998.0,
        close=999999.0,
        tick_volume=999999.0,
        spread=99.0,
        real_volume=999999.0,
        dxy=999.0,
        us10y=99.0,
        vix=99.0,
        m1_rows=1440,
    )
    a = build_feature_dataset(base, "PRICE_ALL", contract)
    b = build_feature_dataset(tuple(changed), "PRICE_ALL", contract)

    assert a.rows[:-1] == b.rows[:-1]
    assert a.labels[:-1] == b.labels[:-1]
    assert a.source_days[:-1] == b.source_days[:-1]


def test_feature_sets_are_isolated() -> None:
    contract = Phase52FeatureContract(train_size=50, validation_size=20)
    observations = _observations()
    price_only = build_feature_dataset(observations, "PRICE_ONLY", contract)
    dxy = build_feature_dataset(observations, "PRICE_DXY", contract)
    us10y = build_feature_dataset(observations, "PRICE_US10Y", contract)
    vix = build_feature_dataset(observations, "PRICE_VIX", contract)
    all_features = build_feature_dataset(observations, "PRICE_ALL", contract)

    assert price_only.feature_count == 19
    assert dxy.feature_count == 22
    assert us10y.feature_count == 22
    assert vix.feature_count == 22
    assert all_features.feature_count == 28
    assert price_only.rows == tuple(row[:19] for row in dxy.rows)
    assert price_only.rows == tuple(row[:19] for row in all_features.rows)
