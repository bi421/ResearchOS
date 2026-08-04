"""
ResearchOS Macro Intelligence Layer - Feature Engineering Enums
Version: feat/enums/v1
Status: FROZEN
"""

from enum import Enum, auto
from typing import Optional


class FeatureCategory(str, Enum):
    """
    Feature category enumeration.
    
    Categories:
    - TREND: Trend-based features
    - SURPRISE: Surprise-based features
    - YIELD: Yield curve features
    - INFLATION: Inflation features
    - LABOR: Labor market features
    - RISK: Risk features
    - DOLLAR: Dollar features
    - LIQUIDITY: Liquidity features
    """
    TREND = "trend"
    SURPRISE = "surprise"
    YIELD = "yield"
    INFLATION = "inflation"
    LABOR = "labor"
    RISK = "risk"
    DOLLAR = "dollar"
    LIQUIDITY = "liquidity"
    
    def is_macro_feature(self) -> bool:
        """Check if this is a macro feature."""
        return True
    
    def get_description(self) -> str:
        """Get human-readable description."""
        descriptions = {
            FeatureCategory.TREND: "Trend-based features (mean, median, std, EMA, momentum)",
            FeatureCategory.SURPRISE: "Surprise features (actual vs forecast, z-scores)",
            FeatureCategory.YIELD: "Yield curve features (spreads, steepening, inversion)",
            FeatureCategory.INFLATION: "Inflation features (momentum, persistence)",
            FeatureCategory.LABOR: "Labor market features (NFP, unemployment, JOLTS)",
            FeatureCategory.RISK: "Risk features (VIX, MOVE, volatility regime)",
            FeatureCategory.DOLLAR: "Dollar features (DXY trend, momentum, volatility)",
            FeatureCategory.LIQUIDITY: "Liquidity features (issuance, SOFR, M2)",
        }
        return descriptions.get(self, "")


class FeatureType(str, Enum):
    """
    Feature type enumeration.
    
    Types:
    - SCALAR: Single value
    - VECTOR: Multiple values
    - RATIO: Ratio of two values
    - SPREAD: Difference between two values
    - PERCENTILE: Percentile rank
    - ZSCORE: Z-score标准化
    """
    SCALAR = "scalar"
    VECTOR = "vector"
    RATIO = "ratio"
    SPREAD = "spread"
    PERCENTILE = "percentile"
    ZSCORE = "zscore"
    
    def is_univariate(self) -> bool:
        """Check if feature is univariate."""
        return self in (
            FeatureType.SCALAR,
            FeatureType.PERCENTILE,
            FeatureType.ZSCORE,
        )
    
    def is_bivariate(self) -> bool:
        """Check if feature is bivariate."""
        return self in (
            FeatureType.RATIO,
            FeatureType.SPREAD,
        )


class FeatureState(str, Enum):
    """
    Feature state enumeration.
    
    States:
    - CALCULATING: Feature is being calculated
    - READY: Feature is ready for use
    - STALE: Feature needs recalculation
    - ERROR: Feature calculation failed
    - DEPRECATED: Feature is deprecated
    """
    CALCULATING = "calculating"
    READY = "ready"
    STALE = "stale"
    ERROR = "error"
    DEPRECATED = "deprecated"
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (
            FeatureState.READY,
            FeatureState.ERROR,
            FeatureState.DEPRECATED,
        )
    
    def is_computable(self) -> bool:
        """Check if feature can be calculated."""
        return self in (
            FeatureState.CALCULATING,
            FeatureState.READY,
            FeatureState.STALE,
        )


class CalculationMethod(str, Enum):
    """
    Calculation method enumeration.
    
    Methods:
    - ROLLING: Rolling window calculation
    - EXPONENTIAL: Exponential weighting
    - CUMULATIVE: Cumulative calculation
    - POINT: Point-in-time calculation
    - DERIVATIVE: Derivative-based calculation
    """
    ROLLING = "rolling"
    EXPONENTIAL = "exponential"
    CUMULATIVE = "cumulative"
    POINT = "point"
    DERIVATIVE = "derivative"
    
    def requires_history(self) -> bool:
        """Check if method requires historical data."""
        return self in (
            CalculationMethod.ROLLING,
            CalculationMethod.EXPONENTIAL,
            CalculationMethod.CUMULATIVE,
            CalculationMethod.DERIVATIVE,
        )


class ValidationRule(str, Enum):
    """
    Validation rule enumeration.
    
    Rules:
    - NO_NAN: No NaN values
    - NO_INF: No infinite values
    - FINITE: Values are finite
    - RANGE: Values within expected range
    - MONOTONIC: Monotonic sequence
    - SMOOTH: Smooth transitions
    """
    NO_NAN = "no_nan"
    NO_INF = "no_inf"
    FINITE = "finite"
    RANGE = "range"
    MONOTONIC = "monotonic"
    SMOOTH = "smooth"


class FeatureVersionCompatibility(str, Enum):
    """
    Feature version compatibility.
    
    Compatibility:
    - FORWARD: Forward compatible
    - BACKWARD: Backward compatible
    - BREAKING: Breaking change
    """
    FORWARD = "forward"
    BACKWARD = "backward"
    BREAKING = "breaking"
