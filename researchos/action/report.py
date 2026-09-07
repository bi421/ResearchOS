"""Deterministic pre-trade report assembly; no execution logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from researchos.risk.contracts import RiskCalculation

ACTION_SCHEMA_VERSION = "pretrade.v1"


@dataclass(frozen=True)
class PreTradeReport:
    """Immutable human-review package assembled from research and risk outputs."""

    schema_version: str
    asset: str
    direction: str
    probability: float
    risk_amount: float
    risk_fraction: float
    position_size: float | None
    research_valid: bool
    risk_valid: bool
    status: str
    research_id: str | None = None
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "asset": self.asset,
            "direction": self.direction,
            "probability": self.probability,
            "risk_amount": self.risk_amount,
            "risk_fraction": self.risk_fraction,
            "position_size": self.position_size,
            "research_valid": self.research_valid,
            "risk_valid": self.risk_valid,
            "status": self.status,
            "research_id": self.research_id,
            "limitations": list(self.limitations),
        }


def build_pre_trade_report(
    risk: RiskCalculation,
    *,
    research_valid: bool,
    research_limitations: tuple[str, ...] = (),
) -> PreTradeReport:
    """Assemble a review report without making an execution decision.

    A report is ``READY_FOR_HUMAN_REVIEW`` only when the research is marked
    valid and the risk calculation itself completed successfully. Unvalidated
    research is explicitly blocked from appearing trade-ready.
    """
    risk_valid = risk.status == "CALCULATED"
    limitations = tuple(research_limitations)

    if not research_valid:
        status = "BLOCKED_RESEARCH_VALIDATION"
    elif not risk_valid:
        status = "BLOCKED_RISK_CALCULATION"
    elif risk.risk_amount <= 0:
        status = "NO_POSITIVE_RISK_BUDGET"
    else:
        status = "READY_FOR_HUMAN_REVIEW"

    return PreTradeReport(
        schema_version=ACTION_SCHEMA_VERSION,
        asset=risk.asset,
        direction=risk.direction,
        probability=risk.probability,
        risk_amount=risk.risk_amount,
        risk_fraction=risk.final_risk_fraction,
        position_size=risk.position_size,
        research_valid=research_valid,
        risk_valid=risk_valid,
        status=status,
        research_id=risk.research_id,
        limitations=limitations,
    )
