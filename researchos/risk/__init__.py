"""ResearchOS decision-risk boundary.

This package is a pure, research-only sizing layer. It consumes a validated
research probability plus account, payoff, and risk-policy inputs and returns
an immutable risk calculation. It never places orders or depends on a broker.
"""

from researchos.risk.adapters import risk_input_from_probability
from researchos.risk.contracts import (
    RiskCalculation,
    RiskInput,
    RiskPolicy,
    TradeStatistics,
)
from researchos.risk.engine import calculate_risk

__all__ = [
    "RiskCalculation",
    "RiskInput",
    "RiskPolicy",
    "TradeStatistics",
    "calculate_risk",
    "risk_input_from_probability",
]
