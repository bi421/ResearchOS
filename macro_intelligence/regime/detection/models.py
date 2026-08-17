"""
ResearchOS Macro Intelligence Layer - Regime Detection Models

Defines the data structures used by all regime detectors.
These models convert FeatureVectors and Statistical outputs into
deterministic RegimeEvidence and RegimeAssessment objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# Regime Classification Enums (Phase 2)
# =============================================================================


class InflationSignal(Enum):
    """Inflation regime signal output."""

    LOW = "low"
    STABLE = "stable"
    RISING = "rising"
    HIGH = "high"
    FALLING = "falling"
    DEFLATIONARY = "deflationary"


class GrowthSignal(Enum):
    """Growth regime signal output."""

    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    CONTRACTION = "contraction"
    RECOVERY = "recovery"


class MonetarySignal(Enum):
    """Monetary regime signal output."""

    HAWKISH = "hawkish"
    NEUTRAL = "neutral"
    DOVISH = "dovish"


class LiquiditySignal(Enum):
    """Liquidity regime signal output."""

    EXPANDING = "expanding"
    NEUTRAL = "neutral"
    CONTRACTING = "contracting"


class EmploymentSignal(Enum):
    """Employment regime signal output."""

    STRONG = "strong"
    NORMAL = "normal"
    WEAKENING = "weakening"
    STRESSED = "stressed"


class RiskSignal(Enum):
    """Risk regime signal output."""

    RISK_ON = "risk_on"
    NORMAL = "normal"
    RISK_OFF = "risk_off"
    CRISIS = "crisis"


# =============================================================================
# Feature Vectors
# =============================================================================


@dataclass(frozen=True)
class FeatureVector:
    """
    Aggregated feature vector from validated evidence objects.

    Contains all computed features needed for regime detection.
    Immutable: Yes (frozen=True)
    """

    # Inflation features
    cpi_yoy: float | None = None
    cpi_core_yoy: float | None = None
    pce_yoy: float | None = None
    pce_core_yoy: float | None = None
    ppi_yoy: float | None = None
    ppi_core_yoy: float | None = None
    inflation_trend: str | None = None  # "UPWARD", "DOWNWARD", "NEUTRAL"
    inflation_momentum: float | None = None  # % change in trend
    inflation_z_score: float | None = None  # distance from mean in std units
    inflation_percentile: float | None = None  # percentile vs historical

    # Growth features
    gdp_yoy: float | None = None
    gdp_mom: float | None = None
    pmi_mfg: float | None = None
    pmi_svc: float | None = None
    growth_trend: str | None = None
    growth_momentum: float | None = None
    growth_z_score: float | None = None
    growth_percentile: float | None = None

    # Monetary features
    fed_rate: float | None = None
    fed_policy_direction: str | None = None  # "TIGHTENING", "EASING", "HOLD"
    yield_curve_2_10: float | None = None  # 2Y - 10Y spread
    yield_curve_5_30: float | None = None  # 5Y - 30Y spread
    real_yield_10y: float | None = None
    monetary_tightness: float | None = None  # composite tightness index
    monetary_z_score: float | None = None

    # Liquidity features
    ted_spread: float | None = None  # T-bill - Eurodollar spread
    high_yield_spread: float | None = None  # HYS - treasury spread
    investment_grade_spread: float | None = None
    dxy: float | None = None  # Dollar Index
    liquidity_index: float | None = None  # composite liquidity metric
    liquidity_z_score: float | None = None

    # Employment features
    nfp_change: float | None = None  # thousands
    unemployment_rate: float | None = None
    jolts_total: float | None = None
    jolts_hirings: float | None = None
    jolts_separations: float | None = None
    labor_market_z_score: float | None = None
    labor_market_percentile: float | None = None

    # Risk features
    vix: float | None = None
    move_index: float | None = None
    market_volatility_20d: float | None = None
    credit_spread_10y: float | None = None
    risk_premia: float | None = None
    risk_z_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cpi_yoy": self.cpi_yoy,
            "cpi_core_yoy": self.cpi_core_yoy,
            "pce_yoy": self.pce_yoy,
            "pce_core_yoy": self.pce_core_yoy,
            "ppi_yoy": self.ppi_yoy,
            "ppi_core_yoy": self.ppi_core_yoy,
            "inflation_trend": self.inflation_trend,
            "inflation_momentum": self.inflation_momentum,
            "inflation_z_score": self.inflation_z_score,
            "inflation_percentile": self.inflation_percentile,
            "gdp_yoy": self.gdp_yoy,
            "gdp_mom": self.gdp_mom,
            "pmi_mfg": self.pmi_mfg,
            "pmi_svc": self.pmi_svc,
            "growth_trend": self.growth_trend,
            "growth_momentum": self.growth_momentum,
            "growth_z_score": self.growth_z_score,
            "growth_percentile": self.growth_percentile,
            "fed_rate": self.fed_rate,
            "fed_policy_direction": self.fed_policy_direction,
            "yield_curve_2_10": self.yield_curve_2_10,
            "yield_curve_5_30": self.yield_curve_5_30,
            "real_yield_10y": self.real_yield_10y,
            "monetary_tightness": self.monetary_tightness,
            "monetary_z_score": self.monetary_z_score,
            "ted_spread": self.ted_spread,
            "high_yield_spread": self.high_yield_spread,
            "investment_grade_spread": self.investment_grade_spread,
            "dxy": self.dxy,
            "liquidity_index": self.liquidity_index,
            "liquidity_z_score": self.liquidity_z_score,
            "nfp_change": self.nfp_change,
            "unemployment_rate": self.unemployment_rate,
            "jolts_total": self.jolts_total,
            "jolts_hirings": self.jolts_hirings,
            "jolts_separations": self.jolts_separations,
            "labor_market_z_score": self.labor_market_z_score,
            "labor_market_percentile": self.labor_market_percentile,
            "vix": self.vix,
            "move_index": self.move_index,
            "market_volatility_20d": self.market_volatility_20d,
            "credit_spread_10y": self.credit_spread_10y,
            "risk_premia": self.risk_premia,
            "risk_z_score": self.risk_z_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureVector:
        """Deserialize from dictionary."""
        return cls(
            cpi_yoy=data.get("cpi_yoy"),
            cpi_core_yoy=data.get("cpi_core_yoy"),
            pce_yoy=data.get("pce_yoy"),
            pce_core_yoy=data.get("pce_core_yoy"),
            ppi_yoy=data.get("ppi_yoy"),
            ppi_core_yoy=data.get("ppi_core_yoy"),
            inflation_trend=data.get("inflation_trend"),
            inflation_momentum=data.get("inflation_momentum"),
            inflation_z_score=data.get("inflation_z_score"),
            inflation_percentile=data.get("inflation_percentile"),
            gdp_yoy=data.get("gdp_yoy"),
            gdp_mom=data.get("gdp_mom"),
            pmi_mfg=data.get("pmi_mfg"),
            pmi_svc=data.get("pmi_svc"),
            growth_trend=data.get("growth_trend"),
            growth_momentum=data.get("growth_momentum"),
            growth_z_score=data.get("growth_z_score"),
            growth_percentile=data.get("growth_percentile"),
            fed_rate=data.get("fed_rate"),
            fed_policy_direction=data.get("fed_policy_direction"),
            yield_curve_2_10=data.get("yield_curve_2_10"),
            yield_curve_5_30=data.get("yield_curve_5_30"),
            real_yield_10y=data.get("real_yield_10y"),
            monetary_tightness=data.get("monetary_tightness"),
            monetary_z_score=data.get("monetary_z_score"),
            ted_spread=data.get("ted_spread"),
            high_yield_spread=data.get("high_yield_spread"),
            investment_grade_spread=data.get("investment_grade_spread"),
            dxy=data.get("dxy"),
            liquidity_index=data.get("liquidity_index"),
            liquidity_z_score=data.get("liquidity_z_score"),
            nfp_change=data.get("nfp_change"),
            unemployment_rate=data.get("unemployment_rate"),
            jolts_total=data.get("jolts_total"),
            jolts_hirings=data.get("jolts_hirings"),
            jolts_separations=data.get("jolts_separations"),
            labor_market_z_score=data.get("labor_market_z_score"),
            labor_market_percentile=data.get("labor_market_percentile"),
            vix=data.get("vix"),
            move_index=data.get("move_index"),
            market_volatility_20d=data.get("market_volatility_20d"),
            credit_spread_10y=data.get("credit_spread_10y"),
            risk_premia=data.get("risk_premia"),
            risk_z_score=data.get("risk_z_score"),
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> FeatureVector:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the feature vector.

        MIL-DET-001: Hash depends ONLY on semantic data.
        """
        import hashlib
        import json

        hash_data = {k: v for k, v in self.to_dict().items() if v is not None}
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =============================================================================
# Detection Evidence
# =============================================================================


@dataclass(frozen=True)
class DetectionEvidence:
    """
    Evidence object produced by a single detector.

    Contains the raw signal, confidence, and all contributing factors
    needed for downstream classification.
    """

    # Identity
    detector_name: str
    signal: str  # The detected regime signal

    # Evidence
    confidence: float  # 0.0 to 1.0
    algorithm_version: str
    contributing_factors: dict[str, float] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)

    # Metadata
    feature_hash: str | None = None
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector_name": self.detector_name,
            "signal": self.signal,
            "confidence": self.confidence,
            "contributing_factors": self.contributing_factors,
            "evidence_refs": sorted(self.evidence_refs),
            "algorithm_version": self.algorithm_version,
            "feature_hash": self.feature_hash,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DetectionEvidence:
        return cls(
            detector_name=data["detector_name"],
            signal=data["signal"],
            confidence=data["confidence"],
            contributing_factors=data.get("contributing_factors", {}),
            evidence_refs=data.get("evidence_refs", []),
            algorithm_version=data["algorithm_version"],
            feature_hash=data.get("feature_hash"),
            details=data.get("details", ""),
        )

    def compute_hash(self) -> str:
        """Deterministic hash for detection evidence."""
        import hashlib
        import json

        hash_data = {
            "detector_name": self.detector_name,
            "signal": self.signal,
            "confidence": self.confidence,
            "contributing_factors": dict(sorted(self.contributing_factors.items())),
            "evidence_refs": sorted(self.evidence_refs),
            "algorithm_version": self.algorithm_version,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =============================================================================
# Regime Assessment
# =============================================================================


@dataclass(frozen=True)
class RegimeAssessment:
    """
    Aggregated regime assessment from all detectors.

    Contains the combined signals, overall confidence, and
    all contributing detection evidence.
    """

    # Timestamp
    assessment_time: datetime
    algorithm_version: str

    # Per-detector signals
    inflation_signal: DetectionEvidence
    growth_signal: DetectionEvidence
    monetary_signal: DetectionEvidence
    liquidity_signal: DetectionEvidence
    employment_signal: DetectionEvidence
    risk_signal: DetectionEvidence

    # Aggregated
    overall_confidence: float
    dominant_regime: str | None = None
    regime_description: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_time": self.assessment_time.isoformat(),
            "algorithm_version": self.algorithm_version,
            "inflation": self.inflation_signal.to_dict(),
            "growth": self.growth_signal.to_dict(),
            "monetary": self.monetary_signal.to_dict(),
            "liquidity": self.liquidity_signal.to_dict(),
            "employment": self.employment_signal.to_dict(),
            "risk": self.risk_signal.to_dict(),
            "overall_confidence": self.overall_confidence,
            "dominant_regime": self.dominant_regime,
            "regime_description": self.regime_description,
            "evidence_refs": sorted(self.evidence_refs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeAssessment:
        return cls(
            assessment_time=datetime.fromisoformat(data["assessment_time"]),
            algorithm_version=data["algorithm_version"],
            inflation_signal=DetectionEvidence.from_dict(data["inflation"]),
            growth_signal=DetectionEvidence.from_dict(data["growth"]),
            monetary_signal=DetectionEvidence.from_dict(data["monetary"]),
            liquidity_signal=DetectionEvidence.from_dict(data["liquidity"]),
            employment_signal=DetectionEvidence.from_dict(data["employment"]),
            risk_signal=DetectionEvidence.from_dict(data["risk"]),
            overall_confidence=data["overall_confidence"],
            dominant_regime=data.get("dominant_regime"),
            regime_description=data.get("regime_description", ""),
            evidence_refs=data.get("evidence_refs", []),
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RegimeAssessment:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Deterministic hash for regime assessment."""
        import hashlib
        import json

        hash_data = {
            "assessment_time": self.assessment_time.isoformat(),
            "algorithm_version": self.algorithm_version,
            "inflation": self.inflation_signal.to_dict(),
            "growth": self.growth_signal.to_dict(),
            "monetary": self.monetary_signal.to_dict(),
            "liquidity": self.liquidity_signal.to_dict(),
            "employment": self.employment_signal.to_dict(),
            "risk": self.risk_signal.to_dict(),
            "overall_confidence": self.overall_confidence,
            "dominant_regime": self.dominant_regime,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
