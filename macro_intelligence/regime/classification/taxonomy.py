"""
ResearchOS Macro Intelligence Layer - Regime Classification Taxonomy

Defines the macro regime taxonomy used by the classification engine.
All regime labels are permanent constants.
"""

from __future__ import annotations

from enum import Enum


class MacroRegime(Enum):
    """
    Primary macro regime classification.
    
    Derived from Growth x Inflation combinations.
    """
    GOLDILOCKS = "goldilocks"
    INFLATIONARY_GROWTH = "inflationary_growth"
    STAGFLATION = "stagflation"
    DISINFLATION = "disinflation"
    DEFLATIONARY_SLOWDOWN = "deflationary_slowdown"
    RECESSION = "recession"


class LiquidityRegime(Enum):
    """
    Liquidity regime classification.
    """
    LIQUIDITY_EXPANSION = "liquidity_expansion"
    LIQUIDITY_NEUTRAL = "liquidity_neutral"
    LIQUIDITY_CONTRACTION = "liquidity_contraction"


class RiskRegime(Enum):
    """
    Risk regime classification.
    """
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    CRISIS = "crisis"


class MonetaryRegime(Enum):
    """
    Monetary policy regime classification.
    """
    FED_HAWKISH = "fed_hawkish"
    FED_NEUTRAL = "fed_neutral"
    FED_DOVISH = "fed_dovish"


# =============================================================================
# Classification priority ordering (for tie-breaking)
# =============================================================================

MACRO_REGIME_PRIORITY = [
    MacroRegime.RECESSION,
    MacroRegime.DEFLATIONARY_SLOWDOWN,
    MacroRegime.STAGFLATION,
    MacroRegime.DISINFLATION,
    MacroRegime.INFLATIONARY_GROWTH,
    MacroRegime.GOLDILOCKS,
]

LIQUIDITY_REGIME_PRIORITY = [
    LiquidityRegime.LIQUIDITY_CONTRACTION,
    LiquidityRegime.LIQUIDITY_NEUTRAL,
    LiquidityRegime.LIQUIDITY_EXPANSION,
]

RISK_REGIME_PRIORITY = [
    RiskRegime.CRISIS,
    RiskRegime.RISK_OFF,
    RiskRegime.RISK_ON,
]

MONETARY_REGIME_PRIORITY = [
    MonetaryRegime.FED_HAWKISH,
    MonetaryRegime.FED_NEUTRAL,
    MonetaryRegime.FED_DOVISH,
]
