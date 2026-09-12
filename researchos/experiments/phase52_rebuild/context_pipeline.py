"""Production orchestration for context-aware Phase 5.2 feature construction.

The context dataset is feature state only: its observations are never emitted as
research samples. Research observations remain the only rows eligible for labels,
training, validation, and the minimum-sample gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .context_dataset import load_context_daily_observations
from .context_features import ContextFeatureAudit, build_context_feature_dataset
from .daily_dataset import DailyObservation, build_daily_common_dataset
from .feature_contract import FEATURE_SET_NAMES, Phase52FeatureContract
from .feature_dataset import FeatureDataset


@dataclass(frozen=True)
class ContextAwareFeatureBuild:
    """Immutable result of the production context-aware feature build."""

    context_observations: tuple[DailyObservation, ...]
    research_observations: tuple[DailyObservation, ...]
    datasets: dict[str, FeatureDataset]
    audits: dict[str, ContextFeatureAudit]

    @property
    def research_sample_count(self) -> int:
        return len(self.research_observations)

    @property
    def usable_sample_count(self) -> int:
        counts = {audit.emitted_rows for audit in self.audits.values()}
        if len(counts) != 1:
            raise AssertionError("feature-set context audits disagree on emitted sample count")
        return counts.pop()

    @property
    def context_sample_count(self) -> int:
        return len(self.context_observations)

    def validate(self, contract: Phase52FeatureContract) -> None:
        """Fail closed on context/research boundary and sample-accounting invariants."""
        if not self.context_observations:
            raise ValueError("context observations cannot be empty")
        if self.context_observations[-1].day >= self.research_observations[0].day:
            raise ValueError("context must end strictly before research starts")
        if self.context_sample_count < contract.warmup:
            raise ValueError(
                f"context has {self.context_sample_count} rows; "
                f"{contract.warmup} warm-up rows are required"
            )
        expected = max(0, self.research_sample_count - contract.horizon)
        if self.usable_sample_count != expected:
            raise AssertionError(
                f"context-aware sample accounting mismatch: expected {expected}, "
                f"got {self.usable_sample_count}"
            )
        for feature_set in FEATURE_SET_NAMES:
            dataset = self.datasets[feature_set]
            audit = self.audits[feature_set]
            if not audit.invariant_ok:
                raise AssertionError(f"context audit failed for {feature_set}")
            if dataset.metadata.get("context_is_feature_state_only") is not True:
                raise AssertionError(f"context emitted as samples for {feature_set}")
            if dataset.metadata.get("context_rows_emitted") is not False:
                raise AssertionError(f"context emission contract missing for {feature_set}")
            if dataset.metadata.get("no_interpolation_or_forward_fill") is not True:
                raise AssertionError(f"repair contract missing for {feature_set}")


def build_context_aware_feature_datasets(
    context_xau_path: str | Path,
    context_dxy_path: str | Path,
    us10y_path: str | Path,
    vix_path: str | Path,
    research_xau_path: str | Path,
    research_dxy_path: str | Path,
    *,
    contract: Phase52FeatureContract | None = None,
) -> ContextAwareFeatureBuild:
    """Build all Phase 5.2 research datasets using pre-research context state.

    The context XAU source must use the same canonical MT5 schema as the
    research XAU source. Context observations are loaded from an exact
    four-way intersection and are consumed only to initialize feature state.
    """
    contract = contract or Phase52FeatureContract()
    context = load_context_daily_observations(
        context_xau_path,
        context_dxy_path,
        us10y_path,
        vix_path,
    )
    research = build_daily_common_dataset(
        research_xau_path,
        research_dxy_path,
        us10y_path,
        vix_path,
    )
    if not context:
        raise ValueError("no exact four-way context observations available")
    if not research:
        raise ValueError("no exact four-way research observations available")
    if context[-1].day >= research[0].day:
        raise ValueError("context must end strictly before research starts")
    if len(context) < contract.warmup:
        raise ValueError(
            f"context has {len(context)} rows; {contract.warmup} warm-up rows are required"
        )

    datasets: dict[str, FeatureDataset] = {}
    audits: dict[str, ContextFeatureAudit] = {}
    for feature_set in FEATURE_SET_NAMES:
        dataset, audit = build_context_feature_dataset(
            context,
            research,
            feature_set,
            contract,
        )
        datasets[feature_set] = dataset
        audits[feature_set] = audit

    result = ContextAwareFeatureBuild(
        context_observations=context,
        research_observations=research,
        datasets=datasets,
        audits=audits,
    )
    result.validate(contract)
    return result


__all__ = [
    "ContextAwareFeatureBuild",
    "build_context_aware_feature_datasets",
]
