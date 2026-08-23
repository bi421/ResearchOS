"""
ResearchOS Macro Intelligence Layer - Monetary Detector

Deterministic monetary regime detection using Fed policy,
yield curve, and real yields.

Algorithm version: mon-det/v2.0.0
"""

from __future__ import annotations

from macro_intelligence.regime.detection.models import (
    DetectionEvidence,
    FeatureVector,
    MonetarySignal,
)

ALGORITHM_VERSION = "mon-det/v2.0.0"


# =============================================================================
# Thresholds (deterministic, permanent)
# =============================================================================

# Yield curve inversion threshold
_YIELD_CURVE_INVERTED = -25.0  # basis points (2Y - 10Y below -25bp = inverted)

# Real yield thresholds
_REAL_YIELD_HAWKISH = 2.0  # Above this: hawkish
_REAL_YIELD_DOVISH = -0.5  # Below this: dovish

# Fed rate thresholds
_FED_RATE_RESTRICTIVE = 3.5  # Above this: considered restrictive
_FED_RATE_EASY = 0.5  # Below this: considered easy

# Monetary tightness index thresholds
_TIGHTNESS_HAWKISH = 0.5  # Above this: hawkish
_TIGHTNESS_DOVISH = -0.5  # Below this: dovish


def detect_monetary(features: FeatureVector) -> DetectionEvidence:
    """
    Detect monetary regime from feature vector.

    Uses: Fed rate, FOMC direction, yield curve, real yields,
          monetary tightness index.

    Args:
        features: FeatureVector with monetary-related data.

    Returns:
        DetectionEvidence with monetary regime signal.
    """
    fed_rate = features.fed_rate
    policy_direction = features.fed_policy_direction
    yield_curve = features.yield_curve_2_10
    real_yield = features.real_yield_10y
    tightness = features.monetary_tightness

    if fed_rate is None and policy_direction is None:
        return _build_evidence(
            signal=MonetarySignal.NEUTRAL.value,
            confidence=0.0,
            factors={},
        )

    factors: dict[str, float] = {
        "fed_rate": fed_rate or 0.0,
        "yield_curve_2_10_bps": (yield_curve or 0.0) * 100,
        "real_yield_10y": real_yield or 0.0,
    }

    if tightness is not None:
        factors["monetary_tightness"] = tightness

    # Factor 1: Fed policy direction
    policy_score = _classify_policy_direction(policy_direction, fed_rate, factors)

    # Factor 2: Yield curve
    curve_score = _classify_yield_curve(yield_curve, factors)

    # Factor 3: Real yields
    real_score = _classify_real_yields(real_yield, factors)

    # Factor 4: Tightness index
    tightness_score = _classify_tightness(tightness, factors)

    # Combine signals
    signal = _combine_monetary_signals(policy_score, curve_score, real_score, tightness_score)
    confidence = _compute_monetary_confidence(policy_score, curve_score, real_score, tightness_score)

    return _build_evidence(signal, confidence, factors)


def _classify_policy_direction(direction: str | None, fed_rate: float | None, factors: dict[str, float]) -> str:
    """Classify monetary policy direction."""
    if direction is None:
        return "neutral"

    factors["policy_direction"] = direction

    if direction == "TIGHTENING":
        return MonetarySignal.HAWKISH.value
    elif direction == "EASING":
        return MonetarySignal.DOVISH.value
    else:
        return MonetarySignal.NEUTRAL.value


def _classify_yield_curve(yield_curve: float | None, factors: dict[str, float]) -> str:
    """Classify monetary stance by yield curve."""
    if yield_curve is None:
        return "neutral"

    # Convert to basis points for threshold comparison
    curve_bps = yield_curve * 100
    factors["yield_curve_bps"] = curve_bps

    if curve_bps < _YIELD_CURVE_INVERTED:
        # Inverted curve typically precedes tightening cycle end
        return MonetarySignal.HAWKISH.value
    elif curve_bps > 100:
        # Steep curve suggests dovish/recovery phase
        return MonetarySignal.DOVISH.value
    else:
        return MonetarySignal.NEUTRAL.value


def _classify_real_yields(real_yield: float | None, factors: dict[str, float]) -> str:
    """Classify monetary stance by real yields."""
    if real_yield is None:
        return "neutral"

    factors["real_yield"] = real_yield

    if real_yield >= _REAL_YIELD_HAWKISH:
        return MonetarySignal.HAWKISH.value
    elif real_yield <= _REAL_YIELD_DOVISH:
        return MonetarySignal.DOVISH.value
    else:
        return MonetarySignal.NEUTRAL.value


def _classify_tightness(tightness: float | None, factors: dict[str, float]) -> str:
    """Classify monetary stance by tightness index."""
    if tightness is None:
        return "neutral"

    factors["tightness_index"] = tightness

    if tightness >= _TIGHTNESS_HAWKISH:
        return MonetarySignal.HAWKISH.value
    elif tightness <= _TIGHTNESS_DOVISH:
        return MonetarySignal.DOVISH.value
    else:
        return MonetarySignal.NEUTRAL.value


def _combine_monetary_signals(policy: str, curve: str, real: str, tightness: str) -> str:
    """
    Combine monetary signals deterministically.

    Priority: HAWKISH/DOVISH based on majority vote.
    """
    signals = [policy, curve, real, tightness]
    non_neutral = [s for s in signals if s != "neutral"]

    if not non_neutral:
        return MonetarySignal.NEUTRAL.value

    # Count votes
    hawkish_count = sum(1 for s in non_neutral if s == MonetarySignal.HAWKISH.value)
    dovish_count = sum(1 for s in non_neutral if s == MonetarySignal.DOVISH.value)

    if hawkish_count > dovish_count:
        return MonetarySignal.HAWKISH.value
    elif dovish_count > hawkish_count:
        return MonetarySignal.DOVISH.value
    else:
        # Tie: use Fed rate level as tiebreaker
        return MonetarySignal.NEUTRAL.value


def _compute_monetary_confidence(
    policy: str,
    curve: str,
    real: str,
    tightness: str,
) -> float:
    """Compute detection confidence."""
    signals = [policy, curve, real, tightness]
    non_neutral = [s for s in signals if s != "neutral"]
    agreement_count = len(non_neutral)
    base_confidence = min(0.35 + (agreement_count * 0.15), 0.95)

    return round(base_confidence, 2)


def _build_evidence(
    signal: str,
    confidence: float,
    factors: dict[str, float],
    details: str = "",
) -> DetectionEvidence:
    """Build DetectionEvidence from monetary detection."""
    return DetectionEvidence(
        detector_name="monetary_detector",
        signal=signal,
        confidence=confidence,
        contributing_factors=factors,
        algorithm_version=ALGORITHM_VERSION,
        details=details or f"Signal: {signal}",
    )
