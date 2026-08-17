"""Macro Intelligence objects — institutional XAUUSD macro factor analysis.

Based on the TRADER-OS Macro Intelligence Layer specification.

Each object represents a deterministic snapshot of a macro driver
affecting gold prices. All scores are 0-100, all confidences are 0-1,
all conclusions are fully explainable via evidence references.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now

# ---------------------------------------------------------------------------
# 1. US Real Yields
# ---------------------------------------------------------------------------


class RealYieldSnapshot(BaseObject):
    """Snapshot of US real yield conditions and their impact on gold.

    Attributes:
        ten_year_yield: US 10Y Treasury yield (percent)
        five_year_yield: US 5Y Treasury yield (percent)
        inflation_expectations: 5Y breakeven inflation rate (percent)
        tips_yield: 10Y TIPS real yield (percent)
        real_yield_curve: "Normal", "Flat", "Inverted", "Steepening", "Flattening"
        real_yield_trend: "Rising", "Falling", "Stable", "Extreme_Rising", "Extreme_Falling"
        historical_correlation: Historical correlation with gold (-1 to 1)
        score: Real Yield Score (0-100, 100 = most gold-bullish)
        confidence: Confidence in this assessment (0-1)
        evidence_ids: Supporting observation IDs
        expected_gold_impact: "Strongly_Bullish", "Bullish", "Neutral", "Bearish", "Strongly_Bearish"
    """

    def __init__(
        self,
        ten_year_yield: float = 0.0,
        five_year_yield: float = 0.0,
        inflation_expectations: float = 0.0,
        tips_yield: float = 0.0,
        real_yield_curve: str = "Normal",
        real_yield_trend: str = "Stable",
        historical_correlation: float = -0.7,
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        expected_gold_impact: str = "Neutral",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"RealYieldSnapshot|{ts}|{ten_year_yield}|{five_year_yield}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.ten_year_yield = ten_year_yield
        self.five_year_yield = five_year_yield
        self.inflation_expectations = inflation_expectations
        self.tips_yield = tips_yield
        self.real_yield_curve = real_yield_curve
        self.real_yield_trend = real_yield_trend
        self.historical_correlation = historical_correlation
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.expected_gold_impact = expected_gold_impact
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Real yield snapshot analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "ten_year_yield": self.ten_year_yield,
            "five_year_yield": self.five_year_yield,
            "inflation_expectations": self.inflation_expectations,
            "tips_yield": self.tips_yield,
            "real_yield_curve": self.real_yield_curve,
            "real_yield_trend": self.real_yield_trend,
            "historical_correlation": self.historical_correlation,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "expected_gold_impact": self.expected_gold_impact,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "ten_year_yield": self.ten_year_yield,
                "five_year_yield": self.five_year_yield,
                "inflation_expectations": self.inflation_expectations,
                "tips_yield": self.tips_yield,
                "real_yield_curve": self.real_yield_curve,
                "real_yield_trend": self.real_yield_trend,
                "historical_correlation": self.historical_correlation,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
                "expected_gold_impact": self.expected_gold_impact,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "RealYieldSnapshot":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.ten_year_yield = data.get("ten_year_yield", 0.0)
        obj.five_year_yield = data.get("five_year_yield", 0.0)
        obj.inflation_expectations = data.get("inflation_expectations", 0.0)
        obj.tips_yield = data.get("tips_yield", 0.0)
        obj.real_yield_curve = data.get("real_yield_curve", "Normal")
        obj.real_yield_trend = data.get("real_yield_trend", "Stable")
        obj.historical_correlation = data.get("historical_correlation", -0.7)
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.expected_gold_impact = data.get("expected_gold_impact", "Neutral")
        return obj


# ---------------------------------------------------------------------------
# 2. US Dollar (DXY)
# ---------------------------------------------------------------------------


class DollarStrengthSnapshot(BaseObject):
    """Snapshot of US Dollar strength and its implications for gold.

    Attributes:
        dxy: DXY index value
        dxy_trend: "Rising", "Falling", "Ranging", "Breakout_Up", "Breakout_Down"
        dxy_momentum: "Strong_Bullish", "Bullish", "Neutral", "Bearish", "Strong_Bearish"
        relative_strength: DXY relative strength metric (0-100)
        multi_timeframe_trend: "All_Bullish", "Mixed_Bullish", "Mixed", "Mixed_Bearish", "All_Bearish"
        score: Dollar Strength Score (0-100, 100 = most gold-bullish = weakest dollar)
        confidence: Confidence in this assessment (0-1)
    """

    def __init__(
        self,
        dxy: float = 100.0,
        dxy_trend: str = "Ranging",
        dxy_momentum: str = "Neutral",
        relative_strength: float = 50.0,
        multi_timeframe_trend: str = "Mixed",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"DollarStrengthSnapshot|{ts}|{dxy}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.dxy = dxy
        self.dxy_trend = dxy_trend
        self.dxy_momentum = dxy_momentum
        self.relative_strength = relative_strength
        self.multi_timeframe_trend = multi_timeframe_trend
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.lifecycle.transition(
            LifecycleStage.ANALYZED, reason="Dollar strength snapshot analyzed"
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "dxy": self.dxy,
            "dxy_trend": self.dxy_trend,
            "dxy_momentum": self.dxy_momentum,
            "relative_strength": self.relative_strength,
            "multi_timeframe_trend": self.multi_timeframe_trend,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "dxy": self.dxy,
                "dxy_trend": self.dxy_trend,
                "dxy_momentum": self.dxy_momentum,
                "relative_strength": self.relative_strength,
                "multi_timeframe_trend": self.multi_timeframe_trend,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "DollarStrengthSnapshot":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.dxy = data.get("dxy", 100.0)
        obj.dxy_trend = data.get("dxy_trend", "Ranging")
        obj.dxy_momentum = data.get("dxy_momentum", "Neutral")
        obj.relative_strength = data.get("relative_strength", 50.0)
        obj.multi_timeframe_trend = data.get("multi_timeframe_trend", "Mixed")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        return obj


# ---------------------------------------------------------------------------
# 3. Federal Reserve
# ---------------------------------------------------------------------------


class FedPolicyAssessment(BaseObject):
    """Assessment of Federal Reserve policy stance and impact on gold.

    Attributes:
        rate_decision: Latest rate decision text
        rate_change_bps: Rate change in basis points
        dot_plot_median: Median dot plot rate expectation
        balance_sheet_change: Monthly balance sheet change (billions)
        policy_classification: "Hawkish", "Dovish", "Neutral", "Extremely_Hawkish", "Extremely_Dovish"
        hawkishness_score: 0 (extremely dovish) to 100 (extremely hawkish)
        gold_pressure: "Bullish", "Bearish", "Neutral"
        score: Fed Policy Score (0-100, 100 = most gold-bullish = most dovish)
        confidence: Confidence in this assessment (0-1)
    """

    def __init__(
        self,
        rate_decision: str = "",
        rate_change_bps: float = 0.0,
        dot_plot_median: float = 0.0,
        balance_sheet_change: float = 0.0,
        policy_classification: str = "Neutral",
        hawkishness_score: float = 50.0,
        gold_pressure: str = "Neutral",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"FedPolicyAssessment|{ts}|{policy_classification}|{rate_change_bps}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.rate_decision = rate_decision
        self.rate_change_bps = rate_change_bps
        self.dot_plot_median = dot_plot_median
        self.balance_sheet_change = balance_sheet_change
        self.policy_classification = policy_classification
        self.hawkishness_score = hawkishness_score
        self.gold_pressure = gold_pressure
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Fed policy analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "rate_decision": self.rate_decision,
            "rate_change_bps": self.rate_change_bps,
            "dot_plot_median": self.dot_plot_median,
            "balance_sheet_change": self.balance_sheet_change,
            "policy_classification": self.policy_classification,
            "hawkishness_score": self.hawkishness_score,
            "gold_pressure": self.gold_pressure,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "rate_decision": self.rate_decision,
                "rate_change_bps": self.rate_change_bps,
                "dot_plot_median": self.dot_plot_median,
                "balance_sheet_change": self.balance_sheet_change,
                "policy_classification": self.policy_classification,
                "hawkishness_score": self.hawkishness_score,
                "gold_pressure": self.gold_pressure,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "FedPolicyAssessment":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.rate_decision = data.get("rate_decision", "")
        obj.rate_change_bps = data.get("rate_change_bps", 0.0)
        obj.dot_plot_median = data.get("dot_plot_median", 0.0)
        obj.balance_sheet_change = data.get("balance_sheet_change", 0.0)
        obj.policy_classification = data.get("policy_classification", "Neutral")
        obj.hawkishness_score = data.get("hawkishness_score", 50.0)
        obj.gold_pressure = data.get("gold_pressure", "Neutral")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        return obj


# ---------------------------------------------------------------------------
# 4. Inflation
# ---------------------------------------------------------------------------


class InflationAssessment(BaseObject):
    """Assessment of inflation conditions and implications for gold.

    Attributes:
        cpi: Headline CPI YoY (percent)
        core_cpi: Core CPI YoY (percent)
        ppi: PPI YoY (percent)
        pce: PCE YoY (percent)
        inflation_expectations_5y: 5Y breakeven (percent)
        inflation_regime: "Deflation", "Disinflation", "Stable", "Moderate_Inflation", "High_Inflation", "Hyperinflation"
        score: Inflation Score (0-100, 100 = most gold-bullish = highest inflation concern)
        confidence: Confidence (0-1)
        expected_fed_reaction: "Hawkish", "Dovish", "Neutral", "Accommodative", "Restrictive"
    """

    def __init__(
        self,
        cpi: float = 0.0,
        core_cpi: float = 0.0,
        ppi: float = 0.0,
        pce: float = 0.0,
        inflation_expectations_5y: float = 0.0,
        inflation_regime: str = "Stable",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        expected_fed_reaction: str = "Neutral",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"InflationAssessment|{ts}|{cpi}|{core_cpi}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.cpi = cpi
        self.core_cpi = core_cpi
        self.ppi = ppi
        self.pce = pce
        self.inflation_expectations_5y = inflation_expectations_5y
        self.inflation_regime = inflation_regime
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.expected_fed_reaction = expected_fed_reaction
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Inflation analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "cpi": self.cpi,
            "core_cpi": self.core_cpi,
            "ppi": self.ppi,
            "pce": self.pce,
            "inflation_expectations_5y": self.inflation_expectations_5y,
            "inflation_regime": self.inflation_regime,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "expected_fed_reaction": self.expected_fed_reaction,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "cpi": self.cpi,
                "core_cpi": self.core_cpi,
                "ppi": self.ppi,
                "pce": self.pce,
                "inflation_expectations_5y": self.inflation_expectations_5y,
                "inflation_regime": self.inflation_regime,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
                "expected_fed_reaction": self.expected_fed_reaction,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "InflationAssessment":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.cpi = data.get("cpi", 0.0)
        obj.core_cpi = data.get("core_cpi", 0.0)
        obj.ppi = data.get("ppi", 0.0)
        obj.pce = data.get("pce", 0.0)
        obj.inflation_expectations_5y = data.get("inflation_expectations_5y", 0.0)
        obj.inflation_regime = data.get("inflation_regime", "Stable")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.expected_fed_reaction = data.get("expected_fed_reaction", "Neutral")
        return obj


# ---------------------------------------------------------------------------
# 5. Labor Market
# ---------------------------------------------------------------------------


class LaborMarketAssessment(BaseObject):
    """Assessment of US labor market conditions.

    Attributes:
        nfp: Non-farm payrolls change (thousands)
        unemployment_rate: U-3 unemployment rate (percent)
        initial_claims: Weekly initial jobless claims (thousands)
        continuing_claims: Continuing claims (thousands)
        wage_growth: Average hourly earnings YoY (percent)
        jolts: JOLTS job openings (millions)
        economic_strength: "Very_Strong", "Strong", "Moderate", "Weak", "Very_Weak"
        score: Labor Market Score (0-100, 100 = weakest = most gold-bullish)
        confidence: Confidence (0-1)
        expected_fed_path: "Hawkish", "Dovish", "Neutral", "Cutting", "Hiking"
    """

    def __init__(
        self,
        nfp: float = 0.0,
        unemployment_rate: float = 0.0,
        initial_claims: float = 0.0,
        continuing_claims: float = 0.0,
        wage_growth: float = 0.0,
        jolts: float = 0.0,
        economic_strength: str = "Moderate",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        expected_fed_path: str = "Neutral",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"LaborMarketAssessment|{ts}|{nfp}|{unemployment_rate}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.nfp = nfp
        self.unemployment_rate = unemployment_rate
        self.initial_claims = initial_claims
        self.continuing_claims = continuing_claims
        self.wage_growth = wage_growth
        self.jolts = jolts
        self.economic_strength = economic_strength
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.expected_fed_path = expected_fed_path
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Labor market analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "nfp": self.nfp,
            "unemployment_rate": self.unemployment_rate,
            "initial_claims": self.initial_claims,
            "continuing_claims": self.continuing_claims,
            "wage_growth": self.wage_growth,
            "jolts": self.jolts,
            "economic_strength": self.economic_strength,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "expected_fed_path": self.expected_fed_path,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "nfp": self.nfp,
                "unemployment_rate": self.unemployment_rate,
                "initial_claims": self.initial_claims,
                "continuing_claims": self.continuing_claims,
                "wage_growth": self.wage_growth,
                "jolts": self.jolts,
                "economic_strength": self.economic_strength,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
                "expected_fed_path": self.expected_fed_path,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "LaborMarketAssessment":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.nfp = data.get("nfp", 0.0)
        obj.unemployment_rate = data.get("unemployment_rate", 0.0)
        obj.initial_claims = data.get("initial_claims", 0.0)
        obj.continuing_claims = data.get("continuing_claims", 0.0)
        obj.wage_growth = data.get("wage_growth", 0.0)
        obj.jolts = data.get("jolts", 0.0)
        obj.economic_strength = data.get("economic_strength", "Moderate")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.expected_fed_path = data.get("expected_fed_path", "Neutral")
        return obj


# ---------------------------------------------------------------------------
# 6. Economic Growth
# ---------------------------------------------------------------------------


class EconomicGrowthAssessment(BaseObject):
    """Assessment of US economic growth and recession risk.

    Attributes:
        gdp: GDP QoQ annualized (percent)
        ism_manufacturing: ISM Manufacturing PMI
        ism_services: ISM Services PMI
        retail_sales: Retail sales MoM (percent)
        durable_goods: Durable goods orders MoM (percent)
        industrial_production: Industrial production MoM (percent)
        growth_phase: "Expansion", "Slowdown", "Contraction", "Recovery", "Boom"
        recession_risk: "Low", "Moderate", "Elevated", "High", "Imminent"
        score: Economic Growth Score (0-100, 100 = weakest = most gold-bullish)
        confidence: Confidence (0-1)
    """

    def __init__(
        self,
        gdp: float = 0.0,
        ism_manufacturing: float = 50.0,
        ism_services: float = 50.0,
        retail_sales: float = 0.0,
        durable_goods: float = 0.0,
        industrial_production: float = 0.0,
        growth_phase: str = "Expansion",
        recession_risk: str = "Low",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"EconomicGrowthAssessment|{ts}|{gdp}|{ism_manufacturing}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.gdp = gdp
        self.ism_manufacturing = ism_manufacturing
        self.ism_services = ism_services
        self.retail_sales = retail_sales
        self.durable_goods = durable_goods
        self.industrial_production = industrial_production
        self.growth_phase = growth_phase
        self.recession_risk = recession_risk
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Economic growth analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "gdp": self.gdp,
            "ism_manufacturing": self.ism_manufacturing,
            "ism_services": self.ism_services,
            "retail_sales": self.retail_sales,
            "durable_goods": self.durable_goods,
            "industrial_production": self.industrial_production,
            "growth_phase": self.growth_phase,
            "recession_risk": self.recession_risk,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "gdp": self.gdp,
                "ism_manufacturing": self.ism_manufacturing,
                "ism_services": self.ism_services,
                "retail_sales": self.retail_sales,
                "durable_goods": self.durable_goods,
                "industrial_production": self.industrial_production,
                "growth_phase": self.growth_phase,
                "recession_risk": self.recession_risk,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "EconomicGrowthAssessment":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.gdp = data.get("gdp", 0.0)
        obj.ism_manufacturing = data.get("ism_manufacturing", 50.0)
        obj.ism_services = data.get("ism_services", 50.0)
        obj.retail_sales = data.get("retail_sales", 0.0)
        obj.durable_goods = data.get("durable_goods", 0.0)
        obj.industrial_production = data.get("industrial_production", 0.0)
        obj.growth_phase = data.get("growth_phase", "Expansion")
        obj.recession_risk = data.get("recession_risk", "Low")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        return obj


# ---------------------------------------------------------------------------
# 7. Safe Haven Demand
# ---------------------------------------------------------------------------


class SafeHavenAssessment(BaseObject):
    """Assessment of safe haven demand for gold from geopolitical/financial stress.

    Attributes:
        risk_aversion_score: Market risk aversion (0-100, 100 = maximum fear)
        safe_haven_demand: "Extreme", "Elevated", "Normal", "Subdued", "None"
        active_conflicts: List of active geopolitical conflicts
        financial_stress: "Crisis", "Elevated", "Normal", "Low"
        vix_equivalent: Estimated VIX level
        score: Safe Haven Score (0-100, 100 = maximum gold-bullish)
        confidence: Confidence (0-1)
    """

    def __init__(
        self,
        risk_aversion_score: float = 50.0,
        safe_haven_demand: str = "Normal",
        active_conflicts: Optional[List[str]] = None,
        financial_stress: str = "Normal",
        vix_equivalent: float = 15.0,
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"SafeHavenAssessment|{ts}|{risk_aversion_score}|{financial_stress}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.risk_aversion_score = risk_aversion_score
        self.safe_haven_demand = safe_haven_demand
        self.active_conflicts: List[str] = active_conflicts or []
        self.financial_stress = financial_stress
        self.vix_equivalent = vix_equivalent
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Safe haven demand analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "risk_aversion_score": self.risk_aversion_score,
            "safe_haven_demand": self.safe_haven_demand,
            "active_conflicts": sorted(self.active_conflicts),
            "financial_stress": self.financial_stress,
            "vix_equivalent": self.vix_equivalent,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "risk_aversion_score": self.risk_aversion_score,
                "safe_haven_demand": self.safe_haven_demand,
                "active_conflicts": self.active_conflicts,
                "financial_stress": self.financial_stress,
                "vix_equivalent": self.vix_equivalent,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "SafeHavenAssessment":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.risk_aversion_score = data.get("risk_aversion_score", 50.0)
        obj.safe_haven_demand = data.get("safe_haven_demand", "Normal")
        obj.active_conflicts = list(data.get("active_conflicts", []))
        obj.financial_stress = data.get("financial_stress", "Normal")
        obj.vix_equivalent = data.get("vix_equivalent", 15.0)
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        return obj


# ---------------------------------------------------------------------------
# 8. Central Bank Gold Purchases
# ---------------------------------------------------------------------------


class CentralBankDemand(BaseObject):
    """Assessment of central bank gold reserve accumulation.

    Attributes:
        monthly_purchases: Monthly net purchases (tonnes)
        quarterly_purchases: Quarterly net purchases (tonnes)
        annual_purchases: Annual net purchases (tonnes)
        largest_buyers: List of largest purchasing countries
        demand_trend: "Accelerating", "Stable", "Declining", "Surge", "Minimal"
        reserve_diversification: "Aggressive", "Moderate", "Minimal", "None"
        score: Central Bank Demand Score (0-100, 100 = strongest demand)
        confidence: Confidence (0-1)
    """

    def __init__(
        self,
        monthly_purchases: float = 0.0,
        quarterly_purchases: float = 0.0,
        annual_purchases: float = 0.0,
        largest_buyers: Optional[List[str]] = None,
        demand_trend: str = "Stable",
        reserve_diversification: str = "Moderate",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"CentralBankDemand|{ts}|{monthly_purchases}|{demand_trend}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.monthly_purchases = monthly_purchases
        self.quarterly_purchases = quarterly_purchases
        self.annual_purchases = annual_purchases
        self.largest_buyers: List[str] = largest_buyers or []
        self.demand_trend = demand_trend
        self.reserve_diversification = reserve_diversification
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Central bank demand analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "monthly_purchases": self.monthly_purchases,
            "quarterly_purchases": self.quarterly_purchases,
            "annual_purchases": self.annual_purchases,
            "largest_buyers": sorted(self.largest_buyers),
            "demand_trend": self.demand_trend,
            "reserve_diversification": self.reserve_diversification,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "monthly_purchases": self.monthly_purchases,
                "quarterly_purchases": self.quarterly_purchases,
                "annual_purchases": self.annual_purchases,
                "largest_buyers": self.largest_buyers,
                "demand_trend": self.demand_trend,
                "reserve_diversification": self.reserve_diversification,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "CentralBankDemand":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.monthly_purchases = data.get("monthly_purchases", 0.0)
        obj.quarterly_purchases = data.get("quarterly_purchases", 0.0)
        obj.annual_purchases = data.get("annual_purchases", 0.0)
        obj.largest_buyers = list(data.get("largest_buyers", []))
        obj.demand_trend = data.get("demand_trend", "Stable")
        obj.reserve_diversification = data.get("reserve_diversification", "Moderate")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        return obj


# ---------------------------------------------------------------------------
# 9. Physical Gold Market
# ---------------------------------------------------------------------------


class PhysicalDemandSnapshot(BaseObject):
    """Snapshot of physical gold market supply and demand conditions.

    Attributes:
        comex_inventories: COMEX gold inventory (tonnes)
        shanghai_premium: Shanghai Gold Exchange premium/discount (USD/oz)
        etf_flows_monthly: Monthly ETF net flows (tonnes)
        indian_demand: "Strong", "Moderate", "Weak", "Festive_Season", "Price_Sensitive"
        chinese_demand: "Strong", "Moderate", "Weak", "Policy_Driven", "Price_Sensitive"
        mining_production: Annual mining production (tonnes)
        aisc: All-in sustaining cost per ounce (USD)
        seasonality: "Positive", "Neutral", "Negative", "Strong_Positive", "Strong_Negative"
        score: Physical Demand Score (0-100, 100 = strongest gold support)
        confidence: Confidence (0-1)
        supply_pressure: "Constrained", "Balanced", "Abundant", "Disrupted"
    """

    def __init__(
        self,
        comex_inventories: float = 0.0,
        shanghai_premium: float = 0.0,
        etf_flows_monthly: float = 0.0,
        indian_demand: str = "Moderate",
        chinese_demand: str = "Moderate",
        mining_production: float = 0.0,
        aisc: float = 0.0,
        seasonality: str = "Neutral",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        supply_pressure: str = "Balanced",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"PhysicalDemandSnapshot|{ts}|{comex_inventories}|{etf_flows_monthly}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.comex_inventories = comex_inventories
        self.shanghai_premium = shanghai_premium
        self.etf_flows_monthly = etf_flows_monthly
        self.indian_demand = indian_demand
        self.chinese_demand = chinese_demand
        self.mining_production = mining_production
        self.aisc = aisc
        self.seasonality = seasonality
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.supply_pressure = supply_pressure
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Physical market analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "comex_inventories": self.comex_inventories,
            "shanghai_premium": self.shanghai_premium,
            "etf_flows_monthly": self.etf_flows_monthly,
            "indian_demand": self.indian_demand,
            "chinese_demand": self.chinese_demand,
            "mining_production": self.mining_production,
            "aisc": self.aisc,
            "seasonality": self.seasonality,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "supply_pressure": self.supply_pressure,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "comex_inventories": self.comex_inventories,
                "shanghai_premium": self.shanghai_premium,
                "etf_flows_monthly": self.etf_flows_monthly,
                "indian_demand": self.indian_demand,
                "chinese_demand": self.chinese_demand,
                "mining_production": self.mining_production,
                "aisc": self.aisc,
                "seasonality": self.seasonality,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
                "supply_pressure": self.supply_pressure,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "PhysicalDemandSnapshot":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.comex_inventories = data.get("comex_inventories", 0.0)
        obj.shanghai_premium = data.get("shanghai_premium", 0.0)
        obj.etf_flows_monthly = data.get("etf_flows_monthly", 0.0)
        obj.indian_demand = data.get("indian_demand", "Moderate")
        obj.chinese_demand = data.get("chinese_demand", "Moderate")
        obj.mining_production = data.get("mining_production", 0.0)
        obj.aisc = data.get("aisc", 0.0)
        obj.seasonality = data.get("seasonality", "Neutral")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.supply_pressure = data.get("supply_pressure", "Balanced")
        return obj


# ---------------------------------------------------------------------------
# 10. Positioning
# ---------------------------------------------------------------------------


class PositioningAssessment(BaseObject):
    """Assessment of gold futures and ETF positioning.

    Attributes:
        managed_money_long: Managed money long contracts
        managed_money_short: Managed money short contracts
        commercial_long: Commercial long contracts
        commercial_short: Commercial short contracts
        open_interest: Total open interest
        etf_holdings: Total ETF holdings (tonnes)
        net_positioning: Net managed money position
        crowded_side: "Long", "Short", "Neutral", "Extreme_Long", "Extreme_Short"
        positioning_extreme: "Yes", "No", "Approaching"
        score: Positioning Score (0-100, 100 = most gold-bullish from positioning)
        confidence: Confidence (0-1)
    """

    def __init__(
        self,
        managed_money_long: float = 0.0,
        managed_money_short: float = 0.0,
        commercial_long: float = 0.0,
        commercial_short: float = 0.0,
        open_interest: float = 0.0,
        etf_holdings: float = 0.0,
        crowded_side: str = "Neutral",
        positioning_extreme: str = "No",
        score: float = 50.0,
        confidence: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"PositioningAssessment|{ts}|{managed_money_long}|{managed_money_short}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.managed_money_long = managed_money_long
        self.managed_money_short = managed_money_short
        self.commercial_long = commercial_long
        self.commercial_short = commercial_short
        self.open_interest = open_interest
        self.etf_holdings = etf_holdings
        self.net_positioning = managed_money_long - managed_money_short
        self.crowded_side = crowded_side
        self.positioning_extreme = positioning_extreme
        self.score = score
        self.confidence = confidence
        self.evidence_ids: List[str] = evidence_ids or []
        self.lifecycle.transition(LifecycleStage.ANALYZED, reason="Positioning analyzed")

    def _to_hashable_dict(self) -> dict:
        return {
            "managed_money_long": self.managed_money_long,
            "managed_money_short": self.managed_money_short,
            "commercial_long": self.commercial_long,
            "commercial_short": self.commercial_short,
            "open_interest": self.open_interest,
            "etf_holdings": self.etf_holdings,
            "crowded_side": self.crowded_side,
            "positioning_extreme": self.positioning_extreme,
            "score": self.score,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "managed_money_long": self.managed_money_long,
                "managed_money_short": self.managed_money_short,
                "commercial_long": self.commercial_long,
                "commercial_short": self.commercial_short,
                "open_interest": self.open_interest,
                "etf_holdings": self.etf_holdings,
                "net_positioning": self.net_positioning,
                "crowded_side": self.crowded_side,
                "positioning_extreme": self.positioning_extreme,
                "score": self.score,
                "confidence": self.confidence,
                "evidence_ids": self.evidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "PositioningAssessment":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.managed_money_long = data.get("managed_money_long", 0.0)
        obj.managed_money_short = data.get("managed_money_short", 0.0)
        obj.commercial_long = data.get("commercial_long", 0.0)
        obj.commercial_short = data.get("commercial_short", 0.0)
        obj.open_interest = data.get("open_interest", 0.0)
        obj.etf_holdings = data.get("etf_holdings", 0.0)
        obj.net_positioning = obj.managed_money_long - obj.managed_money_short
        obj.crowded_side = data.get("crowded_side", "Neutral")
        obj.positioning_extreme = data.get("positioning_extreme", "No")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        return obj


# ---------------------------------------------------------------------------
# Aggregate Macro Score
# ---------------------------------------------------------------------------


class MacroScore(BaseObject):
    """Aggregate macro score for XAUUSD combining all 10 macro drivers.

    Attributes:
        aggregate_score: Combined macro score (0-100, 100 = most gold-bullish)
        component_scores: Dict mapping driver names to their individual scores
        component_confidences: Dict mapping driver names to their confidences
        dominant_driver: The macro driver currently most affecting gold
        agreeing_drivers: List of drivers agreeing on gold direction
        conflicting_drivers: List of drivers conflicting with the dominant view
        driver_count: Number of drivers assessed
        assessment_timestamp: When the aggregate was computed
    """

    def __init__(
        self,
        aggregate_score: float = 50.0,
        component_scores: Optional[Dict[str, float]] = None,
        component_confidences: Optional[Dict[str, float]] = None,
        dominant_driver: str = "",
        agreeing_drivers: Optional[List[str]] = None,
        conflicting_drivers: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"MacroScore|{ts}|{aggregate_score}|{dominant_driver}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.aggregate_score = aggregate_score
        self.component_scores: Dict[str, float] = component_scores or {}
        self.component_confidences: Dict[str, float] = component_confidences or {}
        self.dominant_driver = dominant_driver
        self.agreeing_drivers: List[str] = agreeing_drivers or []
        self.conflicting_drivers: List[str] = conflicting_drivers or []
        self.lifecycle.transition(
            LifecycleStage.ANALYZED, reason=f"Macro score computed: {aggregate_score:.1f}"
        )

    @property
    def driver_count(self) -> int:
        return len(self.component_scores)

    def _to_hashable_dict(self) -> dict:
        return {
            "aggregate_score": self.aggregate_score,
            "component_scores": dict(sorted(self.component_scores.items())),
            "component_confidences": dict(sorted(self.component_confidences.items())),
            "dominant_driver": self.dominant_driver,
            "agreeing_drivers": sorted(self.agreeing_drivers),
            "conflicting_drivers": sorted(self.conflicting_drivers),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "aggregate_score": self.aggregate_score,
                "component_scores": self.component_scores,
                "component_confidences": self.component_confidences,
                "dominant_driver": self.dominant_driver,
                "agreeing_drivers": self.agreeing_drivers,
                "conflicting_drivers": self.conflicting_drivers,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MacroScore":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.aggregate_score = data.get("aggregate_score", 50.0)
        obj.component_scores = dict(data.get("component_scores", {}))
        obj.component_confidences = dict(data.get("component_confidences", {}))
        obj.dominant_driver = data.get("dominant_driver", "")
        obj.agreeing_drivers = list(data.get("agreeing_drivers", []))
        obj.conflicting_drivers = list(data.get("conflicting_drivers", []))
        return obj


# ---------------------------------------------------------------------------
# Macro Probability Assessment
# ---------------------------------------------------------------------------


class MacroProbability(BaseObject):
    """Probability distribution over gold market outcomes.

    Every probability references historical analogues for transparency.
    Based on historical event studies and deterministic rules.

    Attributes:
        probability_long: Probability gold rallies (0-1)
        probability_short: Probability gold falls (0-1)
        probability_range: Probability gold ranges (0-1)
        probability_high_volatility: Probability of high volatility (0-1)
        probability_breakout: Probability of a directional breakout (0-1)
        probability_fakeout: Probability of a false breakout (0-1)
        historical_analogues: List of historical analogue event IDs
        methodology: Description of probability methodology used
        dominant_bias: "Long", "Short", "Range", "Uncertain"
    """

    def __init__(
        self,
        probability_long: float = 0.33,
        probability_short: float = 0.33,
        probability_range: float = 0.34,
        probability_high_volatility: float = 0.3,
        probability_breakout: float = 0.3,
        probability_fakeout: float = 0.3,
        historical_analogues: Optional[List[str]] = None,
        methodology: str = "Weighted macro driver consensus",
        dominant_bias: str = "Uncertain",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"MacroProbability|{ts}|{probability_long}|{probability_short}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.probability_long = probability_long
        self.probability_short = probability_short
        self.probability_range = probability_range
        self.probability_high_volatility = probability_high_volatility
        self.probability_breakout = probability_breakout
        self.probability_fakeout = probability_fakeout
        self.historical_analogues: List[str] = historical_analogues or []
        self.methodology = methodology
        self.dominant_bias = dominant_bias
        self.lifecycle.transition(
            LifecycleStage.ANALYZED, reason=f"Probabilities computed: LONG={probability_long:.2f}"
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "probability_long": self.probability_long,
            "probability_short": self.probability_short,
            "probability_range": self.probability_range,
            "probability_high_volatility": self.probability_high_volatility,
            "probability_breakout": self.probability_breakout,
            "probability_fakeout": self.probability_fakeout,
            "historical_analogues": sorted(self.historical_analogues),
            "methodology": self.methodology,
            "dominant_bias": self.dominant_bias,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "probability_long": self.probability_long,
                "probability_short": self.probability_short,
                "probability_range": self.probability_range,
                "probability_high_volatility": self.probability_high_volatility,
                "probability_breakout": self.probability_breakout,
                "probability_fakeout": self.probability_fakeout,
                "historical_analogues": self.historical_analogues,
                "methodology": self.methodology,
                "dominant_bias": self.dominant_bias,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MacroProbability":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.probability_long = data.get("probability_long", 0.33)
        obj.probability_short = data.get("probability_short", 0.33)
        obj.probability_range = data.get("probability_range", 0.34)
        obj.probability_high_volatility = data.get("probability_high_volatility", 0.3)
        obj.probability_breakout = data.get("probability_breakout", 0.3)
        obj.probability_fakeout = data.get("probability_fakeout", 0.3)
        obj.historical_analogues = list(data.get("historical_analogues", []))
        obj.methodology = data.get("methodology", "Weighted macro driver consensus")
        obj.dominant_bias = data.get("dominant_bias", "Uncertain")
        return obj


# ---------------------------------------------------------------------------
# Macro Regime
# ---------------------------------------------------------------------------


class MacroRegime(BaseObject):
    """Current macro regime classification for XAUUSD.

    Attributes:
        regime_name: "Risk_On", "Risk_Off", "Inflation_Scare", "Growth_Scare",
                     "Fed_Pivot", "Stagflation", "Goldilocks", "Crisis",
                     "Liquidity_Driven", "Range_Bound"
        regime_description: Human-readable description
        primary_driver: Dominant macro driver
        secondary_drivers: Supporting macro drivers
        stability: "Stable", "Transitioning", "Volatile", "Uncertain"
        score: Regime score (0-100)
        confidence: Confidence in regime classification (0-1)
    """

    def __init__(
        self,
        regime_name: str = "Range_Bound",
        regime_description: str = "",
        primary_driver: str = "",
        secondary_drivers: Optional[List[str]] = None,
        stability: str = "Stable",
        score: float = 50.0,
        confidence: float = 0.0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"MacroRegime|{ts}|{regime_name}|{primary_driver}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.regime_name = regime_name
        self.regime_description = regime_description
        self.primary_driver = primary_driver
        self.secondary_drivers: List[str] = secondary_drivers or []
        self.stability = stability
        self.score = score
        self.confidence = confidence
        self.lifecycle.transition(
            LifecycleStage.ANALYZED, reason=f"Regime classified: {regime_name}"
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "regime_name": self.regime_name,
            "regime_description": self.regime_description,
            "primary_driver": self.primary_driver,
            "secondary_drivers": sorted(self.secondary_drivers),
            "stability": self.stability,
            "score": self.score,
            "confidence": self.confidence,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "regime_name": self.regime_name,
                "regime_description": self.regime_description,
                "primary_driver": self.primary_driver,
                "secondary_drivers": self.secondary_drivers,
                "stability": self.stability,
                "score": self.score,
                "confidence": self.confidence,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MacroRegime":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.regime_name = data.get("regime_name", "Range_Bound")
        obj.regime_description = data.get("regime_description", "")
        obj.primary_driver = data.get("primary_driver", "")
        obj.secondary_drivers = list(data.get("secondary_drivers", []))
        obj.stability = data.get("stability", "Stable")
        obj.score = data.get("score", 50.0)
        obj.confidence = data.get("confidence", 0.0)
        return obj


# ---------------------------------------------------------------------------
# Institutional Macro Report
# ---------------------------------------------------------------------------


class MacroReport(BaseObject):
    """Complete institutional macro report for XAUUSD.

    This is the final output of the Macro Intelligence Layer,
    designed for professional traders and analysts.

    Attributes:
        title: Report title
        regime: Current macro regime classification
        dominant_drivers: List of {driver, score, confidence, impact} dicts
        conflicting_drivers: List of drivers with conflicting signals
        macro_score_id: Link to MacroScore object
        probability_id: Link to MacroProbability object
        narrative: Full market narrative
        risk_assessment: Dict with risk factors
        expected_volatility: "Low", "Moderate", "Elevated", "High", "Extreme"
        suggested_bias: "Long", "Short", "Neutral", "Long_Bias", "Short_Bias"
        key_levels: Dict of key price levels
        report_format: "Summary", "Standard", "Detailed", "Institutional"
    """

    def __init__(
        self,
        title: str = "XAUUSD Macro Intelligence Report",
        regime: str = "Range_Bound",
        dominant_drivers: Optional[List[Dict[str, Any]]] = None,
        conflicting_drivers: Optional[List[Dict[str, Any]]] = None,
        macro_score_id: str = "",
        probability_id: str = "",
        narrative: str = "",
        risk_assessment: Optional[Dict[str, Any]] = None,
        expected_volatility: str = "Moderate",
        suggested_bias: str = "Neutral",
        key_levels: Optional[Dict[str, float]] = None,
        report_format: str = "Standard",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        if id is None:
            ts = (timestamp or utc_now()).isoformat()
            seed = f"MacroReport|{ts}|{title}|{regime}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp or utc_now()
        self.title = title
        self.regime = regime
        self.dominant_drivers: List[Dict[str, Any]] = dominant_drivers or []
        self.conflicting_drivers: List[Dict[str, Any]] = conflicting_drivers or []
        self.macro_score_id = macro_score_id
        self.probability_id = probability_id
        self.narrative = narrative
        self.risk_assessment: Dict[str, Any] = risk_assessment or {}
        self.expected_volatility = expected_volatility
        self.suggested_bias = suggested_bias
        self.key_levels: Dict[str, float] = key_levels or {}
        self.report_format = report_format
        self.lifecycle.transition(LifecycleStage.COMPLETE, reason=f"Report generated: {title}")

    def _to_hashable_dict(self) -> dict:
        return {
            "title": self.title,
            "regime": self.regime,
            "dominant_drivers": self.dominant_drivers,
            "conflicting_drivers": self.conflicting_drivers,
            "macro_score_id": self.macro_score_id,
            "probability_id": self.probability_id,
            "narrative": self.narrative,
            "risk_assessment": dict(sorted(self.risk_assessment.items())),
            "expected_volatility": self.expected_volatility,
            "suggested_bias": self.suggested_bias,
            "key_levels": dict(sorted(self.key_levels.items())),
            "report_format": self.report_format,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "title": self.title,
                "regime": self.regime,
                "dominant_drivers": self.dominant_drivers,
                "conflicting_drivers": self.conflicting_drivers,
                "macro_score_id": self.macro_score_id,
                "probability_id": self.probability_id,
                "narrative": self.narrative,
                "risk_assessment": self.risk_assessment,
                "expected_volatility": self.expected_volatility,
                "suggested_bias": self.suggested_bias,
                "key_levels": self.key_levels,
                "report_format": self.report_format,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MacroReport":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data.get("timestamp", utc_now().isoformat()))
        obj.title = data.get("title", "XAUUSD Macro Intelligence Report")
        obj.regime = data.get("regime", "Range_Bound")
        obj.dominant_drivers = list(data.get("dominant_drivers", []))
        obj.conflicting_drivers = list(data.get("conflicting_drivers", []))
        obj.macro_score_id = data.get("macro_score_id", "")
        obj.probability_id = data.get("probability_id", "")
        obj.narrative = data.get("narrative", "")
        obj.risk_assessment = dict(data.get("risk_assessment", {}))
        obj.expected_volatility = data.get("expected_volatility", "Moderate")
        obj.suggested_bias = data.get("suggested_bias", "Neutral")
        obj.key_levels = {k: float(v) for k, v in data.get("key_levels", {}).items()}
        obj.report_format = data.get("report_format", "Standard")
        return obj
