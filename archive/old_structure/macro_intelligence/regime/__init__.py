"""
ResearchOS Macro Intelligence Layer - Regime Package
"""

from macro_intelligence.regime.contracts import (
    EmploymentRegime,
    GrowthRegime,
    # Type aliases
    InflationRegime,
    LiquidityRegime,
    MacroRegime,
    MonetaryRegime,
    RegimeAssessment,
    RegimeConfidence,
    RegimeEvidence,
    RegimeSnapshot,
    RiskRegime,
)
from macro_intelligence.regime.enums import (
    EmploymentState,
    GrowthState,
    InflationState,
    LiquidityState,
    MonetaryState,
    RegimeSeverity,
    RegimeTransitionType,
    RiskState,
)
from macro_intelligence.regime.interfaces import (
    RegimeClassifierInterface,
    RegimeDetectorInterface,
    RegimeScoringInterface,
    RegimeSnapshotInterface,
)

__all__ = [
    # Enums
    "InflationState",
    "GrowthState",
    "MonetaryState",
    "LiquidityState",
    "EmploymentState",
    "RiskState",
    "RegimeSeverity",
    "RegimeTransitionType",
    # Contracts
    "RegimeConfidence",
    "RegimeEvidence",
    "RegimeAssessment",
    "RegimeSnapshot",
    "MacroRegime",
    # Type aliases
    "InflationRegime",
    "GrowthRegime",
    "MonetaryRegime",
    "LiquidityRegime",
    "EmploymentRegime",
    "RiskRegime",
    # Interfaces
    "RegimeDetectorInterface",
    "RegimeClassifierInterface",
    "RegimeScoringInterface",
    "RegimeSnapshotInterface",
]
