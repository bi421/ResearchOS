from __future__ import annotations

from datetime import date, timedelta

import pytest

from researchos.experiments.phase52_rebuild.context_features import (
    ContextFeatureAudit,
)
from researchos.experiments.phase52_rebuild.context_pipeline import (
    ContextAwareFeatureBuild,
)
from researchos.experiments.phase52_rebuild.daily_dataset import DailyObservation
from researchos.experiments.phase52_rebuild.feature_contract import (
    FEATURE_SET_NAMES,
    Phase52FeatureContract,
)
from researchos.experiments.phase52_rebuild.feature_dataset import FeatureDataset


def _obs(day_index: int) -> DailyObservation:
    day = date(2020, 1, 1) + timedelta(days=day_index)
    iso = day.isoformat()
    return DailyObservation(
        day=iso,
        timestamp=f"{iso}T00:00:00Z",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        tick_volume=100.0,
        spread=1.0,
        real_volume=0.0,
        vwap=100.0,
        dxy=100.0,
        us10y=1.0,
        vix=20.0,
        m1_rows=1440,
    )


def _build(context_count: int = 60, research_count: int = 10) -> ContextAwareFeatureBuild:
    context = tuple(_obs(i) for i in range(context_count))
    research = tuple(_obs(context_count + i) for i in range(research_count))
    datasets = {
        name: FeatureDataset(
            feature_set=name,
            feature_names=("x",),
            rows=tuple((1.0,) for _ in range(research_count - 5)),
            labels=tuple(1 for _ in range(research_count - 5)),
            source_days=tuple(o.day for o in research[:-5]),
            prediction_timestamps=tuple(o.timestamp for o in research[:-5]),
            metadata={
                "context_is_feature_state_only": True,
                "context_rows_emitted": False,
                "no_interpolation_or_forward_fill": True,
            },
        )
        for name in FEATURE_SET_NAMES
    }
    audits = {
        name: ContextFeatureAudit(
            context_rows=context_count,
            research_rows=research_count,
            warmup_rows=60,
            label_horizon=5,
            emitted_rows=research_count - 5,
            expected_emitted_rows=research_count - 5,
            context_sufficient=context_count >= 60,
        )
        for name in FEATURE_SET_NAMES
    }
    return ContextAwareFeatureBuild(context, research, datasets, audits)


def test_context_build_validates_research_only_sample_accounting() -> None:
    result = _build()
    result.validate(Phase52FeatureContract(warmup=60, horizon=5, train_size=5, validation_size=5))
    assert result.context_sample_count == 60
    assert result.research_sample_count == 10
    assert result.usable_sample_count == 5


def test_context_build_rejects_overlap() -> None:
    result = _build()
    overlapping = result.context_observations[:-1] + (result.research_observations[0],)
    bad = ContextAwareFeatureBuild(
        overlapping,
        result.research_observations,
        result.datasets,
        result.audits,
    )
    with pytest.raises(ValueError, match="context must end strictly before research starts"):
        bad.validate(Phase52FeatureContract(warmup=60, horizon=5, train_size=5, validation_size=5))


def test_context_build_rejects_missing_context_warmup() -> None:
    result = _build(context_count=59)
    with pytest.raises(ValueError, match="60 warm-up rows are required"):
        result.validate(Phase52FeatureContract(warmup=60, horizon=5, train_size=5, validation_size=5))
