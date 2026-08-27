"""
ResearchOS Macro Intelligence Layer - Regime Detection Package

Provides deterministic regime detection algorithms for the
Macro Intelligence Layer.

All detectors are:
- Pure functions (no mutable state)
- Deterministic (same input always produces same output)
- Stateless (no caches, no randomness)
- Provenance-preserving (output includes evidence references)

Architecture invariants:
- MIL-REG-005: Detectors are deterministic
- MIL-REG-006: Detector output preserves evidence provenance
- MIL-REG-007: Detector logic does not mutate features
- MIL-REG-008: Algorithm versions are permanent
"""

from __future__ import annotations

from researchos.macro.regime.detection.detector import RegimeDetector
from researchos.macro.regime.detection.employment_detector import detect_employment
from researchos.macro.regime.detection.growth_detector import detect_growth
from researchos.macro.regime.detection.inflation_detector import detect_inflation
from researchos.macro.regime.detection.liquidity_detector import detect_liquidity
from researchos.macro.regime.detection.models import (
    DetectionEvidence,
    EmploymentSignal,
    FeatureVector,
    GrowthSignal,
    InflationSignal,
    LiquiditySignal,
    MonetarySignal,
    RegimeAssessment,
    RiskSignal,
)
from researchos.macro.regime.detection.monetary_detector import detect_monetary
from researchos.macro.regime.detection.risk_detector import detect_risk

__all__ = [
    # Models
    "FeatureVector",
    "DetectionEvidence",
    "RegimeAssessment",
    # Signals
    "InflationSignal",
    "GrowthSignal",
    "MonetarySignal",
    "LiquiditySignal",
    "EmploymentSignal",
    "RiskSignal",
    # Detector
    "RegimeDetector",
    # Individual detectors
    "detect_inflation",
    "detect_growth",
    "detect_monetary",
    "detect_liquidity",
    "detect_employment",
    "detect_risk",
]
