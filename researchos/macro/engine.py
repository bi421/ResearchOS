"""MacroAnalysisEngine — Institutional XAUUSD Macro Intelligence Service.

This engine provides deterministic macro analysis for gold across 10 drivers:
1. US Real Yields    2. US Dollar (DXY)    3. Federal Reserve
4. Inflation         5. Labor Market       6. Economic Growth
7. Safe Haven        8. Central Bank Demand 9. Physical Market
10. Positioning

Every method produces deterministic, fully attributable objects that
integrate with the existing TRADER-OS audit chain, attribution system,
and serialization framework.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from researchos.core.base_object import BaseObject
from researchos.objects.macro import (
    CentralBankDemand,
    DollarStrengthSnapshot,
    EconomicGrowthAssessment,
    FedPolicyAssessment,
    InflationAssessment,
    LaborMarketAssessment,
    MacroProbability,
    MacroRegime,
    MacroReport,
    MacroScore,
    PhysicalDemandSnapshot,
    PositioningAssessment,
    RealYieldSnapshot,
    SafeHavenAssessment,
)
from researchos.objects.process import AuditEntry
from researchos.repository.interface import RepositoryInterface


# Macro driver names (consistent identifiers)
DRIVER_REAL_YIELD = "Real_Yield"
DRIVER_DXY = "DXY"
DRIVER_FED = "Fed"
DRIVER_INFLATION = "Inflation"
DRIVER_LABOR = "Labor_Market"
DRIVER_GROWTH = "Economic_Growth"
DRIVER_SAFE_HAVEN = "Safe_Haven"
DRIVER_CENTRAL_BANK = "Central_Bank"
DRIVER_PHYSICAL = "Physical_Demand"
DRIVER_POSITIONING = "Positioning"

ALL_DRIVERS = [
    DRIVER_REAL_YIELD, DRIVER_DXY, DRIVER_FED, DRIVER_INFLATION,
    DRIVER_LABOR, DRIVER_GROWTH, DRIVER_SAFE_HAVEN,
    DRIVER_CENTRAL_BANK, DRIVER_PHYSICAL, DRIVER_POSITIONING,
]

# Weights for aggregate macro score (sums to 1.0)
DRIVER_WEIGHTS: Dict[str, float] = {
    DRIVER_REAL_YIELD: 0.18,
    DRIVER_DXY: 0.15,
    DRIVER_FED: 0.14,
    DRIVER_INFLATION: 0.13,
    DRIVER_LABOR: 0.08,
    DRIVER_GROWTH: 0.07,
    DRIVER_SAFE_HAVEN: 0.10,
    DRIVER_CENTRAL_BANK: 0.06,
    DRIVER_PHYSICAL: 0.05,
    DRIVER_POSITIONING: 0.04,
}

# Regime classification thresholds
REGIME_SCORE_MAP: Dict[str, Tuple[float, float, str, str]] = {
    "Crisis": (85, 100, "Risk_Off", "Financial/geopolitical crisis driving safe-haven flows"),
    "Risk_Off": (70, 84, "Risk_Off", "Broad risk aversion supporting gold"),
    "Stagflation": (65, 84, "Mixed", "High inflation + weak growth = gold-friendly"),
    "Fed_Pivot": (60, 80, "Mixed", "Market pricing Fed pivot = gold supportive"),
    "Inflation_Scare": (55, 75, "Risk_Off", "Rising inflation concerns driving gold demand"),
    "Goldilocks": (30, 50, "Risk_On", "Strong growth + contained inflation = neutral for gold"),
    "Risk_On": (0, 35, "Risk_On", "Risk appetite high = headwind for gold"),
    "Range_Bound": (40, 60, "Neutral", "No dominant macro catalyst, gold ranging"),
}


class MacroAnalysisEngine:
    """Institutional XAUUSD Macro Intelligence Service.

    Provides deterministic macro analysis across 10 drivers, aggregate
    scoring, probability estimation, regime classification, and
    institutional report generation.

    Usage:
        engine = MacroAnalysisEngine(repository)
        real_yield = engine.assess_real_yields(...)
        macro_score = engine.compute_macro_score()
        probabilities = engine.compute_probabilities(macro_score)
        report = engine.generate_report(macro_score, probabilities)
    """

    def __init__(self, repository: RepositoryInterface):
        self.repo = repository

    # ------------------------------------------------------------------
    # 1. US Real Yields
    # ------------------------------------------------------------------

    def assess_real_yields(
        self,
        ten_year_yield: float,
        five_year_yield: float,
        inflation_expectations: float,
        tips_yield: float,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> RealYieldSnapshot:
        """Assess US real yield conditions and impact on gold.

        Scoring logic (deterministic):
        - Lower real yields = higher gold score (inverse relationship)
        - Falling real yield trend = bullish for gold
        - Extreme negative real yields = strongly bullish
        """
        # Compute real yield curve
        real_curve = self._classify_yield_curve(ten_year_yield, five_year_yield)
        real_trend = self._classify_real_yield_trend(tips_yield, inflation_expectations)
        score = self._score_real_yields(tips_yield, real_trend, ten_year_yield)
        confidence = self._compute_real_yield_confidence(tips_yield, ten_year_yield)
        impact = self._classify_gold_impact(score)

        snapshot = RealYieldSnapshot(
            ten_year_yield=ten_year_yield,
            five_year_yield=five_year_yield,
            inflation_expectations=inflation_expectations,
            tips_yield=tips_yield,
            real_yield_curve=real_curve,
            real_yield_trend=real_trend,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            expected_gold_impact=impact,
            ontology_tags=ontology_tags,
        )
        self.repo.save(snapshot)
        self._audit("REAL_YIELD_ASSESSED", snapshot.id, f"Score={score}, Trend={real_trend}")
        return snapshot

    def _classify_yield_curve(self, ten_yr: float, five_yr: float) -> str:
        diff = ten_yr - five_yr
        if diff > 0.5:
            return "Steepening"
        elif diff > 0.1:
            return "Normal"
        elif diff > -0.1:
            return "Flat"
        elif diff > -0.5:
            return "Flattening"
        else:
            return "Inverted"

    def _classify_real_yield_trend(self, tips: float, inflation_exp: float) -> str:
        real = tips
        if real > 2.5:
            return "Extreme_Rising"
        elif real > 1.5:
            return "Rising"
        elif real > 0.5:
            return "Stable"
        elif real > -0.5:
            return "Falling"
        else:
            return "Extreme_Falling"

    def _score_real_yields(self, tips: float, trend: str, nominal: float) -> float:
        # Base score from TIPS level (lower = more gold bullish)
        if tips <= -1.0:
            base = 90.0
        elif tips <= -0.5:
            base = 80.0
        elif tips <= 0.0:
            base = 70.0
        elif tips <= 0.5:
            base = 55.0
        elif tips <= 1.0:
            base = 40.0
        elif tips <= 1.5:
            base = 30.0
        elif tips <= 2.0:
            base = 20.0
        else:
            base = 10.0

        # Trend adjustment
        trend_adj = {
            "Extreme_Falling": 15,
            "Falling": 10,
            "Stable": 0,
            "Rising": -10,
            "Extreme_Rising": -20,
        }.get(trend, 0)

        # Inflation expectations adjustment
        if nominal > 5.0 and tips < 0.5:
            infl_adj = 10  # High nominal + low real = inflation concern = gold bullish
        else:
            infl_adj = 0

        return max(0.0, min(100.0, base + trend_adj + infl_adj))

    def _compute_real_yield_confidence(self, tips: float, nominal: float) -> float:
        # Higher confidence when real yields are clearly defined
        if tips != 0.0 and nominal != 0.0:
            return 0.85
        elif tips != 0.0 or nominal != 0.0:
            return 0.60
        return 0.30

    def _classify_gold_impact(self, score: float) -> str:
        if score >= 80:
            return "Strongly_Bullish"
        elif score >= 65:
            return "Bullish"
        elif score >= 45:
            return "Neutral"
        elif score >= 25:
            return "Bearish"
        else:
            return "Strongly_Bearish"

    # ------------------------------------------------------------------
    # 2. US Dollar (DXY)
    # ------------------------------------------------------------------

    def assess_dollar(
        self,
        dxy: float,
        dxy_trend: str = "Ranging",
        dxy_momentum: str = "Neutral",
        relative_strength: float = 50.0,
        multi_timeframe_trend: str = "Mixed",
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> DollarStrengthSnapshot:
        """Assess US Dollar strength and impact on gold.

        Gold is inversely correlated to DXY. Scoring reflects this:
        higher DXY = lower gold score.
        """
        score = self._score_dollar(dxy, dxy_trend, dxy_momentum, relative_strength)
        confidence = self._compute_dollar_confidence(dxy_trend, dxy_momentum)

        snapshot = DollarStrengthSnapshot(
            dxy=dxy,
            dxy_trend=dxy_trend,
            dxy_momentum=dxy_momentum,
            relative_strength=relative_strength,
            multi_timeframe_trend=multi_timeframe_trend,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            ontology_tags=ontology_tags,
        )
        self.repo.save(snapshot)
        self._audit("DOLLAR_ASSESSED", snapshot.id, f"DXY={dxy}, Score={score}")
        return snapshot

    def _score_dollar(self, dxy: float, trend: str, momentum: str, rs: float) -> float:
        # Base score from DXY level (lower DXY = more gold bullish)
        if dxy >= 110:
            base = 15.0
        elif dxy >= 105:
            base = 30.0
        elif dxy >= 100:
            base = 45.0
        elif dxy >= 97:
            base = 55.0
        elif dxy >= 94:
            base = 65.0
        elif dxy >= 90:
            base = 75.0
        else:
            base = 85.0

        # Trend adjustment
        trend_adj = {
            "Breakout_Down": 20,
            "Falling": 15,
            "Ranging": 0,
            "Rising": -15,
            "Breakout_Up": -20,
        }.get(trend, 0)

        # Momentum adjustment
        mom_adj = {
            "Strong_Bearish": 10,
            "Bearish": 5,
            "Neutral": 0,
            "Bullish": -5,
            "Strong_Bullish": -10,
        }.get(momentum, 0)

        # Relative strength adjustment (RS > 70 = overbought = reversal risk)
        rs_adj = 0
        if rs > 70:
            rs_adj = 5  # Overbought dollar = potential reversal = slight gold support
        elif rs < 30:
            rs_adj = -5  # Oversold dollar = potential bounce = slight gold headwind

        return max(0.0, min(100.0, base + trend_adj + mom_adj + rs_adj))

    def _compute_dollar_confidence(self, trend: str, momentum: str) -> float:
        if trend in ("Breakout_Up", "Breakout_Down") and momentum != "Neutral":
            return 0.85
        elif trend != "Ranging":
            return 0.70
        elif momentum != "Neutral":
            return 0.60
        return 0.45

    # ------------------------------------------------------------------
    # 3. Federal Reserve
    # ------------------------------------------------------------------

    def assess_fed_policy(
        self,
        rate_decision: str = "",
        rate_change_bps: float = 0.0,
        dot_plot_median: float = 0.0,
        balance_sheet_change: float = 0.0,
        policy_classification: str = "Neutral",
        hawkishness_score: float = 50.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> FedPolicyAssessment:
        """Assess Federal Reserve policy stance and gold impact."""
        score = self._score_fed_policy(policy_classification, hawkishness_score, rate_change_bps)
        confidence = self._compute_fed_confidence(policy_classification, rate_change_bps)
        gold_pressure = "Bullish" if score >= 60 else ("Bearish" if score <= 40 else "Neutral")

        assessment = FedPolicyAssessment(
            rate_decision=rate_decision,
            rate_change_bps=rate_change_bps,
            dot_plot_median=dot_plot_median,
            balance_sheet_change=balance_sheet_change,
            policy_classification=policy_classification,
            hawkishness_score=hawkishness_score,
            gold_pressure=gold_pressure,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("FED_ASSESSED", assessment.id, f"Policy={policy_classification}, Score={score}")
        return assessment

    def _score_fed_policy(self, classification: str, hawkishness: float, rate_change: float) -> float:
        # Higher score = more dovish = more gold bullish
        class_map = {
            "Extremely_Dovish": 90, "Dovish": 75, "Neutral": 50,
            "Hawkish": 25, "Extremely_Hawkish": 10,
        }
        base = class_map.get(classification, 50.0)

        # Override with hawkishness score if available
        if hawkishness != 50.0:
            base = 100.0 - hawkishness  # Invert: low hawkishness = high gold score

        # Rate change adjustment (rate cuts = bullish for gold)
        if rate_change < 0:
            return min(100.0, base + 15)
        elif rate_change > 0:
            return max(0.0, base - 15)
        return base

    def _compute_fed_confidence(self, classification: str, rate_change: float) -> float:
        if classification in ("Extremely_Hawkish", "Extremely_Dovish"):
            return 0.85
        elif classification != "Neutral":
            return 0.70
        elif rate_change != 0:
            return 0.65
        return 0.40

    # ------------------------------------------------------------------
    # 4. Inflation
    # ------------------------------------------------------------------

    def assess_inflation(
        self,
        cpi: float,
        core_cpi: float = 0.0,
        ppi: float = 0.0,
        pce: float = 0.0,
        inflation_expectations_5y: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> InflationAssessment:
        """Assess inflation conditions and implications for gold."""
        regime = self._classify_inflation_regime(cpi, core_cpi)
        score = self._score_inflation(cpi, core_cpi, regime)
        confidence = self._compute_inflation_confidence(cpi, core_cpi)
        fed_reaction = self._expected_fed_reaction(regime, cpi)

        assessment = InflationAssessment(
            cpi=cpi,
            core_cpi=core_cpi,
            ppi=ppi,
            pce=pce,
            inflation_expectations_5y=inflation_expectations_5y,
            inflation_regime=regime,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            expected_fed_reaction=fed_reaction,
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("INFLATION_ASSESSED", assessment.id, f"CPI={cpi}, Regime={regime}")
        return assessment

    def _classify_inflation_regime(self, cpi: float, core_cpi: float) -> str:
        avg = (cpi + core_cpi) / 2 if core_cpi else cpi
        if avg > 10:
            return "Hyperinflation"
        elif avg > 5:
            return "High_Inflation"
        elif avg > 3:
            return "Moderate_Inflation"
        elif avg > 1:
            return "Stable"
        elif avg > 0:
            return "Disinflation"
        else:
            return "Deflation"

    def _score_inflation(self, cpi: float, core_cpi: float, regime: str) -> float:
        # Higher inflation = more gold bullish (store of value)
        avg = (cpi + core_cpi) / 2 if core_cpi else cpi
        if regime == "Hyperinflation":
            return 95.0
        elif regime == "High_Inflation":
            return 85.0
        elif regime == "Moderate_Inflation":
            return 70.0
        elif regime == "Stable":
            return 50.0
        elif regime == "Disinflation":
            return 40.0 if avg > 0 else 30.0
        else:  # Deflation
            return 25.0

    def _compute_inflation_confidence(self, cpi: float, core_cpi: float) -> float:
        if cpi != 0.0 and core_cpi != 0.0:
            return 0.80
        elif cpi != 0.0:
            return 0.55
        return 0.30

    def _expected_fed_reaction(self, regime: str, cpi: float) -> str:
        if regime in ("Hyperinflation", "High_Inflation"):
            return "Hawkish"
        elif regime == "Moderate_Inflation":
            return "Restrictive" if cpi > 4 else "Neutral"
        elif regime == "Disinflation":
            return "Dovish"
        elif regime == "Deflation":
            return "Accommodative"
        return "Neutral"

    # ------------------------------------------------------------------
    # 5. Labor Market
    # ------------------------------------------------------------------

    def assess_labor_market(
        self,
        nfp: float = 0.0,
        unemployment_rate: float = 0.0,
        initial_claims: float = 0.0,
        continuing_claims: float = 0.0,
        wage_growth: float = 0.0,
        jolts: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> LaborMarketAssessment:
        """Assess US labor market conditions."""
        strength = self._classify_labor_strength(nfp, unemployment_rate, wage_growth)
        score = self._score_labor_market(strength, unemployment_rate)
        confidence = self._compute_labor_confidence(nfp, unemployment_rate)
        fed_path = self._expected_fed_path_from_labor(strength, wage_growth)

        assessment = LaborMarketAssessment(
            nfp=nfp,
            unemployment_rate=unemployment_rate,
            initial_claims=initial_claims,
            continuing_claims=continuing_claims,
            wage_growth=wage_growth,
            jolts=jolts,
            economic_strength=strength,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            expected_fed_path=fed_path,
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("LABOR_ASSESSED", assessment.id, f"NFP={nfp}, UE={unemployment_rate}")
        return assessment

    def _classify_labor_strength(self, nfp: float, ue: float, wages: float) -> str:
        # Higher NFP, lower UE = stronger labor market
        if nfp > 300 and ue < 3.5:
            return "Very_Strong"
        elif nfp > 200 and ue < 4.0:
            return "Strong"
        elif nfp > 100 and ue < 5.0:
            return "Moderate"
        elif nfp > 0 and ue < 6.0:
            return "Weak"
        else:
            return "Very_Weak"

    def _score_labor_market(self, strength: str, ue: float) -> float:
        # Weaker labor market = more gold bullish (fed cuts)
        strength_map = {
            "Very_Strong": 20, "Strong": 35, "Moderate": 50,
            "Weak": 70, "Very_Weak": 85,
        }
        base = strength_map.get(strength, 50)

        # Unemployment adjustment
        if ue > 6.0:
            base += 10
        elif ue > 5.0:
            base += 5

        return max(0.0, min(100.0, base))

    def _compute_labor_confidence(self, nfp: float, ue: float) -> float:
        if nfp != 0.0 and ue != 0.0:
            return 0.75
        elif nfp != 0.0 or ue != 0.0:
            return 0.50
        return 0.25

    def _expected_fed_path_from_labor(self, strength: str, wages: float) -> str:
        if strength in ("Very_Weak", "Weak"):
            return "Cutting"
        elif strength == "Moderate":
            return "Neutral"
        elif strength == "Strong":
            return "Hiking" if wages > 4.0 else "Hawkish"
        else:  # Very_Strong
            return "Hiking"

    # ------------------------------------------------------------------
    # 6. Economic Growth
    # ------------------------------------------------------------------

    def assess_economic_growth(
        self,
        gdp: float = 0.0,
        ism_manufacturing: float = 50.0,
        ism_services: float = 50.0,
        retail_sales: float = 0.0,
        durable_goods: float = 0.0,
        industrial_production: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> EconomicGrowthAssessment:
        """Assess US economic growth and recession risk."""
        phase = self._classify_growth_phase(gdp, ism_manufacturing, ism_services)
        recession = self._assess_recession_risk(ism_manufacturing, ism_services, gdp)
        score = self._score_growth(phase, recession)

        assessment = EconomicGrowthAssessment(
            gdp=gdp,
            ism_manufacturing=ism_manufacturing,
            ism_services=ism_services,
            retail_sales=retail_sales,
            durable_goods=durable_goods,
            industrial_production=industrial_production,
            growth_phase=phase,
            recession_risk=recession,
            score=score,
            confidence=0.70,
            evidence_ids=evidence_ids or [],
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("GROWTH_ASSESSED", assessment.id, f"GDP={gdp}, ISM_Mfg={ism_manufacturing}")
        return assessment

    def _classify_growth_phase(self, gdp: float, ism_mfg: float, ism_svc: float) -> str:
        avg_ism = (ism_mfg + ism_svc) / 2
        if avg_ism > 55 and gdp > 3:
            return "Boom"
        elif avg_ism > 50 and gdp > 2:
            return "Expansion"
        elif avg_ism > 45 and gdp > 0:
            return "Slowdown"
        elif avg_ism > 40 and gdp > -2:
            return "Contraction"
        else:
            return "Recovery"

    def _assess_recession_risk(self, ism_mfg: float, ism_svc: float, gdp: float) -> str:
        if ism_mfg < 40 and ism_svc < 45 and gdp < 0:
            return "Imminent"
        elif ism_mfg < 45 and gdp < 1:
            return "High"
        elif ism_mfg < 48 and gdp < 2:
            return "Elevated"
        elif ism_mfg < 50:
            return "Moderate"
        else:
            return "Low"

    def _score_growth(self, phase: str, recession: str) -> float:
        # Weaker growth = more gold bullish (safe haven + fed support)
        phase_map = {
            "Boom": 20, "Expansion": 30, "Slowdown": 55,
            "Contraction": 75, "Recovery": 45,
        }
        base = phase_map.get(phase, 50)

        rec_adj = {
            "Imminent": 20, "High": 15, "Elevated": 8, "Moderate": 3, "Low": 0,
        }.get(recession, 0)

        return max(0.0, min(100.0, base + rec_adj))

    # ------------------------------------------------------------------
    # 7. Safe Haven Demand
    # ------------------------------------------------------------------

    def assess_safe_haven(
        self,
        risk_aversion_score: float = 50.0,
        safe_haven_demand: str = "Normal",
        active_conflicts: Optional[List[str]] = None,
        financial_stress: str = "Normal",
        vix_equivalent: float = 15.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> SafeHavenAssessment:
        """Assess safe haven demand for gold."""
        score = self._score_safe_haven(risk_aversion_score, safe_haven_demand, financial_stress, vix_equivalent)
        confidence = self._compute_safe_haven_confidence(risk_aversion_score, len(active_conflicts or []))

        assessment = SafeHavenAssessment(
            risk_aversion_score=risk_aversion_score,
            safe_haven_demand=safe_haven_demand,
            active_conflicts=active_conflicts or [],
            financial_stress=financial_stress,
            vix_equivalent=vix_equivalent,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("SAFE_HAVEN_ASSESSED", assessment.id, f"Risk_Aversion={risk_aversion_score}")
        return assessment

    def _score_safe_haven(self, aversion: float, demand: str, stress: str, vix: float) -> float:
        # Higher risk aversion = more gold bullish
        aversion_score = aversion  # Already 0-100

        demand_map = {"Extreme": 95, "Elevated": 75, "Normal": 50, "Subdued": 30, "None": 15}
        demand_score = demand_map.get(demand, 50)

        stress_map = {"Crisis": 95, "Elevated": 70, "Normal": 50, "Low": 30}
        stress_score = stress_map.get(stress, 50)

        vix_score = min(100, vix * 2)

        return max(0.0, min(100.0, (aversion_score * 0.35 + demand_score * 0.30 + stress_score * 0.20 + vix_score * 0.15)))

    def _compute_safe_haven_confidence(self, aversion: float, conflict_count: int) -> float:
        if conflict_count > 2 and aversion > 70:
            return 0.85
        elif conflict_count > 0 and aversion > 50:
            return 0.70
        elif aversion != 50:
            return 0.55
        return 0.35

    # ------------------------------------------------------------------
    # 8. Central Bank Gold Purchases
    # ------------------------------------------------------------------

    def assess_central_bank_demand(
        self,
        monthly_purchases: float = 0.0,
        quarterly_purchases: float = 0.0,
        annual_purchases: float = 0.0,
        largest_buyers: Optional[List[str]] = None,
        demand_trend: str = "Stable",
        reserve_diversification: str = "Moderate",
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> CentralBankDemand:
        """Assess central bank gold demand."""
        score = self._score_central_bank_demand(monthly_purchases, annual_purchases, demand_trend)
        confidence = self._compute_cb_confidence(monthly_purchases, annual_purchases)

        assessment = CentralBankDemand(
            monthly_purchases=monthly_purchases,
            quarterly_purchases=quarterly_purchases,
            annual_purchases=annual_purchases,
            largest_buyers=largest_buyers or [],
            demand_trend=demand_trend,
            reserve_diversification=reserve_diversification,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("CB_DEMAND_ASSESSED", assessment.id, f"Monthly={monthly_purchases}t, Trend={demand_trend}")
        return assessment

    def _score_central_bank_demand(self, monthly: float, annual: float, trend: str) -> float:
        # Score based on purchase volumes
        if annual > 1000:
            volume_score = 90
        elif annual > 800:
            volume_score = 80
        elif annual > 600:
            volume_score = 70
        elif annual > 400:
            volume_score = 60
        elif annual > 200:
            volume_score = 50
        elif annual > 100:
            volume_score = 40
        elif annual > 0:
            volume_score = 30
        else:
            volume_score = 20

        trend_adj = {"Surge": 15, "Accelerating": 10, "Stable": 0, "Declining": -10, "Minimal": -15}.get(trend, 0)

        return max(0.0, min(100.0, volume_score + trend_adj))

    def _compute_cb_confidence(self, monthly: float, annual: float) -> float:
        if monthly > 0 and annual > 0:
            return 0.80
        elif annual > 0:
            return 0.60
        return 0.30

    # ------------------------------------------------------------------
    # 9. Physical Gold Market
    # ------------------------------------------------------------------

    def assess_physical_demand(
        self,
        comex_inventories: float = 0.0,
        shanghai_premium: float = 0.0,
        etf_flows_monthly: float = 0.0,
        indian_demand: str = "Moderate",
        chinese_demand: str = "Moderate",
        mining_production: float = 0.0,
        aisc: float = 0.0,
        seasonality: str = "Neutral",
        supply_pressure: str = "Balanced",
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> PhysicalDemandSnapshot:
        """Assess physical gold market conditions."""
        score = self._score_physical_demand(etf_flows_monthly, indian_demand, chinese_demand, seasonality, supply_pressure)
        confidence = self._compute_physical_confidence(comex_inventories, etf_flows_monthly)

        snapshot = PhysicalDemandSnapshot(
            comex_inventories=comex_inventories,
            shanghai_premium=shanghai_premium,
            etf_flows_monthly=etf_flows_monthly,
            indian_demand=indian_demand,
            chinese_demand=chinese_demand,
            mining_production=mining_production,
            aisc=aisc,
            seasonality=seasonality,
            score=score,
            confidence=confidence,
            evidence_ids=evidence_ids or [],
            supply_pressure=supply_pressure,
            ontology_tags=ontology_tags,
        )
        self.repo.save(snapshot)
        self._audit("PHYSICAL_ASSESSED", snapshot.id, f"ETF_Flows={etf_flows_monthly}t")
        return snapshot

    def _score_physical_demand(self, etf_flows: float, india: str, china: str, seasonality: str, supply: str) -> float:
        # ETF flows (positive = bullish)
        etf_score = max(0, min(100, 50 + etf_flows * 5))

        demand_map = {"Strong": 80, "Festive_Season": 75, "Policy_Driven": 70, "Moderate": 50, "Price_Sensitive": 40, "Weak": 25}
        india_score = demand_map.get(india, 50)
        china_score = demand_map.get(china, 50)

        seas_map = {"Strong_Positive": 75, "Positive": 65, "Neutral": 50, "Negative": 35, "Strong_Negative": 20}
        seas_score = seas_map.get(seasonality, 50)

        supply_map = {"Disrupted": 85, "Constrained": 70, "Balanced": 50, "Abundant": 30}
        supply_score = supply_map.get(supply, 50)

        return max(0.0, min(100.0, (etf_score * 0.25 + india_score * 0.20 + china_score * 0.20 + seas_score * 0.15 + supply_score * 0.20)))

    def _compute_physical_confidence(self, inventories: float, etf_flows: float) -> float:
        if inventories > 0 and etf_flows != 0:
            return 0.70
        elif inventories > 0 or etf_flows != 0:
            return 0.50
        return 0.25

    # ------------------------------------------------------------------
    # 10. Positioning
    # ------------------------------------------------------------------

    def assess_positioning(
        self,
        managed_money_long: float = 0.0,
        managed_money_short: float = 0.0,
        commercial_long: float = 0.0,
        commercial_short: float = 0.0,
        open_interest: float = 0.0,
        etf_holdings: float = 0.0,
        evidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> PositioningAssessment:
        """Assess gold futures and ETF positioning."""
        net = managed_money_long - managed_money_short
        crowded, extreme = self._classify_positioning(net, managed_money_long, managed_money_short)
        score = self._score_positioning(net, crowded, extreme)

        assessment = PositioningAssessment(
            managed_money_long=managed_money_long,
            managed_money_short=managed_money_short,
            commercial_long=commercial_long,
            commercial_short=commercial_short,
            open_interest=open_interest,
            etf_holdings=etf_holdings,
            crowded_side=crowded,
            positioning_extreme=extreme,
            score=score,
            confidence=0.65 if (managed_money_long or managed_money_short) else 0.25,
            evidence_ids=evidence_ids or [],
            ontology_tags=ontology_tags,
        )
        self.repo.save(assessment)
        self._audit("POSITIONING_ASSESSED", assessment.id, f"Net={net:.0f}, Crowded={crowded}")
        return assessment

    def _classify_positioning(self, net: float, mm_long: float, mm_short: float) -> Tuple[str, str]:
        total = mm_long + mm_short
        if total == 0:
            return "Neutral", "No"
        net_ratio = (mm_long - mm_short) / total  # -1 to 1

        if net_ratio > 0.6:
            return "Extreme_Long", "Yes"
        elif net_ratio > 0.3:
            return "Long", "Approaching"
        elif net_ratio < -0.6:
            return "Extreme_Short", "Yes"
        elif net_ratio < -0.3:
            return "Short", "Approaching"
        else:
            return "Neutral", "No"

    def _score_positioning(self, net: float, crowded: str, extreme: str) -> float:
        # Extreme long = contrarian bearish signal (crowded trade)
        # Extreme short = contrarian bullish signal
        crowded_map = {
            "Extreme_Short": 80,
            "Short": 65,
            "Neutral": 50,
            "Long": 35,
            "Extreme_Long": 20,
        }
        base = crowded_map.get(crowded, 50)

        if extreme == "Yes":
            base += 5 if crowded in ("Extreme_Short", "Short") else -5

        return max(0.0, min(100.0, base))

    # ------------------------------------------------------------------
    # Aggregate Macro Score
    # ------------------------------------------------------------------

    def compute_macro_score(
        self,
        ontology_tags: Optional[List[str]] = None,
    ) -> MacroScore:
        """Compute aggregate macro score from all stored assessments.

        Collects the most recent assessment for each driver from the
        repository and computes a weighted aggregate score.
        """
        scores: Dict[str, float] = {}
        confidences: Dict[str, float] = {}

        # Collect scores from each driver's latest assessment
        driver_types = {
            DRIVER_REAL_YIELD: RealYieldSnapshot,
            DRIVER_DXY: DollarStrengthSnapshot,
            DRIVER_FED: FedPolicyAssessment,
            DRIVER_INFLATION: InflationAssessment,
            DRIVER_LABOR: LaborMarketAssessment,
            DRIVER_GROWTH: EconomicGrowthAssessment,
            DRIVER_SAFE_HAVEN: SafeHavenAssessment,
            DRIVER_CENTRAL_BANK: CentralBankDemand,
            DRIVER_PHYSICAL: PhysicalDemandSnapshot,
            DRIVER_POSITIONING: PositioningAssessment,
        }

        for driver_name, driver_cls in driver_types.items():
            latest = self._get_latest_by_type(driver_cls)
            if latest is not None:
                scores[driver_name] = getattr(latest, "score", 50.0)
                confidences[driver_name] = getattr(latest, "confidence", 0.0)

        if not scores:
            return MacroScore(aggregate_score=50.0, ontology_tags=ontology_tags)

        # Weighted aggregate
        total_weight = 0.0
        weighted_sum = 0.0
        for driver, score in scores.items():
            weight = DRIVER_WEIGHTS.get(driver, 0.1) * confidences.get(driver, 0.5)
            weighted_sum += score * weight
            total_weight += weight

        aggregate = round(weighted_sum / max(total_weight, 0.01), 1)

        # Determine dominant driver (highest weighted contribution)
        dominant = max(scores, key=lambda d: scores[d] * DRIVER_WEIGHTS.get(d, 0.1) * confidences.get(d, 0.5))

        # Determine agreeing vs conflicting drivers
        agreeing, conflicting = self._classify_drivers(scores, dominant)

        macro_score = MacroScore(
            aggregate_score=aggregate,
            component_scores=scores,
            component_confidences=confidences,
            dominant_driver=dominant,
            agreeing_drivers=agreeing,
            conflicting_drivers=conflicting,
            ontology_tags=ontology_tags,
        )
        self.repo.save(macro_score)
        self._audit("MACRO_SCORE_COMPUTED", macro_score.id, f"Aggregate={aggregate}, Dominant={dominant}")
        return macro_score

    def _classify_drivers(self, scores: Dict[str, float], dominant: str) -> Tuple[List[str], List[str]]:
        """Classify drivers as agreeing or conflicting with the dominant driver."""
        dom_score = scores.get(dominant, 50)
        dom_bias = "bullish" if dom_score >= 55 else ("bearish" if dom_score <= 45 else "neutral")

        agreeing = []
        conflicting = []
        for driver, score in scores.items():
            if driver == dominant:
                agreeing.append(driver)
                continue
            bias = "bullish" if score >= 55 else ("bearish" if score <= 45 else "neutral")
            if dom_bias == "neutral":
                agreeing.append(driver)
            elif bias == dom_bias:
                agreeing.append(driver)
            elif bias == "neutral":
                agreeing.append(driver)
            else:
                conflicting.append(driver)

        return agreeing, conflicting

    # ------------------------------------------------------------------
    # Probability Engine
    # ------------------------------------------------------------------

    def compute_probabilities(
        self,
        macro_score: MacroScore,
        regime: MacroRegime,
        historical_analogue_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> MacroProbability:
        """Compute probability distribution over gold market outcomes.

        Uses deterministic rules based on:
        - Aggregate macro score
        - Regime classification
        - Driver agreement/conflict ratio
        - Confidence-weighted component scores
        """
        agg = macro_score.aggregate_score
        agreement_ratio = self._compute_agreement_ratio(macro_score)
        avg_confidence = self._compute_avg_confidence(macro_score)
        driver_count = macro_score.driver_count

        # Base probabilities from macro score
        if agg >= 75:
            p_long = 0.55 + (agg - 75) / 250  # 0.55-0.65 range
            p_short = 0.10
            p_range = 0.35 - (agg - 75) / 250
        elif agg >= 60:
            p_long = 0.45 + (agg - 60) / 150  # 0.45-0.55
            p_short = 0.15
            p_range = 0.40
        elif agg >= 40:
            p_long = 0.30
            p_short = 0.30
            p_range = 0.40
        elif agg >= 25:
            p_long = 0.15
            p_short = 0.45 + (40 - agg) / 150  # 0.45-0.55
            p_range = 0.40
        else:
            p_long = 0.10
            p_short = 0.55 + (25 - agg) / 250  # 0.55-0.65
            p_range = 0.35

        # Adjust for agreement ratio (higher agreement = more directional conviction)
        if agreement_ratio > 0.7:
            p_long += 0.05 if agg > 50 else -0.05
            p_short += 0.05 if agg < 50 else -0.05
            p_range -= 0.05

        # Adjust for confidence
        if avg_confidence < 0.4:
            p_range += 0.10
            p_long *= 0.9
            p_short *= 0.9

        # Volatility probability
        regime_vol_map = {
            "Crisis": 0.8, "Risk_Off": 0.6, "Stagflation": 0.55,
            "Fed_Pivot": 0.5, "Inflation_Scare": 0.45, "Goldilocks": 0.25,
            "Risk_On": 0.3, "Range_Bound": 0.2,
        }
        p_high_vol = regime_vol_map.get(regime.regime_name, 0.3)
        if agg > 80 or agg < 20:
            p_high_vol = min(0.9, p_high_vol + 0.15)

        # Breakout probability
        if agg >= 70 or agg <= 30:
            p_breakout = 0.35 + (abs(agg - 50) / 100) * 0.3  # 0.35-0.50
        elif driver_count >= 7 and agreement_ratio > 0.6:
            p_breakout = 0.30
        else:
            p_breakout = 0.20

        # Fakeout probability (higher when conflicting signals or extreme positioning)
        if agreement_ratio < 0.4:
            p_fakeout = 0.45
        elif agreement_ratio < 0.6:
            p_fakeout = 0.35
        else:
            p_fakeout = 0.20

        # Normalize directional probabilities to sum to 1.0
        total_dir = p_long + p_short + p_range
        p_long /= total_dir
        p_short /= total_dir
        p_range /= total_dir

        # Determine dominant bias
        bias = self._determine_bias(p_long, p_short, p_range)

        probability = MacroProbability(
            probability_long=round(p_long, 4),
            probability_short=round(p_short, 4),
            probability_range=round(p_range, 4),
            probability_high_volatility=round(min(1.0, p_high_vol), 4),
            probability_breakout=round(min(1.0, p_breakout), 4),
            probability_fakeout=round(min(1.0, p_fakeout), 4),
            historical_analogues=historical_analogue_ids or [],
            methodology="Weighted macro driver consensus with regime-based volatility adjustment",
            dominant_bias=bias,
            ontology_tags=ontology_tags,
        )
        self.repo.save(probability)
        self._audit("PROBABILITY_COMPUTED", probability.id, f"LONG={p_long:.2f}, SHORT={p_short:.2f}, Bias={bias}")
        return probability

    def _compute_agreement_ratio(self, macro_score: MacroScore) -> float:
        total = macro_score.driver_count or 1
        agreeing = len(macro_score.agreeing_drivers)
        return agreeing / total

    def _compute_avg_confidence(self, macro_score: MacroScore) -> float:
        confs = list(macro_score.component_confidences.values())
        if not confs:
            return 0.5
        return sum(confs) / len(confs)

    def _determine_bias(self, p_long: float, p_short: float, p_range: float) -> str:
        if p_long > 0.50:
            return "Long"
        elif p_short > 0.50:
            return "Short"
        elif p_long > 0.40 and p_long > p_short:
            return "Long_Bias"
        elif p_short > 0.40 and p_short > p_long:
            return "Short_Bias"
        else:
            return "Neutral"

    # ------------------------------------------------------------------
    # Macro Regime Classification
    # ------------------------------------------------------------------

    def classify_regime(
        self,
        macro_score: MacroScore,
        ontology_tags: Optional[List[str]] = None,
    ) -> MacroRegime:
        """Classify the current macro regime based on aggregate score and drivers."""
        agg = macro_score.aggregate_score
        primary = macro_score.dominant_driver

        # Find matching regime
        regime_name = "Range_Bound"
        description = "No dominant macro catalyst, gold ranging"
        for name, (low, high, _, desc) in sorted(REGIME_SCORE_MAP.items(),
                                                   key=lambda x: abs(x[1][0] + x[1][1]) / 2 - agg):
            if low <= agg <= high:
                if abs(low + high) / 2 - agg < 20:  # Closest match
                    regime_name = name
                    _, _, _, description = REGIME_SCORE_MAP[name]
                    break

        # Override if extreme scores
        if agg >= 85:
            regime_name = "Crisis"
            _, _, _, description = REGIME_SCORE_MAP["Crisis"]
        elif agg >= 70 and primary in (DRIVER_SAFE_HAVEN, DRIVER_CENTRAL_BANK):
            regime_name = "Risk_Off"
            _, _, _, description = REGIME_SCORE_MAP["Risk_Off"]

        # Determine stability
        conf = self._compute_avg_confidence(macro_score)
        if conf < 0.4:
            stability = "Uncertain"
        elif agg > 75 or agg < 25:
            stability = "Volatile"
        else:
            stability = "Stable" if macro_score.driver_count >= 7 else "Transitioning"

        secondary = [d for d in macro_score.agreeing_drivers if d != primary][:3]
        regime_score = agg

        regime = MacroRegime(
            regime_name=regime_name,
            regime_description=description,
            primary_driver=primary,
            secondary_drivers=secondary,
            stability=stability,
            score=regime_score,
            confidence=conf,
            ontology_tags=ontology_tags,
        )
        self.repo.save(regime)
        self._audit("REGIME_CLASSIFIED", regime.id, f"Regime={regime_name}, Primary={primary}")
        return regime

    # ------------------------------------------------------------------
    # Institutional Report Generation
    # ------------------------------------------------------------------

    def generate_report(
        self,
        macro_score: MacroScore,
        probabilities: MacroProbability,
        regime: MacroRegime,
        key_levels: Optional[Dict[str, float]] = None,
        report_format: str = "Institutional",
        ontology_tags: Optional[List[str]] = None,
    ) -> MacroReport:
        """Generate a complete institutional macro report for XAUUSD.

        Combines all analysis into a single report object with narrative,
        risk assessment, and actionable bias.
        """
        # Build dominant drivers list
        dominant_list = []
        for driver, score in sorted(macro_score.component_scores.items(),
                                     key=lambda x: x[1], reverse=True)[:5]:
            impact = self._classify_gold_impact(score)
            dominant_list.append({
                "driver": driver,
                "score": score,
                "confidence": macro_score.component_confidences.get(driver, 0.0),
                "impact": impact,
            })

        # Build conflicting drivers
        conflicting_list = []
        for driver in macro_score.conflicting_drivers:
            score = macro_score.component_scores.get(driver, 50)
            conflicting_list.append({
                "driver": driver,
                "score": score,
                "reason": f"Score {score:.0f} diverges from dominant driver {macro_score.dominant_driver}",
            })

        # Risk assessment
        risk_assessment = {
            "aggregate_score": macro_score.aggregate_score,
            "driver_agreement_ratio": round(self._compute_agreement_ratio(macro_score), 2),
            "average_confidence": round(self._compute_avg_confidence(macro_score), 2),
            "dominant_driver": macro_score.dominant_driver,
            "regime": regime.regime_name,
            "regime_stability": regime.stability,
            "fakeout_probability": probabilities.probability_fakeout,
            "high_volatility_probability": probabilities.probability_high_volatility,
        }

        # Generate narrative
        narrative = self._generate_narrative(macro_score, regime, probabilities)

        # Determine expected volatility
        if probabilities.probability_high_volatility >= 0.6:
            expected_vol = "High"
        elif probabilities.probability_high_volatility >= 0.4:
            expected_vol = "Elevated"
        elif probabilities.probability_high_volatility >= 0.25:
            expected_vol = "Moderate"
        else:
            expected_vol = "Low"

        # Determine suggested bias
        suggested_bias = probabilities.dominant_bias

        report = MacroReport(
            title=f"XAUUSD Macro Intelligence Report — {regime.regime_name} Regime",
            regime=regime.regime_name,
            dominant_drivers=dominant_list,
            conflicting_drivers=conflicting_list,
            macro_score_id=macro_score.id,
            probability_id=probabilities.id,
            narrative=narrative,
            risk_assessment=risk_assessment,
            expected_volatility=expected_vol,
            suggested_bias=suggested_bias,
            key_levels=key_levels or {},
            report_format=report_format,
            ontology_tags=ontology_tags,
        )
        self.repo.save(report)
        self._audit("REPORT_GENERATED", report.id, f"Bias={suggested_bias}, Vol={expected_vol}")
        return report

    def _generate_narrative(self, macro_score: MacroScore, regime: MacroRegime, probabilities: MacroProbability) -> str:
        """Generate a deterministic narrative based on current macro conditions."""
        parts = []
        agg = macro_score.aggregate_score

        opening = f"XAUUSD is in a {regime.regime_name} regime (score: {agg:.0f}/100)."
        parts.append(opening)

        if agg >= 70:
            parts.append("Macro conditions are strongly supportive of gold.")
        elif agg >= 55:
            parts.append("Macro conditions are moderately supportive of gold.")
        elif agg > 45:
            parts.append("Macro conditions are neutral for gold.")
        elif agg > 30:
            parts.append("Macro conditions are mildly headwind for gold.")
        else:
            parts.append("Macro conditions are strongly headwind for gold.")

        if macro_score.dominant_driver:
            dom_score = macro_score.component_scores.get(macro_score.dominant_driver, 50)
            parts.append(f"The dominant driver is {macro_score.dominant_driver} (score: {dom_score:.0f}).")

        if macro_score.agreeing_drivers:
            parts.append(f"Agreeing drivers: {', '.join(macro_score.agreeing_drivers[:4])}.")

        if macro_score.conflicting_drivers:
            parts.append(f"Conflicting signals from: {', '.join(macro_score.conflicting_drivers)}.")

        if regime.stability == "Volatile":
            parts.append("The regime is volatile — expect rapid shifts in macro conditions.")
        elif regime.stability == "Transitioning":
            parts.append("The regime appears to be transitioning — monitor for confirmation.")

        bias = probabilities.dominant_bias
        if bias == "Long":
            parts.append(f"The balance of evidence suggests a bullish bias (P(LONG)={probabilities.probability_long:.0%}).")
        elif bias == "Short":
            parts.append(f"The balance of evidence suggests a bearish bias (P(SHORT)={probabilities.probability_short:.0%}).")
        elif bias == "Neutral":
            parts.append("Evidence is evenly balanced — no directional bias is warranted.")

        if probabilities.probability_fakeout > 0.35:
            parts.append(f"Elevated fakeout probability ({probabilities.probability_fakeout:.0%}) — confirm before acting.")
        if probabilities.probability_high_volatility > 0.5:
            parts.append(f"High volatility expected ({probabilities.probability_high_volatility:.0%}) — size accordingly.")

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Convenience: Full analysis in one call
    # ------------------------------------------------------------------

    def full_analysis(
        self,
        real_yield_data: Dict[str, Any],
        dollar_data: Dict[str, Any],
        fed_data: Dict[str, Any],
        inflation_data: Dict[str, Any],
        labor_data: Dict[str, Any],
        growth_data: Dict[str, Any],
        safe_haven_data: Dict[str, Any],
        cb_data: Dict[str, Any],
        physical_data: Dict[str, Any],
        positioning_data: Dict[str, Any],
        key_levels: Optional[Dict[str, float]] = None,
        ontology_tags: Optional[List[str]] = None,
    ) -> MacroReport:
        """Run a full macro intelligence analysis in one call.

        Accepts data dicts for all 10 drivers, runs assessments,
        computes aggregate score, probabilities, and generates report.

        Returns:
            Complete MacroReport with all supporting objects persisted.
        """
        # Assess all 10 drivers
        self.assess_real_yields(**real_yield_data, ontology_tags=ontology_tags)
        self.assess_dollar(**dollar_data, ontology_tags=ontology_tags)
        self.assess_fed_policy(**fed_data, ontology_tags=ontology_tags)
        self.assess_inflation(**inflation_data, ontology_tags=ontology_tags)
        self.assess_labor_market(**labor_data, ontology_tags=ontology_tags)
        self.assess_economic_growth(**growth_data, ontology_tags=ontology_tags)
        self.assess_safe_haven(**safe_haven_data, ontology_tags=ontology_tags)
        self.assess_central_bank_demand(**cb_data, ontology_tags=ontology_tags)
        self.assess_physical_demand(**physical_data, ontology_tags=ontology_tags)
        self.assess_positioning(**positioning_data, ontology_tags=ontology_tags)

        # Compute aggregate
        macro_score = self.compute_macro_score(ontology_tags=ontology_tags)
        regime = self.classify_regime(macro_score, ontology_tags=ontology_tags)
        probabilities = self.compute_probabilities(macro_score, regime, ontology_tags=ontology_tags)

        # Generate report
        report = self.generate_report(
            macro_score=macro_score,
            probabilities=probabilities,
            regime=regime,
            key_levels=key_levels,
            ontology_tags=ontology_tags,
        )
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_latest_by_type(self, cls: type) -> Optional[BaseObject]:
        """Get the most recently saved object of a given type."""
        latest = None
        latest_ts = datetime.min.replace(tzinfo=timezone.utc)
        for obj in self.repo.get_all():
            if not isinstance(obj, cls):
                continue
            ts = getattr(obj, "timestamp", getattr(obj, "created_at", None))
            if ts and ts > latest_ts:
                latest = obj
                latest_ts = ts
        return latest

    def _audit(self, action: str, object_id: str, reason: str) -> None:
        """Record an audit entry for macro engine actions."""
        entry = AuditEntry(
            actor="macro_analysis_engine",
            action=action,
            object_id=object_id,
            object_type="MacroIntelligence",
        )
        self.repo.save(entry)
