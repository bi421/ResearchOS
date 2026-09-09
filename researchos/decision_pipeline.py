"""Canonical ResearchOS Block 2 -> Block 3 -> Block 4 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from researchos.action.report import PreTradeReport, build_pre_trade_report
from researchos.decision_engine.probability import ProbabilityAssessment
from researchos.risk.adapters import risk_input_from_probability
from researchos.risk.contracts import RiskPolicy, TradeStatistics
from researchos.risk.engine import calculate_risk


@dataclass(frozen=True)
class DecisionPipelineInput:
    """Explicit API-first input for the canonical decision pipeline."""

    assessment: ProbabilityAssessment | dict[str, Any]
    asset: str
    direction: str
    account_equity: float
    trade_statistics: TradeStatistics
    research_valid: bool
    research_limitations: tuple[str, ...] = ()
    risk_policy: RiskPolicy = RiskPolicy()
    risk_per_unit: float | None = None
    probability_calibration_status: str | None = None


def _calibration_status(request: DecisionPipelineInput) -> str | None:
    """Resolve explicit calibration evidence without inventing a status.

    A pipeline-level value has precedence. Otherwise a status already attached
    to the ProbabilityAssessment (or its serialized form) is preserved.
    """
    if request.probability_calibration_status is not None:
        return request.probability_calibration_status
    if isinstance(request.assessment, ProbabilityAssessment):
        return request.assessment.probability_calibration_status
    return request.assessment.get("probability_calibration_status")


def run_decision_pipeline(request: DecisionPipelineInput) -> PreTradeReport:
    """Run probability -> risk -> human-review report deterministically."""
    risk_input = risk_input_from_probability(
        request.assessment,
        asset=request.asset,
        direction=request.direction,
        account_equity=request.account_equity,
        trade_statistics=request.trade_statistics,
        risk_policy=request.risk_policy,
        risk_per_unit=request.risk_per_unit,
        probability_calibration_status=_calibration_status(request),
    )
    risk = calculate_risk(risk_input)
    return build_pre_trade_report(
        risk,
        research_valid=request.research_valid,
        research_limitations=request.research_limitations,
    )
