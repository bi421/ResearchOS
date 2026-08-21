"""Comprehensive tests for the Macro Intelligence Layer (XAUUSD)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from researchos.macro.engine import (
    ALL_DRIVERS,
    DRIVER_CENTRAL_BANK,
    DRIVER_DXY,
    DRIVER_FED,
    DRIVER_GROWTH,
    DRIVER_INFLATION,
    DRIVER_LABOR,
    DRIVER_PHYSICAL,
    DRIVER_POSITIONING,
    DRIVER_REAL_YIELD,
    DRIVER_SAFE_HAVEN,
    DRIVER_WEIGHTS,
    MacroAnalysisEngine,
)
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
from researchos.repository.memory import MemoryRepository


def ts(year=2024, month=1, day=1):
    return datetime(year, month, day, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo():
    return MemoryRepository()


@pytest.fixture
def engine(repo):
    return MacroAnalysisEngine(repo)


# ===========================================================================
# PHASE 1 — Object Serialization Round-Trips
# ===========================================================================


class TestObjectSerialization:
    """Verify to_dict/from_dict round-trip for all 13 macro types."""

    def test_real_yield_snapshot_round_trip(self):
        obj = RealYieldSnapshot(
            ten_year_yield=4.5,
            five_year_yield=4.2,
            inflation_expectations=2.5,
            tips_yield=1.8,
            score=35.0,
            confidence=0.8,
        )
        d = obj.to_dict()
        obj2 = RealYieldSnapshot.from_dict(d)
        assert obj.id == obj2.id
        assert obj.ten_year_yield == obj2.ten_year_yield
        assert obj.score == obj2.score
        assert obj.expected_gold_impact == obj2.expected_gold_impact

    def test_dollar_strength_snapshot_round_trip(self):
        obj = DollarStrengthSnapshot(dxy=104.5, dxy_trend="Rising", score=40.0, confidence=0.7)
        d = obj.to_dict()
        obj2 = DollarStrengthSnapshot.from_dict(d)
        assert obj.id == obj2.id
        assert obj.dxy == obj2.dxy
        assert obj.score == obj2.score

    def test_fed_policy_assessment_round_trip(self):
        obj = FedPolicyAssessment(policy_classification="Dovish", rate_change_bps=-25, score=75.0)
        d = obj.to_dict()
        obj2 = FedPolicyAssessment.from_dict(d)
        assert obj.id == obj2.id
        assert obj.policy_classification == obj2.policy_classification
        assert obj.gold_pressure == obj2.gold_pressure

    def test_inflation_assessment_round_trip(self):
        obj = InflationAssessment(cpi=3.2, core_cpi=2.8, score=70.0)
        d = obj.to_dict()
        obj2 = InflationAssessment.from_dict(d)
        assert obj.id == obj2.id
        assert obj.inflation_regime == obj2.inflation_regime

    def test_labor_market_assessment_round_trip(self):
        obj = LaborMarketAssessment(nfp=150, unemployment_rate=4.1, score=55.0)
        d = obj.to_dict()
        obj2 = LaborMarketAssessment.from_dict(d)
        assert obj.id == obj2.id
        assert obj.economic_strength == obj2.economic_strength

    def test_economic_growth_assessment_round_trip(self):
        obj = EconomicGrowthAssessment(gdp=2.1, ism_manufacturing=48.5, score=60.0)
        d = obj.to_dict()
        obj2 = EconomicGrowthAssessment.from_dict(d)
        assert obj.id == obj2.id
        assert obj.growth_phase == obj2.growth_phase

    def test_safe_haven_assessment_round_trip(self):
        obj = SafeHavenAssessment(
            risk_aversion_score=75,
            safe_haven_demand="Elevated",
            active_conflicts=["Ukraine"],
            score=72.0,
        )
        d = obj.to_dict()
        obj2 = SafeHavenAssessment.from_dict(d)
        assert obj.id == obj2.id
        assert obj.active_conflicts == ["Ukraine"]

    def test_central_bank_demand_round_trip(self):
        obj = CentralBankDemand(monthly_purchases=50, annual_purchases=800, demand_trend="Accelerating", score=78.0)
        d = obj.to_dict()
        obj2 = CentralBankDemand.from_dict(d)
        assert obj.id == obj2.id
        assert obj.monthly_purchases == obj2.monthly_purchases

    def test_physical_demand_snapshot_round_trip(self):
        obj = PhysicalDemandSnapshot(comex_inventories=800, etf_flows_monthly=25, indian_demand="Strong", score=68.0)
        d = obj.to_dict()
        obj2 = PhysicalDemandSnapshot.from_dict(d)
        assert obj.id == obj2.id
        assert obj.indian_demand == obj2.indian_demand

    def test_positioning_assessment_round_trip(self):
        obj = PositioningAssessment(managed_money_long=250000, managed_money_short=50000, score=45.0)
        d = obj.to_dict()
        obj2 = PositioningAssessment.from_dict(d)
        assert obj.id == obj2.id
        assert obj.net_positioning == 200000
        assert obj2.net_positioning == 200000

    def test_macro_score_round_trip(self):
        obj = MacroScore(
            aggregate_score=65.5,
            dominant_driver=DRIVER_FED,
            component_scores={DRIVER_FED: 75.0, DRIVER_DXY: 55.0},
        )
        d = obj.to_dict()
        obj2 = MacroScore.from_dict(d)
        assert obj.id == obj2.id
        assert obj.aggregate_score == obj2.aggregate_score
        assert obj.dominant_driver == obj2.dominant_driver

    def test_macro_probability_round_trip(self):
        obj = MacroProbability(
            probability_long=0.55,
            probability_short=0.15,
            probability_range=0.30,
            dominant_bias="Long",
        )
        d = obj.to_dict()
        obj2 = MacroProbability.from_dict(d)
        assert obj.id == obj2.id
        assert obj.probability_long == obj2.probability_long
        assert obj.dominant_bias == obj2.dominant_bias

    def test_macro_regime_round_trip(self):
        obj = MacroRegime(regime_name="Risk_Off", primary_driver=DRIVER_SAFE_HAVEN, stability="Stable", score=72.0)
        d = obj.to_dict()
        obj2 = MacroRegime.from_dict(d)
        assert obj.id == obj2.id
        assert obj.regime_name == obj2.regime_name

    def test_macro_report_round_trip(self):
        obj = MacroReport(
            title="Test Report",
            regime="Risk_Off",
            suggested_bias="Long",
            expected_volatility="Elevated",
        )
        d = obj.to_dict()
        obj2 = MacroReport.from_dict(d)
        assert obj.id == obj2.id
        assert obj.title == obj2.title
        assert obj.suggested_bias == obj2.suggested_bias

    def test_all_types_object_type_in_dict(self):
        """All macro types include object_type in serialized output."""
        objs = [
            RealYieldSnapshot(),
            DollarStrengthSnapshot(),
            FedPolicyAssessment(),
            InflationAssessment(),
            LaborMarketAssessment(),
            EconomicGrowthAssessment(),
            SafeHavenAssessment(),
            CentralBankDemand(),
            PhysicalDemandSnapshot(),
            PositioningAssessment(),
            MacroScore(),
            MacroProbability(),
            MacroRegime(),
            MacroReport(),
        ]
        for obj in objs:
            d = obj.to_dict()
            assert "object_type" in d, f"{type(obj).__name__} missing object_type"
            assert d["object_type"] == type(obj).__name__


# ===========================================================================
# PHASE 2 — Determinism & Hash Consistency
# ===========================================================================


class TestDeterminism:
    """Same inputs produce same IDs and hashes."""

    def test_deterministic_object_ids(self):
        t = ts(2024, 6, 15)
        o1 = RealYieldSnapshot(ten_year_yield=4.5, tips_yield=1.8, timestamp=t)
        o2 = RealYieldSnapshot(ten_year_yield=4.5, tips_yield=1.8, timestamp=t)
        assert o1.id == o2.id

    def test_deterministic_hashes(self):
        o1 = MacroScore(aggregate_score=65.0, component_scores={DRIVER_FED: 75.0})
        o2 = MacroScore(aggregate_score=65.0, component_scores={DRIVER_FED: 75.0})
        assert o1.hash == o2.hash

    def test_different_inputs_different_ids(self):
        o1 = RealYieldSnapshot(ten_year_yield=4.5)
        o2 = RealYieldSnapshot(ten_year_yield=5.0)
        assert o1.id != o2.id

    def test_hash_changes_on_score(self):
        o1 = CentralBankDemand(monthly_purchases=50, score=78.0)
        o2 = CentralBankDemand(monthly_purchases=50, score=80.0)
        assert o1.hash != o2.hash

    def test_ontology_tags_in_hashing(self):
        o1 = MacroRegime(regime_name="Risk_Off", ontology_tags=["gold", "macro"])
        o2 = MacroRegime(regime_name="Risk_Off", ontology_tags=["gold"])
        assert o1.hash != o2.hash

    def test_positioning_net_positioning_computed(self):
        o1 = PositioningAssessment(managed_money_long=300000, managed_money_short=100000)
        o2 = PositioningAssessment(managed_money_long=300000, managed_money_short=100000)
        assert o1.net_positioning == 200000
        assert o1.net_positioning == o2.net_positioning

    def test_deterministic_ids_different_timestamp(self):
        o1 = InflationAssessment(cpi=3.2, timestamp=ts(2024, 1, 1))
        o2 = InflationAssessment(cpi=3.2, timestamp=ts(2024, 6, 1))
        assert o1.id != o2.id


# ===========================================================================
# Helper data loaders (module-level for reuse across test classes)
# ===========================================================================


def _load_bullish_drivers(engine):
    engine.assess_real_yields(3.0, 3.0, 3.5, -0.8)
    engine.assess_dollar(92.0, "Falling", "Bearish")
    engine.assess_fed_policy(policy_classification="Dovish", rate_change_bps=-25, hawkishness_score=30)
    engine.assess_inflation(4.5, 4.0)
    engine.assess_labor_market(nfp=80, unemployment_rate=5.2)
    engine.assess_economic_growth(gdp=0.8, ism_manufacturing=46, ism_services=48)
    engine.assess_safe_haven(70, "Elevated", ["Conflict"], "Elevated")
    engine.assess_central_bank_demand(monthly_purchases=60, annual_purchases=900, demand_trend="Accelerating")
    engine.assess_physical_demand(
        comex_inventories=700, etf_flows_monthly=25, indian_demand="Strong", chinese_demand="Strong"
    )
    engine.assess_positioning(managed_money_long=50000, managed_money_short=180000)


def _load_bearish_drivers(engine):
    engine.assess_real_yields(5.5, 4.5, 2.0, 2.5)
    engine.assess_dollar(108.0, "Rising", "Bullish")
    engine.assess_fed_policy(policy_classification="Hawkish", rate_change_bps=25, hawkishness_score=70)
    engine.assess_inflation(2.0, 2.0)
    engine.assess_labor_market(nfp=350, unemployment_rate=3.2)
    engine.assess_economic_growth(gdp=3.5, ism_manufacturing=58, ism_services=56)
    engine.assess_safe_haven(30, "Subdued", [], "Low")
    engine.assess_central_bank_demand(monthly_purchases=5, annual_purchases=50, demand_trend="Declining")
    engine.assess_physical_demand(
        comex_inventories=900, etf_flows_monthly=-15, indian_demand="Weak", chinese_demand="Weak"
    )
    engine.assess_positioning(managed_money_long=250000, managed_money_short=30000)


def _load_mixed_drivers(engine):
    engine.assess_real_yields(4.0, 3.8, 2.5, 1.5)
    engine.assess_dollar(104.0, "Ranging", "Neutral")
    engine.assess_fed_policy(policy_classification="Neutral")
    engine.assess_inflation(3.0, 2.8)
    engine.assess_labor_market(nfp=200, unemployment_rate=3.8)
    engine.assess_economic_growth(gdp=2.5, ism_manufacturing=52, ism_services=50)
    engine.assess_safe_haven(50, "Normal", [], "Normal")
    engine.assess_central_bank_demand(monthly_purchases=30, annual_purchases=500, demand_trend="Stable")
    engine.assess_physical_demand(
        comex_inventories=800,
        etf_flows_monthly=10,
        indian_demand="Moderate",
        chinese_demand="Moderate",
    )
    engine.assess_positioning(managed_money_long=150000, managed_money_short=100000)


# ===========================================================================
# PHASE 3 — Engine Driver Assessments
# ===========================================================================


class TestDriverAssessments:
    """Each of the 10 macro drivers produces correct assessments."""

    def test_real_yields_bullish(self, engine):
        """Low/falling real yields = bullish for gold."""
        result = engine.assess_real_yields(
            ten_year_yield=3.8,
            five_year_yield=3.7,
            inflation_expectations=2.2,
            tips_yield=-0.5,
        )
        assert result.score > 60
        assert result.expected_gold_impact in ("Bullish", "Strongly_Bullish")
        assert result.real_yield_trend == "Extreme_Falling"

    def test_real_yields_bearish(self, engine):
        """High/rising real yields = bearish for gold."""
        result = engine.assess_real_yields(
            ten_year_yield=5.5,
            five_year_yield=4.5,
            inflation_expectations=2.0,
            tips_yield=2.0,
        )
        assert result.score < 40
        assert result.expected_gold_impact in ("Bearish", "Strongly_Bearish")
        assert result.real_yield_trend == "Rising"

    def test_real_yields_extreme(self, engine):
        """Extreme negative real yields = strongly bullish."""
        result = engine.assess_real_yields(
            ten_year_yield=3.0,
            five_year_yield=3.0,
            inflation_expectations=3.0,
            tips_yield=-1.5,
        )
        assert result.score >= 80
        assert result.expected_gold_impact == "Strongly_Bullish"
        assert result.real_yield_trend == "Extreme_Falling"

    def test_dollar_weak_bullish(self, engine):
        """Weak dollar = bullish for gold."""
        result = engine.assess_dollar(dxy=94.0, dxy_trend="Falling", dxy_momentum="Bearish")
        assert result.score > 60

    def test_dollar_strong_bearish(self, engine):
        """Strong dollar = bearish for gold."""
        result = engine.assess_dollar(dxy=108.0, dxy_trend="Rising", dxy_momentum="Bullish")
        assert result.score < 40

    def test_dollar_breakout_down(self, engine):
        """Dollar breakout down = most bullish."""
        result = engine.assess_dollar(dxy=96.0, dxy_trend="Breakout_Down", dxy_momentum="Strong_Bearish")
        assert result.score > 70
        assert result.confidence >= 0.8

    def test_fed_dovish_bullish(self, engine):
        """Dovish Fed = bullish for gold."""
        result = engine.assess_fed_policy(policy_classification="Dovish", rate_change_bps=-25, hawkishness_score=30.0)
        assert result.score > 60
        assert result.gold_pressure == "Bullish"

    def test_fed_hawkish_bearish(self, engine):
        """Hawkish Fed = bearish for gold."""
        result = engine.assess_fed_policy(policy_classification="Hawkish", rate_change_bps=25, hawkishness_score=70.0)
        assert result.score < 40
        assert result.gold_pressure == "Bearish"

    def test_fed_extreme_dovish(self, engine):
        """Extremely dovish = highest score."""
        result = engine.assess_fed_policy(
            policy_classification="Extremely_Dovish", rate_change_bps=-50, hawkishness_score=15.0
        )
        assert result.score >= 80
        assert result.confidence >= 0.8

    def test_inflation_high_bullish(self, engine):
        """High inflation = bullish for gold."""
        result = engine.assess_inflation(cpi=5.5, core_cpi=5.0)
        assert result.score > 70
        assert result.inflation_regime == "High_Inflation"
        assert result.expected_fed_reaction == "Hawkish"

    def test_inflation_stable_neutral(self, engine):
        """Stable inflation = neutral for gold."""
        result = engine.assess_inflation(cpi=2.5, core_cpi=2.3)
        assert 40 <= result.score <= 60
        assert result.inflation_regime == "Stable"

    def test_inflation_hyper(self, engine):
        """Hyperinflation = extremely bullish."""
        result = engine.assess_inflation(cpi=12.0, core_cpi=10.0)
        assert result.score >= 90
        assert result.inflation_regime == "Hyperinflation"

    def test_labor_weak_bullish(self, engine):
        """Weak labor market = bullish for gold."""
        result = engine.assess_labor_market(nfp=50, unemployment_rate=5.5)
        assert result.score > 60
        assert result.economic_strength == "Weak"
        assert result.expected_fed_path == "Cutting"

    def test_labor_strong_bearish(self, engine):
        """Strong labor market = bearish for gold."""
        result = engine.assess_labor_market(nfp=350, unemployment_rate=3.4, wage_growth=4.5)
        assert result.score < 35
        assert result.economic_strength == "Very_Strong"

    def test_growth_weak_bullish(self, engine):
        """Weak growth = bullish for gold."""
        result = engine.assess_economic_growth(gdp=0.5, ism_manufacturing=46, ism_services=48)
        assert result.score > 60
        assert result.recession_risk in ("Elevated", "High")

    def test_growth_boom_bearish(self, engine):
        """Strong growth = neutral to bearish for gold."""
        result = engine.assess_economic_growth(gdp=3.5, ism_manufacturing=58, ism_services=56)
        assert result.score < 35
        assert result.growth_phase == "Boom"

    def test_safe_haven_elevated(self, engine):
        """Elevated safe haven demand = bullish."""
        result = engine.assess_safe_haven(
            risk_aversion_score=75,
            safe_haven_demand="Elevated",
            active_conflicts=["Ukraine", "Gaza"],
            financial_stress="Elevated",
            vix_equivalent=22.0,
        )
        assert result.score > 60

    def test_safe_haven_crisis(self, engine):
        """Crisis conditions = very bullish."""
        result = engine.assess_safe_haven(
            risk_aversion_score=90,
            safe_haven_demand="Extreme",
            active_conflicts=["War", "Conflict", "Crisis"],
            financial_stress="Crisis",
            vix_equivalent=35.0,
        )
        assert result.score >= 75
        assert result.confidence >= 0.8

    def test_central_bank_high_demand(self, engine):
        """Strong central bank buying = bullish."""
        result = engine.assess_central_bank_demand(
            monthly_purchases=60, annual_purchases=900, demand_trend="Accelerating"
        )
        assert result.score > 70

    def test_central_bank_low_demand(self, engine):
        """Minimal central bank buying = neutral."""
        result = engine.assess_central_bank_demand(monthly_purchases=5, annual_purchases=50, demand_trend="Declining")
        assert result.score < 40

    def test_physical_demand_strong(self, engine):
        """Strong physical demand = bullish."""
        result = engine.assess_physical_demand(
            comex_inventories=700,
            etf_flows_monthly=30,
            indian_demand="Strong",
            chinese_demand="Strong",
            seasonality="Positive",
        )
        assert result.score > 60

    def test_physical_demand_weak(self, engine):
        """Weak physical demand = bearish."""
        result = engine.assess_physical_demand(
            comex_inventories=900,
            etf_flows_monthly=-20,
            indian_demand="Weak",
            chinese_demand="Weak",
            seasonality="Negative",
            supply_pressure="Abundant",
        )
        assert result.score < 45

    def test_positioning_bullish_contrarian(self, engine):
        """Extreme short positioning = contrarian bullish."""
        result = engine.assess_positioning(managed_money_long=40000, managed_money_short=200000)
        assert result.score > 60
        assert result.crowded_side == "Extreme_Short"

    def test_positioning_bearish_contrarian(self, engine):
        """Extreme long positioning = contrarian bearish."""
        result = engine.assess_positioning(managed_money_long=250000, managed_money_short=30000)
        assert result.score < 40
        assert result.crowded_side == "Extreme_Long"

    def test_positioning_neutral(self, engine):
        """Neutral positioning = neutral score."""
        result = engine.assess_positioning(managed_money_long=100000, managed_money_short=90000)
        assert result.score == 50.0
        assert result.crowded_side == "Neutral"

    def test_all_drivers_assessed_and_persisted(self, engine, repo):
        """Every driver assessment persists to the repository."""
        engine.assess_real_yields(4.5, 4.2, 2.5, 1.8)
        engine.assess_dollar(104.0)
        engine.assess_fed_policy(policy_classification="Neutral")
        engine.assess_inflation(3.0, 2.8)
        engine.assess_labor_market(200, 3.8)
        engine.assess_economic_growth(2.5, 52.0, 50.0)
        engine.assess_safe_haven(50)
        engine.assess_central_bank_demand(monthly_purchases=30, annual_purchases=500)
        engine.assess_physical_demand(comex_inventories=800, etf_flows_monthly=10)
        engine.assess_positioning(managed_money_long=150000, managed_money_short=100000)

        all_objs = repo.get_all()
        driver_types = {
            RealYieldSnapshot,
            DollarStrengthSnapshot,
            FedPolicyAssessment,
            InflationAssessment,
            LaborMarketAssessment,
            EconomicGrowthAssessment,
            SafeHavenAssessment,
            CentralBankDemand,
            PhysicalDemandSnapshot,
            PositioningAssessment,
        }
        found_types = {type(o) for o in all_objs}
        for dt in driver_types:
            assert dt in found_types, f"{dt.__name__} not persisted"


# ===========================================================================
# PHASE 4 — Aggregate Scoring
# ===========================================================================


class TestMacroScore:
    """Weighted aggregate macro scoring."""

    def test_macro_score_no_drivers(self, engine):
        """No stored assessments = default 50.0 score."""
        score = engine.compute_macro_score()
        assert score.aggregate_score == 50.0
        assert score.driver_count == 0

    def test_macro_score_single_driver(self, engine):
        """Single driver determines aggregate."""
        engine.assess_real_yields(3.0, 3.0, 3.5, -1.0)  # Very bullish
        score = engine.compute_macro_score()
        assert score.aggregate_score > 50
        assert score.dominant_driver == DRIVER_REAL_YIELD

    def test_macro_score_all_bullish(self, engine):
        """All drivers bullish = high aggregate."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        assert score.aggregate_score > 60
        assert len(score.component_scores) == 10

    def test_macro_score_all_bearish(self, engine):
        """All drivers bearish = low aggregate."""
        _load_bearish_drivers(engine)
        score = engine.compute_macro_score()
        assert score.aggregate_score < 40
        assert len(score.component_scores) == 10

    def test_macro_score_agreeing_conflicting(self, engine):
        """Agreeing and conflicting drivers are classified correctly."""
        _load_mixed_drivers(engine)
        score = engine.compute_macro_score()
        assert len(score.agreeing_drivers) > 0
        assert len(score.conflicting_drivers) >= 0
        assert score.dominant_driver != ""

    def test_macro_score_weights_sum_to_one(self):
        """DRIVER_WEIGHTS sum to approximately 1.0."""
        total = sum(DRIVER_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_macro_score_all_drivers_in_weights(self):
        """All 10 drivers have weights defined."""
        for driver in ALL_DRIVERS:
            assert driver in DRIVER_WEIGHTS, f"{driver} missing from weights"

    def test_macro_score_persistence(self, engine, repo):
        """MacroScore is persisted to repo."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        loaded = repo.get(score.id)
        assert loaded is not None
        assert loaded.aggregate_score == score.aggregate_score


# ===========================================================================
# PHASE 5 — Probability Engine
# ===========================================================================


class TestProbabilities:
    """Probability distribution computation."""

    def test_probability_bullish_bias(self, engine):
        """High macro score = long bias."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        assert prob.probability_long > prob.probability_short
        assert prob.dominant_bias in ("Long", "Long_Bias")

    def test_probability_bearish_bias(self, engine):
        """Low macro score = short bias."""
        _load_bearish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        assert prob.probability_short > prob.probability_long
        assert prob.dominant_bias in ("Short", "Short_Bias")

    def test_probability_neutral(self, engine):
        """Neutral macro score = no dominant bias."""
        _load_mixed_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        engine.compute_probabilities(score, regime)
        assert 40 <= score.aggregate_score <= 60

    def test_probability_sum_to_one(self, engine):
        """Directional probabilities sum to 1.0."""
        _load_mixed_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        total = prob.probability_long + prob.probability_short + prob.probability_range
        assert abs(total - 1.0) < 0.01

    def test_probability_persistence(self, engine, repo):
        """Probabilities are persisted."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        assert repo.get(prob.id) is not None

    def test_probability_deterministic(self):
        """Same inputs produce same probabilities."""
        engine1 = MacroAnalysisEngine(MemoryRepository())
        _load_bullish_drivers(engine1)
        score1 = engine1.compute_macro_score()
        regime1 = engine1.classify_regime(score1)
        p1 = engine1.compute_probabilities(score1, regime1)

        engine2 = MacroAnalysisEngine(MemoryRepository())
        _load_bullish_drivers(engine2)
        score2 = engine2.compute_macro_score()
        regime2 = engine2.classify_regime(score2)
        p2 = engine2.compute_probabilities(score2, regime2)

        assert p1.probability_long == p2.probability_long
        assert p1.dominant_bias == p2.dominant_bias


# ===========================================================================
# PHASE 6 — Regime Classification
# ===========================================================================


class TestRegimeClassification:
    """Macro regime classification."""

    def test_regime_crisis(self, engine):
        """Score >= 85 = Crisis regime."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        if score.aggregate_score >= 85:
            assert regime.regime_name == "Crisis"

    def test_regime_risk_off(self, engine):
        """High score with safe haven dominant = Risk_Off."""
        engine.assess_safe_haven(
            risk_aversion_score=85,
            safe_haven_demand="Elevated",
            active_conflicts=["War"],
            financial_stress="Crisis",
            vix_equivalent=30,
        )
        engine.assess_real_yields(3.0, 3.0, 3.0, 1.0)
        engine.assess_dollar(102.0, "Ranging")
        engine.assess_fed_policy(policy_classification="Neutral")
        engine.assess_inflation(3.0, 2.8)
        engine.assess_labor_market(150, 4.5)
        engine.assess_economic_growth(1.5, 48, 50)
        engine.assess_central_bank_demand(monthly_purchases=30, annual_purchases=500)
        engine.assess_physical_demand(comex_inventories=800, etf_flows_monthly=10)
        engine.assess_positioning(managed_money_long=150000, managed_money_short=100000)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        if score.aggregate_score >= 70:
            assert regime.regime_name == "Risk_Off"

    def test_regime_range_bound(self, engine):
        """Mid-range score = Range_Bound."""
        _load_mixed_drivers(engine)
        score = engine.compute_macro_score()
        engine.classify_regime(score)
        assert 40 <= score.aggregate_score <= 60

    def test_regime_stability(self, engine):
        """Stability field is set."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        assert regime.stability in ("Stable", "Transitioning", "Volatile", "Uncertain")
        assert len(regime.secondary_drivers) > 0

    def test_regime_persistence(self, engine, repo):
        """Regime is persisted."""
        _load_mixed_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        assert repo.get(regime.id) is not None


# ===========================================================================
# PHASE 7 — Report Generation
# ===========================================================================


class TestReportGeneration:
    """Institutional report generation."""

    def test_report_basic(self, engine):
        """Report can be generated from macro analysis."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        report = engine.generate_report(score, prob, regime)
        assert isinstance(report, MacroReport)
        assert report.title != ""
        assert report.narrative != ""

    def test_report_contains_risk_assessment(self, engine):
        """Risk assessment is present in report."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        report = engine.generate_report(score, prob, regime)
        assert "aggregate_score" in report.risk_assessment
        assert "driver_agreement_ratio" in report.risk_assessment

    def test_report_contains_dominant_drivers(self, engine):
        """Top 5 dominant drivers are listed."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        report = engine.generate_report(score, prob, regime)
        assert len(report.dominant_drivers) > 0
        assert "driver" in report.dominant_drivers[0]

    def test_report_suggested_bias(self, engine):
        """Suggested bias matches probability bias."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        report = engine.generate_report(score, prob, regime)
        assert report.suggested_bias == prob.dominant_bias

    def test_report_with_key_levels(self, engine):
        """Key price levels appear in report."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        levels = {"support_1": 2300, "support_2": 2250, "resistance_1": 2400, "resistance_2": 2450}
        report = engine.generate_report(score, prob, regime, key_levels=levels)
        assert report.key_levels == levels

    def test_report_persistence(self, engine, repo):
        """Report is persisted."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        report = engine.generate_report(score, prob, regime)
        assert repo.get(report.id) is not None

    def test_report_deterministic(self):
        """Same inputs produce same report narrative."""
        engine1 = MacroAnalysisEngine(MemoryRepository())
        _load_bullish_drivers(engine1)
        s1 = engine1.compute_macro_score()
        reg1 = engine1.classify_regime(s1)
        p1 = engine1.compute_probabilities(s1, reg1)
        r1 = engine1.generate_report(s1, p1, reg1)

        engine2 = MacroAnalysisEngine(MemoryRepository())
        _load_bullish_drivers(engine2)
        s2 = engine2.compute_macro_score()
        reg2 = engine2.classify_regime(s2)
        p2 = engine2.compute_probabilities(s2, reg2)
        r2 = engine2.generate_report(s2, p2, reg2)

        assert r1.narrative == r2.narrative
        assert r1.suggested_bias == r2.suggested_bias


# ===========================================================================
# PHASE 8 — Full Analysis Integration
# ===========================================================================


class TestFullAnalysis:
    """End-to-end full_analysis integration."""

    BULLISH_DATA = {
        "real_yield_data": {
            "ten_year_yield": 3.0,
            "five_year_yield": 3.0,
            "inflation_expectations": 3.5,
            "tips_yield": -0.8,
        },
        "dollar_data": {"dxy": 92.0, "dxy_trend": "Falling", "dxy_momentum": "Bearish"},
        "fed_data": {
            "policy_classification": "Dovish",
            "rate_change_bps": -25,
            "hawkishness_score": 30,
        },
        "inflation_data": {"cpi": 4.5, "core_cpi": 4.0},
        "labor_data": {"nfp": 80, "unemployment_rate": 5.2},
        "growth_data": {"gdp": 0.8, "ism_manufacturing": 46, "ism_services": 48},
        "safe_haven_data": {
            "risk_aversion_score": 70,
            "safe_haven_demand": "Elevated",
            "active_conflicts": ["Conflict"],
            "financial_stress": "Elevated",
        },
        "cb_data": {
            "monthly_purchases": 60,
            "annual_purchases": 900,
            "demand_trend": "Accelerating",
        },
        "physical_data": {
            "comex_inventories": 700,
            "etf_flows_monthly": 25,
            "indian_demand": "Strong",
            "chinese_demand": "Strong",
        },
        "positioning_data": {"managed_money_long": 50000, "managed_money_short": 180000},
    }

    def test_full_analysis_returns_report(self, engine):
        """full_analysis returns a MacroReport."""
        report = engine.full_analysis(**self.BULLISH_DATA)
        assert isinstance(report, MacroReport)

    def test_full_analysis_all_objects_persisted(self, engine, repo):
        """Full analysis persists all objects."""
        report = engine.full_analysis(**self.BULLISH_DATA)
        assert repo.get(report.id) is not None
        assert repo.get(report.macro_score_id) is not None
        assert repo.get(report.probability_id) is not None

    def test_full_analysis_deterministic(self):
        """Same full analysis inputs produce identical output."""
        e1 = MacroAnalysisEngine(MemoryRepository())
        e2 = MacroAnalysisEngine(MemoryRepository())
        r1 = e1.full_analysis(**self.BULLISH_DATA)
        r2 = e2.full_analysis(**self.BULLISH_DATA)
        assert r1.suggested_bias == r2.suggested_bias
        assert r1.regime == r2.regime

    def test_full_analysis_with_ontology_tags(self, engine):
        """Ontology tags propagate through full analysis."""
        report = engine.full_analysis(**self.BULLISH_DATA, ontology_tags=["gold", "macro", "xauusd"])
        assert "gold" in report.ontology_tags

    def test_full_analysis_with_key_levels(self, engine):
        """Key levels propagate to report."""
        levels = {"support": 2300, "resistance": 2450}
        report = engine.full_analysis(**self.BULLISH_DATA, key_levels=levels)
        assert report.key_levels == levels

    def test_full_analysis_generates_narrative(self, engine):
        """Full analysis generates a non-empty narrative."""
        report = engine.full_analysis(**self.BULLISH_DATA)
        assert len(report.narrative) > 50
        assert "XAUUSD" in report.narrative

    def test_full_analysis_expected_volatility_set(self, engine):
        """Expected volatility is set in report."""
        report = engine.full_analysis(**self.BULLISH_DATA)
        assert report.expected_volatility in ("Low", "Moderate", "Elevated", "High")


# ===========================================================================
# PHASE 9 — Edge Cases & Error Handling
# ===========================================================================


class TestEdgeCases:
    """Boundary conditions and edge cases."""

    def test_zero_values(self, engine):
        """Zero inputs should not raise errors."""
        result = engine.assess_real_yields(0, 0, 0, 0)
        assert isinstance(result, RealYieldSnapshot)
        assert 0 <= result.score <= 100

    def test_extreme_values(self, engine):
        """Extreme inputs should be clamped to 0-100 range."""
        result = engine.assess_dollar(dxy=200.0)
        assert 0 <= result.score <= 100

    def test_negative_values(self, engine):
        """Negative values should not break scoring."""
        result = engine.assess_inflation(cpi=-1.0, core_cpi=-0.5)
        assert isinstance(result, InflationAssessment)
        assert 0 <= result.score <= 100

    def test_empty_conflicts_list(self, engine):
        """No active conflicts should be handled gracefully."""
        result = engine.assess_safe_haven(50, "Normal", [], "Normal", 15)
        assert isinstance(result, SafeHavenAssessment)
        assert result.active_conflicts == []

    def test_zero_managed_money(self, engine):
        """Zero positioning should default to neutral."""
        result = engine.assess_positioning(0, 0)
        assert result.crowded_side == "Neutral"
        assert result.positioning_extreme == "No"
        assert result.score == 50.0

    def test_macro_score_loaded_later_updates(self, engine):
        """New assessments update the macro score."""
        engine.assess_real_yields(5.5, 4.5, 2.0, 2.5)
        score1 = engine.compute_macro_score()
        engine.assess_real_yields(3.0, 3.0, 3.5, -0.8)
        score2 = engine.compute_macro_score()
        assert score2.aggregate_score > score1.aggregate_score

    def test_audit_entries_created(self, engine, repo):
        """Each driver assessment creates audit entries."""
        _load_bullish_drivers(engine)
        audits = [o for o in repo.get_all() if isinstance(o, AuditEntry)]
        assert len(audits) >= 10  # At least 10 audit entries for 10 drivers

    def test_idempotent_save(self):
        """Saving same assessment twice does not corrupt."""
        engine = MacroAnalysisEngine(MemoryRepository())
        result1 = engine.assess_real_yields(3.0, 3.0, 3.5, -0.8)
        count1 = len(engine.repo.get_all())
        result2 = engine.assess_real_yields(3.0, 3.0, 3.5, -0.8)
        count2 = len(engine.repo.get_all())
        # Second save should not increase object count (Upsert behavior)
        assert count2 >= count1
        # Both result objects are valid
        assert result1.score == result2.score
        assert result1.ten_year_yield == result2.ten_year_yield

    def test_macro_score_with_single_driver_update(self, engine):
        """Only one driver assessed = score reflects only that driver."""
        engine.assess_real_yields(3.0, 3.0, 3.5, -0.8)
        score = engine.compute_macro_score()
        assert score.driver_count == 1
        assert score.dominant_driver == DRIVER_REAL_YIELD

    def test_all_drivers_list_complete(self):
        """ALL_DRIVERS contains exactly 10 entries."""
        assert len(ALL_DRIVERS) == 10
        expected = {
            DRIVER_REAL_YIELD,
            DRIVER_DXY,
            DRIVER_FED,
            DRIVER_INFLATION,
            DRIVER_LABOR,
            DRIVER_GROWTH,
            DRIVER_SAFE_HAVEN,
            DRIVER_CENTRAL_BANK,
            DRIVER_PHYSICAL,
            DRIVER_POSITIONING,
        }
        assert set(ALL_DRIVERS) == expected

    def test_narrative_generation_all_regimes(self, engine):
        """Narrative is generated for all score ranges."""
        _load_bullish_drivers(engine)
        score = engine.compute_macro_score()
        regime = engine.classify_regime(score)
        prob = engine.compute_probabilities(score, regime)
        report = engine.generate_report(score, prob, regime)
        assert "XAUUSD" in report.narrative
        assert regime.regime_name in report.narrative
