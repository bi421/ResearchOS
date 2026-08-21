"""
ResearchOS Macro Intelligence Layer - Risk Detector

Deterministic risk regime detection using VIX, MOVE index,
volatility features, and market stress indicators.

Algorithm version: risk-det/v2.0.0
"""

from __future__ import annotations

from researchos.macro.regime.detection.models import (
    DetectionEvidence,
    FeatureVector,
    RiskSignal,
)

ALGORITHM_VERSION = "risk-det/v2.0.0"


# =============================================================================
# Thresholds (deterministic, permanent)
# =============================================================================

# VIX thresholds
_VIX_CRISIS_MIN = 40.0  # Above this: CRISIS
_VIX_RISK_OFF_MIN = 30.0  # Above this: RISK_OFF
_VIX_RISK_ON_MAX = 15.0  # Below this: RISK_ON

# MOVE index thresholds
_MOVE_CRISIS_MIN = 200.0  # Above this: CRISIS
_MOVE_RISK_OFF_MIN = 120.0  # Above this: RISK_OFF
_MOVE_RISK_ON_MAX = 80.0  # Below this: RISK_ON

# 20-day realized volatility thresholds
_VOL_CRISIS_MIN = 0.30  # 30% annualized
_VOL_RISK_OFF_MIN = 0.20  # 20% annualized
_VOL_RISK_ON_MAX = 0.12  # 12% annualized

# Risk z-score thresholds
_RISK_Z_CRISIS = 2.5  # Above this: CRISIS
_RISK_Z_RISK_OFF = 1.5  # Above this: RISK_OFF
_RISK_Z_RISK_ON = -1.5  # Below this: RISK_ON


def detect_risk(features: FeatureVector) -> DetectionEvidence:
    """
    Detect risk regime from feature vector.

    Uses: VIX, MOVE index, realized volatility, credit spreads,
          risk z-score.

    Args:
        features: FeatureVector with risk-related data.

    Returns:
        DetectionEvidence with risk regime signal.
    """
    vix = features.vix
    move = features.move_index
    vol_20d = features.market_volatility_20d
    risk_z = features.risk_z_score

    if vix is None and move is None:
        return _build_evidence(
            signal=RiskSignal.NORMAL.value,
            confidence=0.0,
            factors={},
        )

    factors: dict[str, float] = {}

    if vix is not None:
        factors["vix"] = vix
    if move is not None:
        factors["move_index"] = move
    if vol_20d is not None:
        factors["volatility_20d"] = vol_20d
    if risk_z is not None:
        factors["risk_z_score"] = risk_z

    # Factor 1: VIX classification
    vix_score = _classify_vix(vix, factors)

    # Factor 2: MOVE index classification
    move_score = _classify_move(move, factors)

    # Factor 3: Realized volatility
    vol_score = _classify_volatility(vol_20d, factors)

    # Factor 4: Risk z-score
    z_score = features.risk_z_score
    if z_score is not None:
        factors["risk_z_score"] = z_score
        z_score_result = _classify_risk_z(z_score)
    else:
        z_score_result = "neutral"

    # Combine signals
    signal = _combine_risk_signals(vix_score, move_score, vol_score, z_score_result)
    confidence = _compute_risk_confidence(vix_score, move_score, vol_score, z_score_result)

    return _build_evidence(signal, confidence, factors)


def _classify_vix(vix: float | None, factors: dict[str, float]) -> str:
    """Classify risk by VIX."""
    if vix is None:
        return "neutral"

    factors["vix"] = vix

    if vix >= _VIX_CRISIS_MIN:
        return RiskSignal.CRISIS.value
    elif vix >= _VIX_RISK_OFF_MIN:
        return RiskSignal.RISK_OFF.value
    elif vix <= _VIX_RISK_ON_MAX:
        return RiskSignal.RISK_ON.value
    else:
        return RiskSignal.NORMAL.value


def _classify_move(move: float | None, factors: dict[str, float]) -> str:
    """Classify risk by MOVE index."""
    if move is None:
        return "neutral"

    factors["move_index"] = move

    if move >= _MOVE_CRISIS_MIN:
        return RiskSignal.CRISIS.value
    elif move >= _MOVE_RISK_OFF_MIN:
        return RiskSignal.RISK_OFF.value
    elif move <= _MOVE_RISK_ON_MAX:
        return RiskSignal.RISK_ON.value
    else:
        return RiskSignal.NORMAL.value


def _classify_volatility(vol: float | None, factors: dict[str, float]) -> str:
    """Classify risk by 20-day realized volatility."""
    if vol is None:
        return "neutral"

    factors["volatility_20d"] = vol

    if vol >= _VOL_CRISIS_MIN:
        return RiskSignal.CRISIS.value
    elif vol >= _VOL_RISK_OFF_MIN:
        return RiskSignal.RISK_OFF.value
    elif vol <= _VOL_RISK_ON_MAX:
        return RiskSignal.RISK_ON.value
    else:
        return RiskSignal.NORMAL.value


def _classify_risk_z(z_score: float) -> str:
    """Classify risk by z-score."""
    if z_score >= _RISK_Z_CRISIS:
        return RiskSignal.CRISIS.value
    elif z_score >= _RISK_Z_RISK_OFF:
        return RiskSignal.RISK_OFF.value
    elif z_score <= _RISK_Z_RISK_ON:
        return RiskSignal.RISK_ON.value
    else:
        return RiskSignal.NORMAL.value


def _combine_risk_signals(vix: str, move: str, vol: str, z_score: str) -> str:
    """
    Combine risk signals deterministically.

    Priority: CRISIS > RISK_OFF > RISK_ON > NORMAL
    """
    signals = [vix, move, vol, z_score]
    non_neutral = [s for s in signals if s != "neutral"]

    if not non_neutral:
        return RiskSignal.NORMAL.value

    # Check for crisis first (highest priority)
    if any(s == RiskSignal.CRISIS.value for s in non_neutral):
        return RiskSignal.CRISIS.value
    if any(s == RiskSignal.RISK_OFF.value for s in non_neutral):
        return RiskSignal.RISK_OFF.value
    if any(s == RiskSignal.RISK_ON.value for s in non_neutral):
        return RiskSignal.RISK_ON.value

    return RiskSignal.NORMAL.value


def _compute_risk_confidence(
    vix: str,
    move: str,
    vol: str,
    z_score: str,
) -> float:
    """Compute detection confidence."""
    signals = [vix, move, vol, z_score]
    non_neutral = [s for s in signals if s != "neutral"]
    agreement_count = len(non_neutral)
    base_confidence = min(0.35 + (agreement_count * 0.15), 0.95)

    # Extra confidence when all signals agree on crisis/risk-off
    if all(s == RiskSignal.CRISIS.value for s in non_neutral):
        base_confidence = min(base_confidence + 0.1, 1.0)
    elif all(s == RiskSignal.RISK_OFF.value for s in non_neutral):
        base_confidence = min(base_confidence + 0.05, 1.0)

    return round(base_confidence, 2)


def _build_evidence(
    signal: str,
    confidence: float,
    factors: dict[str, float],
    details: str = "",
) -> DetectionEvidence:
    """Build DetectionEvidence from risk detection."""
    return DetectionEvidence(
        detector_name="risk_detector",
        signal=signal,
        confidence=confidence,
        contributing_factors=factors,
        algorithm_version=ALGORITHM_VERSION,
        details=details or f"Signal: {signal}",
    )
