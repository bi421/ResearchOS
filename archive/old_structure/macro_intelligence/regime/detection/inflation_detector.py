"""
ResearchOS Macro Intelligence Layer - Inflation Detector

Deterministic inflation regime detection using trend, momentum,
z-score, and historical percentile analysis.

Algorithm version: infl-det/v2.0.0
"""

from __future__ import annotations

from macro_intelligence.regime.detection.models import (
    DetectionEvidence,
    FeatureVector,
    InflationSignal,
)

ALGORITHM_VERSION = "infl-det/v2.0.0"


# =============================================================================
# Thresholds (deterministic, permanent)
# =============================================================================

# CPI/PCE thresholds (year-over-year %)
_INFLATION_LOW_MAX = 1.5  # Below this: LOW
_INFLATION_TARGET_MIN = 1.5  # Target range: 1.5% - 2.5%
_INFLATION_TARGET_MAX = 2.5
_INFLATION_ELEVATED_MIN = 2.5  # Above target: ELEVATED/RISING
_INFLATION_HIGH_MIN = 4.0  # High inflation
_INFLATION_DEFLOTION_MAX = -0.5  # Below this: DEFLATIONARY

# Momentum thresholds (% change in trend direction)
_MOMENTUM_RISING_MIN = 0.3  # Sustained upward momentum
_MOMENTUM_FALLING_MIN = -0.3  # Sustained downward momentum

# Z-score thresholds
_Z_SCORE_LOW = -1.5  # Below this: LOW signal
_Z_SCORE_HIGH = 1.5  # Above this: HIGH signal

# Percentile thresholds
_PERCENTILE_LOW = 20  # Bottom 20%: LOW
_PERCENTILE_HIGH = 80  # Top 20%: HIGH


def detect_inflation(features: FeatureVector) -> DetectionEvidence:
    """
    Detect inflation regime from feature vector.

    Uses: trend direction, momentum, z-score, historical percentile.

    Args:
        features: FeatureVector with inflation-related data.

    Returns:
        DetectionEvidence with inflation regime signal.
    """
    # Use the primary inflation measure (CPI core if available, else CPI)
    primary_value = _get_primary_inflation_value(features)

    if primary_value is None:
        return _build_evidence(
            signal=InflationSignal.STABLE.value,
            confidence=0.0,
            factors={"primary_value": None},
        )

    # Multi-factor analysis
    factors: dict[str, float] = {
        "primary_value": primary_value,
        "core_cpi": features.cpi_core_yoy or 0.0,
        "pce": features.pce_yoy or 0.0,
    }

    # --- Factor 1: Level classification ---
    level_score = _classify_inflation_level(primary_value, factors)

    # --- Factor 2: Trend direction ---
    trend_score = _classify_inflation_trend(features, factors)

    # --- Factor 3: Momentum ---
    momentum_score = _classify_inflation_momentum(features, factors)

    # --- Factor 4: Z-score ---
    z_score = features.inflation_z_score
    if z_score is not None:
        factors["z_score"] = z_score

    # --- Factor 5: Percentile ---
    percentile = features.inflation_percentile
    if percentile is not None:
        factors["percentile"] = percentile

    # Combine signals (deterministic voting)
    signal = _combine_inflation_signals(level_score, trend_score, momentum_score)
    confidence = _compute_inflation_confidence(level_score, trend_score, momentum_score, z_score, percentile)

    return _build_evidence(signal, confidence, factors, primary_value)


def _get_primary_inflation_value(features: FeatureVector) -> float | None:
    """Get the primary inflation measure from features."""
    if features.cpi_core_yoy is not None:
        return features.cpi_core_yoy
    if features.cpi_yoy is not None:
        return features.cpi_yoy
    if features.pce_core_yoy is not None:
        return features.pce_core_yoy
    if features.pce_yoy is not None:
        return features.pce_yoy
    return None


def _classify_inflation_level(value: float, factors: dict[str, float]) -> str:
    """Classify inflation by level."""
    if value <= _INFLATION_DEFLOTION_MAX:
        return InflationSignal.DEFLATIONARY.value
    elif value < _INFLATION_LOW_MAX:
        return InflationSignal.LOW.value
    elif _INFLATION_TARGET_MIN <= value <= _INFLATION_TARGET_MAX:
        return InflationSignal.STABLE.value
    elif value < _INFLATION_HIGH_MIN:
        return InflationSignal.RISING.value
    else:
        return InflationSignal.HIGH.value


def _classify_inflation_trend(features: FeatureVector, factors: dict[str, float]) -> str:
    """Classify inflation trend direction."""
    trend = features.inflation_trend
    if trend is None:
        return "neutral"

    factors["trend"] = trend

    if trend == "UPWARD":
        return InflationSignal.RISING.value
    elif trend == "DOWNWARD":
        return InflationSignal.FALLING.value
    else:
        return InflationSignal.STABLE.value


def _classify_inflation_momentum(features: FeatureVector, factors: dict[str, float]) -> str:
    """Classify inflation momentum."""
    momentum = features.inflation_momentum
    if momentum is None:
        return "neutral"

    factors["momentum"] = momentum

    if momentum >= _MOMENTUM_RISING_MIN:
        return InflationSignal.RISING.value
    elif momentum <= _MOMENTUM_FALLING_MIN:
        return InflationSignal.FALLING.value
    else:
        return InflationSignal.STABLE.value


def _combine_inflation_signals(level: str, trend: str, momentum: str) -> str:
    """
    Combine inflation signals deterministically.

    Priority: DEFLATIONARY/HIGH > RISING/FALLING > STABLE/LOW
    """
    # Strong signals override
    if level == InflationSignal.DEFLATIONARY.value:
        return InflationSignal.DEFLATIONARY.value
    if level == InflationSignal.HIGH.value:
        return InflationSignal.HIGH.value

    # Trend and momentum alignment
    if trend == momentum:
        return trend

    # Trend overrides level
    if trend in (InflationSignal.RISING.value, InflationSignal.FALLING.value):
        return trend

    # Level classification
    if level in (InflationSignal.LOW.value, InflationSignal.STABLE.value):
        return level

    return InflationSignal.STABLE.value


def _compute_inflation_confidence(
    level: str,
    trend: str,
    momentum: str,
    z_score: float | None,
    percentile: float | None,
) -> float:
    """
    Compute detection confidence (0.0 to 1.0).

    Higher confidence when:
    - Multiple signals agree
    - Z-score is extreme
    - Percentile is extreme
    """
    # Base confidence from signal agreement
    agreement_count = sum(1 for s in [level, trend, momentum] if s != "neutral")
    base_confidence = min(0.5 + (agreement_count * 0.15), 0.95)

    # Boost from z-score
    z_boost = 0.0
    if z_score is not None:
        abs_z = abs(z_score)
        if abs_z >= 2.0:
            z_boost = 0.1
        elif abs_z >= 1.5:
            z_boost = 0.05

    # Boost from percentile
    p_boost = 0.0
    if percentile is not None:
        if percentile <= 10 or percentile >= 90:
            p_boost = 0.05
        elif percentile <= 20 or percentile >= 80:
            p_boost = 0.02

    confidence = min(base_confidence + z_boost + p_boost, 1.0)
    return round(confidence, 2)


def _build_evidence(
    signal: str,
    confidence: float,
    factors: dict[str, float],
    primary_value: float | None = None,
    details: str = "",
) -> DetectionEvidence:
    """Build DetectionEvidence from inflation detection."""
    detail_parts = [f"Signal: {signal}"]
    if primary_value is not None:
        detail_parts.append(f"Primary: {primary_value:.2f}%")
    if details:
        detail_parts.append(details)

    return DetectionEvidence(
        detector_name="inflation_detector",
        signal=signal,
        confidence=confidence,
        contributing_factors=factors,
        algorithm_version=ALGORITHM_VERSION,
        details="; ".join(detail_parts),
    )
