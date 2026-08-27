"""
ResearchOS Macro Intelligence Layer - Regime Package
"""

from researchos.macro.regime.contracts import (
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
from researchos.macro.regime.enums import (
    EmploymentState,
    GrowthState,
    InflationState,
    LiquidityState,
    MonetaryState,
    RegimeSeverity,
    RegimeTransitionType,
    RiskState,
)
from researchos.macro.regime.interfaces import (
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
