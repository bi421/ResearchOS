"""
ResearchOS Macro Intelligence Layer - Regime Enums
Version: regime/enums/v1
Status: FROZEN
"""

from enum import Enum


class InflationState(str, Enum):
    """
    Inflation regime state.

    States:
    - LOW: Inflation below target
    - TARGET: Inflation at target
    - MODERATE: Inflation moderately above target
    - HIGH: Inflation significantly above target
    - HYPER: Hyperinflation
    - DEFATION: Deflation
    """

    LOW = "low"
    TARGET = "target"
    MODERATE = "moderate"
    HIGH = "high"
    HYPER = "hyper"
    DEFATION = "deflation"

    def is_extreme(self) -> bool:
        """Check if this is an extreme state."""
        return self in (
            InflationState.HYPER,
            InflationState.DEFATION,
        )

    def is_stable(self) -> bool:
        """Check if this is a stable state."""
        return self in (
            InflationState.LOW,
            InflationState.TARGET,
        )

    def get_severity(self) -> int:
        """Get severity score (0-10)."""
        severities = {
            InflationState.DEFATION: 7,
            InflationState.LOW: 2,
            InflationState.TARGET: 0,
            InflationState.MODERATE: 4,
            InflationState.HIGH: 7,
            InflationState.HYPER: 10,
        }
        return severities.get(self, 0)


class GrowthState(str, Enum):
    """
    Economic growth regime state.

    States:
    - RECOVERY: Early recovery
    - EXPANSION: Stable expansion
    - OVERHEATING: Economy overheating
    - STAGFLATION: Stagnation with inflation
    - RECESSION: Economic recession
    - DEPRESSION: Severe depression
    """

    RECOVERY = "recovery"
    EXPANSION = "expansion"
    OVERHEATING = "overheating"
    STAGFLATION = "stagflation"
    RECESSION = "recession"
    DEPRESSION = "depression"

    def is_expansionary(self) -> bool:
        """Check if this is an expansionary state."""
        return self in (
            GrowthState.RECOVERY,
            GrowthState.EXPANSION,
            GrowthState.OVERHEATING,
        )

    def is_contractionary(self) -> bool:
        """Check if this is a contractionary state."""
        return self in (
            GrowthState.RECESSION,
            GrowthState.DEPRESSION,
        )

    def is_normal(self) -> bool:
        """Check if this is a normal state."""
        return self in (
            GrowthState.RECOVERY,
            GrowthState.EXPANSION,
        )

    def get_severity(self) -> int:
        """Get severity score (0-10)."""
        severities = {
            GrowthState.RECOVERY: 1,
            GrowthState.EXPANSION: 0,
            GrowthState.OVERHEATING: 3,
            GrowthState.STAGFLATION: 8,
            GrowthState.RECESSION: 6,
            GrowthState.DEPRESSION: 10,
        }
        return severities.get(self, 0)


class MonetaryState(str, Enum):
    """
    Monetary policy regime state.

    States:
    - DIVE: Dovish policy
    - NEUTRAL: Neutral policy
    - HAWK: Hawkish policy
    - EASING: Policy easing
    - TIGHTENING: Policy tightening
    """

    DIVE = "dove"
    NEUTRAL = "neutral"
    HAWK = "hawk"
    EASING = "easing"
    TIGHTENING = "tightening"

    def is_dovish(self) -> bool:
        """Check if policy is dovish."""
        return self in (
            MonetaryState.DIVE,
            MonetaryState.EASING,
        )

    def is_hawkish(self) -> bool:
        """Check if policy is hawkish."""
        return self in (
            MonetaryState.HAWK,
            MonetaryState.TIGHTENING,
        )

    def is_neutral(self) -> bool:
        """Check if policy is neutral."""
        return self == MonetaryState.NEUTRAL

    def get_severity(self) -> int:
        """Get severity score (0-10)."""
        severities = {
            MonetaryState.DIVE: 2,
            MonetaryState.EASING: 3,
            MonetaryState.NEUTRAL: 0,
            MonetaryState.TIGHTENING: 4,
            MonetaryState.HAWK: 6,
        }
        return severities.get(self, 0)


class LiquidityState(str, Enum):
    """
    Liquidity regime state.

    States:
    - ABUNDANT: Excess liquidity
    - NORMAL: Normal liquidity
    - TIGHT: Tight liquidity
    - CRITICAL: Critical liquidity shortage
    """

    ABUNDANT = "abundant"
    NORMAL = "normal"
    TIGHT = "tight"
    CRITICAL = "critical"

    def is_abundant(self) -> bool:
        """Check if liquidity is abundant."""
        return self in (
            LiquidityState.ABUNDANT,
            LiquidityState.NORMAL,
        )

    def is_constrained(self) -> bool:
        """Check if liquidity is constrained."""
        return self in (
            LiquidityState.TIGHT,
            LiquidityState.CRITICAL,
        )

    def get_severity(self) -> int:
        """Get severity score (0-10)."""
        severities = {
            LiquidityState.ABUNDANT: 0,
            LiquidityState.NORMAL: 1,
            LiquidityState.TIGHT: 5,
            LiquidityState.CRITICAL: 9,
        }
        return severities.get(self, 0)


class EmploymentState(str, Enum):
    """
    Employment regime state.

    States:
    - FULL: Full employment
    - STRONG: Strong employment
    - MODERATE: Moderate employment
    - WEAK: Weak employment
    - CRISS: Employment crisis
    """

    FULL = "full"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    CRISS = "crisis"

    def is_healthy(self) -> bool:
        """Check if employment is healthy."""
        return self in (
            EmploymentState.FULL,
            EmploymentState.STRONG,
        )

    def is_stressed(self) -> bool:
        """Check if employment is stressed."""
        return self in (
            EmploymentState.WEAK,
            EmploymentState.CRISS,
        )

    def get_severity(self) -> int:
        """Get severity score (0-10)."""
        severities = {
            EmploymentState.FULL: 0,
            EmploymentState.STRONG: 1,
            EmploymentState.MODERATE: 3,
            EmploymentState.WEAK: 6,
            EmploymentState.CRISS: 9,
        }
        return severities.get(self, 0)


class RiskState(str, Enum):
    """
    Risk regime state.

    States:
    - LOW: Low risk
    - MODERATE: Moderate risk
    - ELEVATED: Elevated risk
    - HIGH: High risk
    - CRITICAL: Critical risk
    """

    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"

    def is_acceptable(self) -> bool:
        """Check if risk is acceptable."""
        return self in (
            RiskState.LOW,
            RiskState.MODERATE,
        )

    def is_warning(self) -> bool:
        """Check if risk is at warning level."""
        return self == RiskState.ELEVATED

    def is_critical(self) -> bool:
        """Check if risk is critical."""
        return self in (
            RiskState.HIGH,
            RiskState.CRITICAL,
        )

    def get_severity(self) -> int:
        """Get severity score (0-10)."""
        severities = {
            RiskState.LOW: 0,
            RiskState.MODERATE: 2,
            RiskState.ELEVATED: 5,
            RiskState.HIGH: 8,
            RiskState.CRITICAL: 10,
        }
        return severities.get(self, 0)


class RegimeSeverity(str, Enum):
    """
    Overall regime severity classification.

    Severity levels:
    - NORMAL: Normal conditions
    - ATTENTION: Require attention
    - WARNING: Warning conditions
    - CRITICAL: Critical conditions
    """

    NORMAL = "normal"
    ATTENTION = "attention"
    WARNING = "warning"
    CRITICAL = "critical"

    def is_serious(self) -> bool:
        """Check if severity is serious."""
        return self in (
            RegimeSeverity.WARNING,
            RegimeSeverity.CRITICAL,
        )

    def get_score(self) -> int:
        """Get numeric severity score."""
        scores = {
            RegimeSeverity.NORMAL: 0,
            RegimeSeverity.ATTENTION: 3,
            RegimeSeverity.WARNING: 6,
            RegimeSeverity.CRITICAL: 10,
        }
        return scores.get(self, 0)


class RegimeTransitionType(str, Enum):
    """
    Type of regime transition.

    Transition types:
    - GRADUAL: Gradual transition
    - ABRUPT: Abrupt transition
    - CYCLICAL: Cyclical transition
    - STRUCTURAL: Structural transition
    """

    GRADUAL = "gradual"
    ABRUPT = "abrupt"
    CYCLICAL = "cyclical"
    STRUCTURAL = "structural"

    def is_sudden(self) -> bool:
        """Check if transition is sudden."""
        return self in (
            RegimeTransitionType.ABRUPT,
            RegimeTransitionType.STRUCTURAL,
        )
