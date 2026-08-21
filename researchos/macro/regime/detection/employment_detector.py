"""
ResearchOS Macro Intelligence Layer - Employment Detector

Deterministic employment regime detection using NFP,
unemployment rate, and JOLTS data.

Algorithm version: emp-det/v2.0.0
"""

from __future__ import annotations

from researchos.macro.regime.detection.models import (
    DetectionEvidence,
    EmploymentSignal,
    FeatureVector,
)

ALGORITHM_VERSION = "emp-det/v2.0.0"


# =============================================================================
# Thresholds (deterministic, permanent)
# =============================================================================

# NFP thresholds (thousands)
_NFP_STRONG_MIN = 150  # Above this: STRONG
_NFP_WEAK_MAX = 75  # Below this: WEAKENING
_NFP_STRESSED_MAX = 25  # Below this: STRESSED

# Unemployment rate thresholds
_UNEMPLOYMENT_STRESSED_MIN = 6.5  # Above this: STRESSED
_UNEMPLOYMENT_WEAKENING_MIN = 5.0  # Above this: WEAKENING
_UNEMPLOYMENT_STRONG_MAX = 4.0  # Below this: STRONG

# JOLTS thresholds (thousands)
_JOLTS_LOW_MIN = 7000  # Below this: WEAKENING
_JOLTS_HIGH_MAX = 10000  # Above this: STRONG


def detect_employment(features: FeatureVector) -> DetectionEvidence:
    """
    Detect employment regime from feature vector.

    Uses: NFP change, unemployment rate, JOLTS total, hirings,
          separations.

    Args:
        features: FeatureVector with employment-related data.

    Returns:
        DetectionEvidence with employment regime signal.
    """
    nfp = features.nfp_change
    unemployment = features.unemployment_rate
    jolts = features.jolts_total

    if nfp is None and unemployment is None and jolts is None:
        return _build_evidence(
            signal=EmploymentSignal.NORMAL.value,
            confidence=0.0,
            factors={},
        )

    factors: dict[str, float] = {}

    if nfp is not None:
        factors["nfp_change"] = nfp
    if unemployment is not None:
        factors["unemployment_rate"] = unemployment
    if jolts is not None:
        factors["jolts_total"] = jolts

    # Factor 1: NFP classification
    nfp_score = _classify_nfp(nfp, factors)

    # Factor 2: Unemployment rate
    unemployment_score = _classify_unemployment(unemployment, factors)

    # Factor 3: JOLTS
    jolts_score = _classify_jolts(jolts, factors)

    # Factor 4: Hirings/Separations ratio (if available)
    hirings = features.jolts_hirings
    separations = features.jolts_separations
    if hirings is not None and separations is not None and separations > 0:
        ratio = hirings / separations
        factors["hirings_separations_ratio"] = ratio
        ratio_score = _classify_hire_separate_ratio(ratio)
    else:
        ratio_score = "neutral"

    # Combine signals
    signal = _combine_employment_signals(nfp_score, unemployment_score, jolts_score, ratio_score)
    confidence = _compute_employment_confidence(nfp_score, unemployment_score, jolts_score, ratio_score)

    return _build_evidence(signal, confidence, factors)


def _classify_nfp(nfp: float | None, factors: dict[str, float]) -> str:
    """Classify employment by NFP."""
    if nfp is None:
        return "neutral"

    factors["nfp_change"] = nfp

    if nfp >= _NFP_STRONG_MIN:
        return EmploymentSignal.STRONG.value
    elif nfp <= _NFP_STRESSED_MAX:
        return EmploymentSignal.STRESSED.value
    elif nfp <= _NFP_WEAK_MAX:
        return EmploymentSignal.WEAKENING.value
    else:
        return EmploymentSignal.NORMAL.value


def _classify_unemployment(unemployment: float | None, factors: dict[str, float]) -> str:
    """Classify employment by unemployment rate."""
    if unemployment is None:
        return "neutral"

    factors["unemployment_rate"] = unemployment

    if unemployment <= _UNEMPLOYMENT_STRONG_MAX:
        return EmploymentSignal.STRONG.value
    elif unemployment >= _UNEMPLOYMENT_STRESSED_MIN:
        return EmploymentSignal.STRESSED.value
    elif unemployment >= _UNEMPLOYMENT_WEAKENING_MIN:
        return EmploymentSignal.WEAKENING.value
    else:
        return EmploymentSignal.NORMAL.value


def _classify_jolts(jolts: float | None, factors: dict[str, float]) -> str:
    """Classify employment by JOLTS."""
    if jolts is None:
        return "neutral"

    factors["jolts_total"] = jolts

    if jolts >= _JOLTS_HIGH_MAX:
        return EmploymentSignal.STRONG.value
    elif jolts <= _JOLTS_LOW_MIN:
        return EmploymentSignal.WEAKENING.value
    else:
        return EmploymentSignal.NORMAL.value


def _classify_hire_separate_ratio(ratio: float) -> str:
    """Classify employment by hirings/separations ratio."""
    if ratio >= 1.1:
        return EmploymentSignal.STRONG.value
    elif ratio <= 0.9:
        return EmploymentSignal.WEAKENING.value
    else:
        return EmploymentSignal.NORMAL.value


def _combine_employment_signals(nfp: str, unemployment: str, jolts: str, ratio: str) -> str:
    """
    Combine employment signals deterministically.

    Priority: STRESSED > STRONG > WEAKENING > NORMAL
    """
    signals = [nfp, unemployment, jolts, ratio]
    non_neutral = [s for s in signals if s != "neutral"]

    if not non_neutral:
        return EmploymentSignal.NORMAL.value

    # Check for extreme signals first
    if any(s == EmploymentSignal.STRESSED.value for s in non_neutral):
        return EmploymentSignal.STRESSED.value
    if any(s == EmploymentSignal.STRONG.value for s in non_neutral):
        return EmploymentSignal.STRONG.value
    if any(s == EmploymentSignal.WEAKENING.value for s in non_neutral):
        return EmploymentSignal.WEAKENING.value

    return EmploymentSignal.NORMAL.value


def _compute_employment_confidence(
    nfp: str,
    unemployment: str,
    jolts: str,
    ratio: str,
) -> float:
    """Compute detection confidence."""
    signals = [nfp, unemployment, jolts, ratio]
    non_neutral = [s for s in signals if s != "neutral"]
    agreement_count = len(non_neutral)
    base_confidence = min(0.35 + (agreement_count * 0.12), 0.95)

    return round(base_confidence, 2)


def _build_evidence(
    signal: str,
    confidence: float,
    factors: dict[str, float],
    details: str = "",
) -> DetectionEvidence:
    """Build DetectionEvidence from employment detection."""
    return DetectionEvidence(
        detector_name="employment_detector",
        signal=signal,
        confidence=confidence,
        contributing_factors=factors,
        algorithm_version=ALGORITHM_VERSION,
        details=details or f"Signal: {signal}",
    )
