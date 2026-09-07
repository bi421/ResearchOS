"""BTC/USDT experiment and validation boundary.

The BTC experiment reuses the deterministic Phase 5.1 statistical primitive
without changing its scientific decision rule. BTC-specific configuration and
validation live here so the crypto entrypoint does not contain placeholder
TODOs or silently pretend that XAUUSD is BTC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from researchos.experiments.phase51.experiment import Phase51Config, run_phase51
from researchos.experiments.phase51.contracts import Outcome, Phase51Result


@dataclass(frozen=True)
class BtcUsdtExperimentConfig:
    """BTC/USDT configuration mapped onto the deterministic Phase 5.1 core."""

    timeframe: str = "1h"
    horizon: int = 5
    threshold: float = 0.0
    train_size: int = 1200
    validation_size: int = 200
    step_size: int = 200
    n_bins: int = 10
    min_sample_count: int = 100
    significance_level: float = 0.05
    spread_spec: str = "fixed:0.0"
    slippage_spec: str = "fixed:0.0"
    commission_spec: str = "fixed:0.0"
    cost_applied: bool = True
    estimator_feature: int | None = None

    def to_phase51(self) -> Phase51Config:
        """Return the shared deterministic experiment configuration."""
        return Phase51Config(
            symbol="BTCUSDT",
            timeframe=self.timeframe,
            horizon=self.horizon,
            threshold=self.threshold,
            train_size=self.train_size,
            validation_size=self.validation_size,
            step_size=self.step_size,
            n_bins=self.n_bins,
            min_sample_count=self.min_sample_count,
            significance_level=self.significance_level,
            spread_spec=self.spread_spec,
            slippage_spec=self.slippage_spec,
            commission_spec=self.commission_spec,
            cost_applied=self.cost_applied,
            estimator_feature=self.estimator_feature,
        )


class BtcUsdtExperiment:
    """Run the shared deterministic predictive-value experiment on BTC/USDT."""

    def __init__(self, config: BtcUsdtExperimentConfig | None = None) -> None:
        self.config = config or BtcUsdtExperimentConfig()

    def run(
        self,
        close: Sequence[float],
        high: Sequence[float],
        low: Sequence[float],
        volume: Sequence[float],
    ) -> Phase51Result:
        """Execute BTC/USDT using the frozen Phase 5.1 scientific primitive."""
        return run_phase51(
            close,
            high,
            low,
            volume,
            self.config.to_phase51(),
        )


@dataclass(frozen=True)
class BtcUsdtValidationReport:
    """Deterministic structural validation of a BTC experiment result."""

    valid: bool
    reasons: tuple[str, ...]
    outcome: str
    sample_count: int


class BtcUsdtValidator:
    """Validate the contract-level integrity of a BTC/USDT experiment result."""

    def validate(self, result: Phase51Result) -> BtcUsdtValidationReport:
        """Reject wrong-symbol or incomplete results without changing the verdict."""
        reasons: list[str] = []
        if result.symbol.upper() != "BTCUSDT":
            reasons.append("result symbol is not BTCUSDT")
        if result.validation is None:
            reasons.append("experiment validation flags are missing")
        if result.outcome == Outcome.BLOCKED:
            reasons.append("BTC/USDT dataset was insufficient for the experiment")
        sample_count = result.model.sample_count if result.model is not None else 0
        if result.outcome != Outcome.BLOCKED and sample_count <= 0:
            reasons.append("validated result contains no samples")
        return BtcUsdtValidationReport(
            valid=not reasons,
            reasons=tuple(reasons),
            outcome=result.outcome.value,
            sample_count=sample_count,
        )


__all__ = [
    "BtcUsdtExperimentConfig",
    "BtcUsdtExperiment",
    "BtcUsdtValidationReport",
    "BtcUsdtValidator",
]
