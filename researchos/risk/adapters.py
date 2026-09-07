"""Adapters from ResearchOS Block 2 probability outputs to ``risk.v1``."""

from __future__ import annotations

from typing import Any

from researchos.decision_engine.probability import ProbabilityAssessment
from researchos.risk.contracts import RiskInput, RiskPolicy, TradeStatistics


_DIRECTION_FIELDS = {
    "bullish": "bullish_probability",
    "bearish": "bearish_probability",
}


def risk_input_from_probability(
    assessment: ProbabilityAssessment | dict[str, Any],
    *,
    asset: str,
    direction: str,
    account_equity: float,
    trade_statistics: TradeStatistics,
    risk_policy: RiskPolicy = RiskPolicy(),
    risk_per_unit: float | None = None,
) -> RiskInput:
    """Translate one validated Block 2 assessment into the ``risk.v1`` input.

    The adapter deliberately requires the caller to select a directional
    outcome. Neutral is not silently converted into a trade direction, and the
    adapter does not alter, normalize, or manufacture the probability.

    ``ProbabilityAssessment`` is accepted directly for in-process use or as a
    serialized dictionary for an API-first boundary.
    """
    data = assessment.to_dict() if isinstance(assessment, ProbabilityAssessment) else assessment
    normalized_direction = direction.strip().lower()

    try:
        probability_field = _DIRECTION_FIELDS[normalized_direction]
    except KeyError as exc:
        raise ValueError("direction must be 'bullish' or 'bearish'") from exc

    if "decision_context_id" not in data:
        raise ValueError("probability assessment is missing decision_context_id")
    if "assessment_hash" not in data:
        raise ValueError("probability assessment is missing assessment_hash")

    probability = float(data[probability_field])
    probability_method = str(data.get("calculation_method", "")) or None
    calibration_status = data.get("probability_calibration_status")

    request = RiskInput(
        asset=asset,
        direction=normalized_direction,
        probability=probability,
        account_equity=account_equity,
        trade_statistics=trade_statistics,
        risk_policy=risk_policy,
        risk_per_unit=risk_per_unit,
        research_id=str(data["decision_context_id"]),
        probability_method=probability_method,
        probability_calibration_status=calibration_status,
    )
    request.validate()
    return request
