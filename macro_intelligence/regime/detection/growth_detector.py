"""
ResearchOS Macro Intelligence Layer - Growth Detector

Deterministic economic growth regime detection using GDP, PMI,
and employment indicators.

Algorithm version: grw-det/v2.0.0
"""

from __future__ import annotations

from macro_intelligence.regime.detection.models import (
    DetectionEvidence,
    FeatureVector,
    GrowthSignal,
)

ALGORITHM_VERSION = "grw-det/v2.0.0"


# =============================================================================
# Thresholds (deterministic, permanent)
# =============================================================================

# GDP thresholds (year-over-year %)
_GDP_CONTRACTION_MAX = 0.0  # Negative or zero: CONTRACTION
_GDP_SLOWDOWN_MIN = 1.0  # Below this: SLOWDOWN
_GDP_EXPANSION_MIN = 2.0  # At or above this: EXPANSION
_GDP_RECOVERY_MIN = 2.5  # Strong recovery threshold

# PMI thresholds (50 is the threshold between expansion/contraction)
_PMI_EXPANSION_MIN = 52.0  # Above this: confirmed expansion
_PMI_CONTRACTION_MAX = 48.0  # Below this: confirmed contraction
_PMI_NEUTRAL_MIN = 48.0  # 48-52: neutral zone

# Growth momentum thresholds (% change)
_MOMENTUM_EXPANSION = 0.5  # Accelerating growth
_MOMENTUM_SLOWDOWN = -0.5  # Decelerating growth


def detect_growth(features: FeatureVector) -> DetectionEvidence:
    """
    Detect growth regime from feature vector.

    Uses: GDP growth, PMI indices, momentum, z-score.

    Args:
        features: FeatureVector with growth-related data.

    Returns:
        DetectionEvidence with growth regime signal.
    """
    gdp = features.gdp_yoy
    pmi_mfg = features.pmi_mfg
    pmi_svc = features.pmi_svc

    if gdp is None and (pmi_mfg is None and pmi_svc is None):
        return _build_evidence(
            signal=GrowthSignal.SLOWDOWN.value,
            confidence=0.0,
            factors={},
        )

    factors: dict[str, float] = {
        "gdp_yoy": gdp or 0.0,
        "pmi_mfg": pmi_mfg or 0.0,
        "pmi_svc": pmi_svc or 0.0,
    }

    # Factor 1: GDP classification
    gdp_score = _classify_gdp(gdp, factors)

    # Factor 2: PMI classification
    pmi_score = _classify_pmi(pmi_mfg, pmi_svc, factors)

    # Factor 3: Momentum
    momentum_score = _classify_momentum(features, factors)

    # Combine signals
    signal = _combine_growth_signals(gdp_score, pmi_score, momentum_score)
    confidence = _compute_growth_confidence(gdp_score, pmi_score, momentum_score, features)

    return _build_evidence(signal, confidence, factors)


def _classify_gdp(gdp: float | None, factors: dict[str, float]) -> str:
    """Classify growth by GDP."""
    if gdp is None:
        return "neutral"

    factors["gdp_yoy"] = gdp

    if gdp >= _GDP_RECOVERY_MIN:
        return GrowthSignal.RECOVERY.value
    elif gdp >= _GDP_EXPANSION_MIN:
        return GrowthSignal.EXPANSION.value
    elif gdp >= _GDP_CONTRACTION_MAX:
        return GrowthSignal.SLOWDOWN.value
    else:
        return GrowthSignal.CONTRACTION.value


def _classify_pmi(
    pmi_mfg: float | None,
    pmi_svc: float | None,
    factors: dict[str, float],
) -> str:
    """Classify growth by PMI indices."""
    mfg = pmi_mfg
    svc = pmi_svc

    if mfg is None and svc is None:
        return "neutral"

    if mfg is not None:
        factors["pmi_mfg"] = mfg
    if svc is not None:
        factors["pmi_svc"] = svc

    # Use composite PMI
    if mfg is not None and svc is not None:
        composite_pmi = (mfg + svc) / 2.0
        factors["composite_pmi"] = composite_pmi
    elif mfg is not None:
        composite_pmi = mfg
    else:
        composite_pmi = svc

    if composite_pmi >= _PMI_EXPANSION_MIN:
        return GrowthSignal.EXPANSION.value
    elif composite_pmi <= _PMI_CONTRACTION_MAX:
        return GrowthSignal.CONTRACTION.value
    else:
        return GrowthSignal.SLOWDOWN.value


def _classify_momentum(features: FeatureVector, factors: dict[str, float]) -> str:
    """Classify growth momentum."""
    momentum = features.growth_momentum
    if momentum is None:
        return "neutral"

    factors["growth_momentum"] = momentum

    if momentum >= _MOMENTUM_EXPANSION:
        return GrowthSignal.RECOVERY.value
    elif momentum <= _MOMENTUM_SLOWDOWN:
        return GrowthSignal.CONTRACTION.value
    else:
        return GrowthSignal.SLOWDOWN.value


def _combine_growth_signals(gdp: str, pmi: str, momentum: str) -> str:
    """
    Combine growth signals deterministically.

    Priority: CONTRACTION > RECOVERY > EXPANSION > SLOWDOWN
    """
    # Strong signals override
    if gdp == GrowthSignal.CONTRACTION.value or pmi == GrowthSignal.CONTRACTION.value:
        return GrowthSignal.CONTRACTION.value
    if gdp == GrowthSignal.RECOVERY.value or momentum == GrowthSignal.RECOVERY.value:
        return GrowthSignal.RECOVERY.value

    # Agreement check
    non_neutral = [s for s in [gdp, pmi, momentum] if s != "neutral"]
    if len(non_neutral) >= 2:
        # Return the most common signal
        return max(set(non_neutral), key=non_neutral.count)

    # Default to GDP
    if gdp != "neutral":
        return gdp
    if pmi != "neutral":
        return pmi

    return GrowthSignal.SLOWDOWN.value


def _compute_growth_confidence(
    gdp: str,
    pmi: str,
    momentum: str,
    features: FeatureVector,
) -> float:
    """Compute detection confidence."""
    # Base confidence from agreement
    signals = [gdp, pmi, momentum]
    non_neutral = [s for s in signals if s != "neutral"]
    agreement_count = len(non_neutral)
    base_confidence = min(0.4 + (agreement_count * 0.15), 0.95)

    # Boost from z-score
    z_boost = 0.0
    z_score = features.growth_z_score
    if z_score is not None:
        abs_z = abs(z_score)
        if abs_z >= 2.0:
            z_boost = 0.1
        elif abs_z >= 1.5:
            z_boost = 0.05

    confidence = min(base_confidence + z_boost, 1.0)
    return round(confidence, 2)


def _build_evidence(
    signal: str,
    confidence: float,
    factors: dict[str, float],
    details: str = "",
) -> DetectionEvidence:
    """Build DetectionEvidence from growth detection."""
    return DetectionEvidence(
        detector_name="growth_detector",
        signal=signal,
        confidence=confidence,
        contributing_factors=factors,
        algorithm_version=ALGORITHM_VERSION,
        details=details or f"Signal: {signal}",
    )
