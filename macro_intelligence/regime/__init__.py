"""
ResearchOS Macro Intelligence Layer - Regime Package
"""

from macro_intelligence.regime.enums import (
    InflationState,
    GrowthState,
    MonetaryState,
    LiquidityState,
    EmploymentState,
    RiskState,
    RegimeSeverity,
    RegimeTransitionType,
)

from macro_intelligence.regime.contracts import (
    RegimeConfidence,
    RegimeEvidence,
    RegimeAssessment,
    RegimeSnapshot,
    MacroRegime,
    # Type aliases
    InflationRegime,
    GrowthRegime,
    MonetaryRegime,
    LiquidityRegime,
    EmploymentRegime,
    RiskRegime,
)

from macro_intelligence.regime.interfaces import (
    RegimeDetectorInterface,
    RegimeClassifierInterface,
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
