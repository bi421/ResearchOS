"""
ResearchOS Macro Intelligence Layer - Liquidity Detector

Deterministic liquidity regime detection using yield spreads,
dollar index, and credit conditions.

Algorithm version: liq-det/v2.0.0
"""

from __future__ import annotations

from macro_intelligence.regime.detection.models import (
    FeatureVector,
    DetectionEvidence,
    LiquiditySignal,
)

ALGORITHM_VERSION = "liq-det/v2.0.0"


# =============================================================================
# Thresholds (deterministic, permanent)
# =============================================================================

# Spread thresholds (basis points)
_SPREAD_EXPANDING_MAX = 50      # Below this: liquidity expanding
_SPREAD_CONTRACTING_MIN = 150   # Above this: liquidity contracting
_SPREAD_NEUTRAL = 100           # Between these: neutral

# Dollar Index thresholds
_DXY_STRONG = 105.0             # Strong dollar = tighter liquidity
_DXY_WEAK = 95.0                # Weak dollar = looser liquidity

# Liquidity index thresholds
_LIQ_EXPANDING = 0.3            # Above this: expanding
_LIQ_CONTRACTING = -0.3         # Below this: contracting


def detect_liquidity(features: FeatureVector) -> DetectionEvidence:
    """
    Detect liquidity regime from feature vector.
    
    Uses: yield spreads, DXY, Treasury curves, credit conditions,
          liquidity index.
    
    Args:
        features: FeatureVector with liquidity-related data.
        
    Returns:
        DetectionEvidence with liquidity regime signal.
    """
    hy_spread = features.high_yield_spread
    ig_spread = features.investment_grade_spread
    ted_spread = features.ted_spread
    dxy = features.dxy
    liquidity_idx = features.liquidity_index
    
    if hy_spread is None and liquidity_idx is None:
        return _build_evidence(
            signal=LiquiditySignal.NEUTRAL.value,
            confidence=0.0,
            factors={},
        )
    
    factors: dict[str, float] = {}
    
    if hy_spread is not None:
        factors["high_yield_spread_bps"] = hy_spread * 100
    if ig_spread is not None:
        factors["ig_spread_bps"] = ig_spread * 100
    if ted_spread is not None:
        factors["ted_spread_bps"] = ted_spread * 100
    if dxy is not None:
        factors["dxy"] = dxy
    if liquidity_idx is not None:
        factors["liquidity_index"] = liquidity_idx
    
    # Factor 1: Credit spread
    spread_score = _classify_spreads(hy_spread, ig_spread, ted_spread, factors)
    
    # Factor 2: Dollar index
    dxy_score = _classify_dxy(dxy, factors)
    
    # Factor 3: Liquidity index
    liq_score = _classify_liquidity_index(liquidity_idx, factors)
    
    # Combine signals
    signal = _combine_liquidity_signals(spread_score, dxy_score, liq_score)
    confidence = _compute_liquidity_confidence(spread_score, dxy_score, liq_score)
    
    return _build_evidence(signal, confidence, factors)


def _classify_spreads(
    hy_spread: float | None,
    ig_spread: float | None,
    ted_spread: float | None,
    factors: dict[str, float],
) -> str:
    """Classify liquidity by credit spreads."""
    # Use the widest spread as the conservative signal
    spreads = []
    if hy_spread is not None:
        spreads.append(("high_yield", hy_spread))
    if ig_spread is not None:
        spreads.append(("ig", ig_spread))
    if ted_spread is not None:
        spreads.append(("ted", ted_spread))
    
    if not spreads:
        return "neutral"
    
    # Use the largest spread (most conservative)
    worst_spread = max(spreads, key=lambda x: x[1])
    spread_bps = worst_spread[1] * 100
    factors["dominant_spread_bps"] = spread_bps
    
    if spread_bps <= _SPREAD_EXPANDING_MAX:
        return LiquiditySignal.EXPANDING.value
    elif spread_bps >= _SPREAD_CONTRACTING_MIN:
        return LiquiditySignal.CONTRACTING.value
    else:
        return LiquiditySignal.NEUTRAL.value


def _classify_dxy(dxy: float | None, factors: dict[str, float]) -> str:
    """Classify liquidity by dollar index."""
    if dxy is None:
        return "neutral"
    
    factors["dxy"] = dxy
    
    if dxy >= _DXY_STRONG:
        # Strong dollar typically means tighter liquidity conditions
        return LiquiditySignal.CONTRACTING.value
    elif dxy <= _DXY_WEAK:
        # Weak dollar typically means looser liquidity
        return LiquiditySignal.EXPANDING.value
    else:
        return LiquiditySignal.NEUTRAL.value


def _classify_liquidity_index(
    liquidity_idx: float | None, factors: dict[str, float]
) -> str:
    """Classify liquidity by composite index."""
    if liquidity_idx is None:
        return "neutral"
    
    factors["liquidity_index"] = liquidity_idx
    
    if liquidity_idx >= _LIQ_EXPANDING:
        return LiquiditySignal.EXPANDING.value
    elif liquidity_idx <= _LIQ_CONTRACTING:
        return LiquiditySignal.CONTRACTING.value
    else:
        return LiquiditySignal.NEUTRAL.value


def _combine_liquidity_signals(
    spread: str, dxy: str, liq: str
) -> str:
    """
    Combine liquidity signals deterministically.
    
    Priority: CONTRACTING/EXPANDING based on majority vote.
    """
    signals = [spread, dxy, liq]
    non_neutral = [s for s in signals if s != "neutral"]
    
    if not non_neutral:
        return LiquiditySignal.NEUTRAL.value
    
    contracting_count = sum(1 for s in non_neutral if s == LiquiditySignal.CONTRACTING.value)
    expanding_count = sum(1 for s in non_neutral if s == LiquiditySignal.EXPANDING.value)
    
    if contracting_count > expanding_count:
        return LiquiditySignal.CONTRACTING.value
    elif expanding_count > contracting_count:
        return LiquiditySignal.EXPANDING.value
    else:
        return LiquiditySignal.NEUTRAL.value


def _compute_liquidity_confidence(
    spread: str,
    dxy: str,
    liq: str,
) -> float:
    """Compute detection confidence."""
    signals = [spread, dxy, liq]
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
    """Build DetectionEvidence from liquidity detection."""
    return DetectionEvidence(
        detector_name="liquidity_detector",
        signal=signal,
        confidence=confidence,
        contributing_factors=factors,
        algorithm_version=ALGORITHM_VERSION,
        details=details or f"Signal: {signal}",
    )
