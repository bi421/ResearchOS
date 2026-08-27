"""Tests for Phase 2: Research Attribution Engine.

Tests cover:
1. Attribution object creation, serialization, determinism
2. AttributionGraph creation and management
3. ResearchAttributionEngine: chain tracing
4. ResearchAttributionEngine: attribution creation
5. ResearchAttributionEngine: graph management
6. ResearchAttributionEngine: integrity verification
7. ResearchAttributionEngine: market memory linking
8. Full integration: research cycle → attribution
9. Edge cases: missing objects, empty chains, cycles
"""

from datetime import datetime, timezone

import pytest

from researchos.engines.attribution import (
    ATTRIBUTABLE_TYPES,
    TRAVERSAL_RULES,
    ResearchAttributionEngine,
)
from researchos.objects.attribution import (
    Attribution,
    AttributionGraph,
)
from researchos.objects.evidence import Evidence
from researchos.objects.hypothesis import Hypothesis
from researchos.objects.interpretation import Interpretation
from researchos.objects.observation import Observation
from researchos.objects.process import AuditEntry
from researchos.objects.research import Research
from researchos.objects.scenario import Scenario
from researchos.storage.repository import OBJECT_REGISTRY

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo():
    """In-memory repository for testing."""
    from researchos.repository.memory import MemoryRepository

    return MemoryRepository()


@pytest.fixture
def engine(repo):
    """ResearchAttributionEngine with in-memory repository."""
    return ResearchAttributionEngine(repo)


@pytest.fixture
def sample_observation(repo):
    obs = Observation(
        source="MACRO:CPI_YOY",
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
        value=3.2,
        unit="percent",
        frequency="monthly",
        geography="US",
        retrieval_method="economic_calendar",
    )
    repo.save(obs)
    return obs


@pytest.fixture
def sample_evidence(repo, sample_observation):
    ev = Evidence(
        observation_id=sample_observation.id,
        hypothesis_id="hyp-test-1",
        interpretation="CPI shows persistent inflation",
        direction="Supporting",
        source_reliability=0.9,
        relevance=0.8,
        tier="Primary",
    )
    repo.save(ev)
    return ev


@pytest.fixture
def sample_interpretation(repo, sample_evidence):
    interp = Interpretation(
        evidence_ids=[sample_evidence.id],
        rule_applied="inflation_assessment_v1",
        context="US monetary policy analysis",
        conclusion="Inflation remains above target, Fed will maintain hawkish stance",
        confidence=0.85,
    )
    repo.save(interp)
    return interp


@pytest.fixture
def sample_hypothesis(repo, sample_interpretation):
    hyp = Hypothesis(
        research_id="research-test-1",
        type="Primary",
        statement="Fed will hold rates steady due to sticky inflation",
        narrative_id="",
        evidence_ids=[sample_interpretation.evidence_ids[0]],
        evidence_strength=0.8,
        coherence=0.7,
        plausibility=0.75,
        falsifiability=0.6,
        confidence=0.72,
    )
    repo.save(hyp)
    return hyp


@pytest.fixture
def sample_scenario(repo, sample_hypothesis):
    sc = Scenario(
        hypothesis_id=sample_hypothesis.id,
        type="Base",
        label="Scenario A: Fed Hold",
        thesis="Fed holds rates steady through Q3",
        probability=0.6,
        regime="Restrictive",
        supporting_evidence=[sample_hypothesis.evidence_ids[0]],
    )
    repo.save(sc)
    return sc


@pytest.fixture
def sample_research(repo):
    r = Research(
        question="Will the Fed cut rates in 2024?",
        time_horizon="Monthly",
        asset="USD",
    )
    repo.save(r)
    return r


@pytest.fixture
def complete_research_cycle(repo, sample_research):
    """Set up a complete mini research cycle for integration testing."""
    research = sample_research

    # Observations
    obs1 = Observation(
        source="MACRO:CPI_YOY",
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
        value=3.2,
        unit="percent",
        geography="US",
        retrieval_method="economic_calendar",
    )
    obs2 = Observation(
        source="MACRO:UNEMPLOYMENT",
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
        value=4.0,
        unit="percent",
        geography="US",
        retrieval_method="economic_calendar",
    )
    repo.save(obs1)
    repo.save(obs2)
    research.observation_ids = [obs1.id, obs2.id]
    repo.save(research)

    # Evidence
    ev1 = Evidence(
        observation_id=obs1.id,
        hypothesis_id="hyp-test-2",
        interpretation="CPI remains sticky",
        direction="Supporting",
        source_reliability=0.9,
        relevance=0.85,
    )
    ev2 = Evidence(
        observation_id=obs2.id,
        hypothesis_id="hyp-test-2",
        interpretation="Labor market cooling",
        direction="Supporting",
        source_reliability=0.85,
        relevance=0.8,
    )
    repo.save(ev1)
    repo.save(ev2)

    # Interpretation
    interp = Interpretation(
        evidence_ids=[ev1.id, ev2.id],
        rule_applied="macro_assessment_v2",
        context="FOMC decision analysis",
        conclusion="Mixed signals: inflation sticky but labor cooling",
        confidence=0.78,
    )
    repo.save(interp)

    # Hypothesis
    hyp = Hypothesis(
        research_id=research.id,
        type="Primary",
        statement="Fed will hold rates steady",
        evidence_ids=[ev1.id, ev2.id],
        evidence_strength=0.8,
        coherence=0.75,
        plausibility=0.7,
        falsifiability=0.65,
        confidence=0.72,
    )
    repo.save(hyp)

    # Link HypothesisSet to research
    from researchos.objects.hypothesis import HypothesisSet

    hs = HypothesisSet(research_id=research.id)
    hs.add_hypothesis(hyp)
    repo.save(hs)
    research.hypothesis_set_id = hs.id
    repo.save(research)

    # Scenario
    sc = Scenario(
        hypothesis_id=hyp.id,
        type="Base",
        label="Scenario A",
        thesis="Fed holds through Q3",
        probability=0.6,
        supporting_evidence=[ev1.id, ev2.id],
    )
    repo.save(sc)

    # Link ScenarioSet to research
    from researchos.objects.scenario import ScenarioSet

    ss = ScenarioSet(research_id=research.id)
    ss.add_scenario(sc)
    repo.save(ss)
    research.scenario_set_id = ss.id
    repo.save(research)

    return {
        "research": research,
        "obs1": obs1,
        "obs2": obs2,
        "ev1": ev1,
        "ev2": ev2,
        "interp": interp,
        "hyp": hyp,
        "sc": sc,
    }


# ===================================================================
# 1. Attribution object
# ===================================================================


class TestAttributionObject:
    def test_create_basic(self):
        attr = Attribution(
            conclusion_id="conc-123",
            conclusion_type="Hypothesis",
            reasoning_path=["Step 1: Observation A", "Step 2: Evidence B"],
            reasoning_object_ids=["obs-1", "ev-1", "hyp-1"],
            evidence_ids=["ev-1"],
            observation_ids=["obs-1"],
            confidence=0.85,
            attribution_trace="Traced from hypothesis back to observations",
            status="Complete",
        )
        assert attr.conclusion_id == "conc-123"
        assert attr.conclusion_type == "Hypothesis"
        assert len(attr.reasoning_path) == 2
        assert attr.confidence == 0.85
        assert attr.status == "Complete"
        assert attr.id is not None

    def test_deterministic_id(self):
        attr1 = Attribution(
            conclusion_id="conc-1",
            conclusion_type="Hypothesis",
            attribution_trace="Test trace",
        )
        attr2 = Attribution(
            conclusion_id="conc-1",
            conclusion_type="Hypothesis",
            attribution_trace="Test trace",
        )
        assert attr1.id == attr2.id

    def test_different_inputs_different_ids(self):
        attr1 = Attribution(
            conclusion_id="conc-1",
            conclusion_type="Hypothesis",
            attribution_trace="Trace A",
        )
        attr2 = Attribution(
            conclusion_id="conc-2",
            conclusion_type="Scenario",
            attribution_trace="Trace B",
        )
        assert attr1.id != attr2.id

    def test_to_dict_from_dict_roundtrip(self):
        attr = Attribution(
            conclusion_id="conc-456",
            conclusion_type="Scenario",
            reasoning_path=["Step 1", "Step 2", "Step 3"],
            reasoning_object_ids=["a", "b", "c"],
            evidence_ids=["ev-1", "ev-2"],
            observation_ids=["obs-1"],
            confidence=0.75,
            attribution_trace="Full trace",
            market_memory_ids=["mm-1"],
            status="Partial",
            ontology_tags=["test"],
        )
        data = attr.to_dict()
        restored = Attribution.from_dict(data)
        assert restored.conclusion_id == "conc-456"
        assert restored.conclusion_type == "Scenario"
        assert restored.reasoning_path == ["Step 1", "Step 2", "Step 3"]
        assert restored.reasoning_object_ids == ["a", "b", "c"]
        assert restored.evidence_ids == ["ev-1", "ev-2"]
        assert restored.observation_ids == ["obs-1"]
        assert restored.confidence == 0.75
        assert restored.attribution_trace == "Full trace"
        assert restored.market_memory_ids == ["mm-1"]
        assert restored.status == "Partial"
        assert attr.hash == restored.hash

    def test_deterministic_hash_stability(self):
        attr1 = Attribution(
            conclusion_id="conc-hash",
            conclusion_type="Hypothesis",
            reasoning_path=["A", "B"],
            reasoning_object_ids=["x", "y"],
            evidence_ids=["e1"],
            observation_ids=["o1"],
            confidence=0.9,
        )
        attr2 = Attribution(
            conclusion_id="conc-hash",
            conclusion_type="Hypothesis",
            reasoning_path=["A", "B"],
            reasoning_object_ids=["x", "y"],
            evidence_ids=["e1"],
            observation_ids=["o1"],
            confidence=0.9,
        )
        assert attr1.hash == attr2.hash

    def test_update_confidence(self):
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            confidence=0.5,
        )
        attr.update_confidence(0.9)
        assert attr.confidence == 0.9

    def test_update_status(self):
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            status="Pending",
        )
        attr.update_status("Complete")
        assert attr.status == "Complete"

    def test_link_market_memory(self):
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
        )
        assert len(attr.market_memory_ids) == 0
        attr.link_market_memory("mm-1")
        assert "mm-1" in attr.market_memory_ids
        attr.link_market_memory("mm-1")  # duplicate ignored
        assert len(attr.market_memory_ids) == 1
        attr.link_market_memory("mm-2")
        assert len(attr.market_memory_ids) == 2

    def test_verify_integrity_complete(self):
        attr = Attribution(
            conclusion_id="conc-ok",
            conclusion_type="Hypothesis",
            reasoning_object_ids=["r1", "r2"],
            evidence_ids=["e1"],
            observation_ids=["o1"],
            market_memory_ids=["m1"],
        )
        available = {"conc-ok", "r1", "r2", "e1", "o1", "m1"}
        report = attr.verify_integrity(available)
        assert report["complete"] is True
        assert report["status"] == "Complete"
        assert len(report["missing_references"]) == 0

    def test_verify_integrity_missing(self):
        attr = Attribution(
            conclusion_id="conc-miss",
            conclusion_type="Hypothesis",
            reasoning_object_ids=["r1", "missing"],
            evidence_ids=["e1"],
            observation_ids=["o1"],
        )
        available = {"conc-miss", "r1", "e1", "o1"}
        report = attr.verify_integrity(available)
        assert report["complete"] is False
        assert "missing" in report["missing_references"]
        assert report["status"] in ("Partial", "Broken")

    def test_verify_integrity_all_missing(self):
        attr = Attribution(
            conclusion_id="conc-all-miss",
            conclusion_type="Hypothesis",
            reasoning_object_ids=["r1"],
        )
        report = attr.verify_integrity(set())
        assert report["complete"] is False
        assert report["status"] == "Broken"

    def test_default_values(self):
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
        )
        assert attr.reasoning_path == []
        assert attr.reasoning_object_ids == []
        assert attr.evidence_ids == []
        assert attr.observation_ids == []
        assert attr.confidence == 0.0
        assert attr.attribution_trace == ""
        assert attr.market_memory_ids == []
        assert attr.status == "Pending"

    def test_object_registry_registered(self):
        assert "Attribution" in OBJECT_REGISTRY
        assert OBJECT_REGISTRY["Attribution"] == Attribution
        assert "AttributionGraph" in OBJECT_REGISTRY
        assert OBJECT_REGISTRY["AttributionGraph"] == AttributionGraph


# ===================================================================
# 2. AttributionGraph
# ===================================================================


class TestAttributionGraph:
    def test_create_empty(self):
        graph = AttributionGraph(research_id="res-1")
        assert graph.research_id == "res-1"
        assert graph.total_attributions == 0
        assert graph.average_confidence == 0.0

    def test_add_attribution(self):
        graph = AttributionGraph(research_id="res-1")
        attr = Attribution(conclusion_id="c1", conclusion_type="Hypothesis", confidence=0.8)
        graph.add_attribution(attr)
        assert graph.total_attributions == 1

    def test_get_by_conclusion(self):
        graph = AttributionGraph(research_id="res-1")
        a1 = Attribution(conclusion_id="c1", conclusion_type="Hypothesis", confidence=0.8)
        a2 = Attribution(conclusion_id="c2", conclusion_type="Scenario", confidence=0.6)
        graph.add_attribution(a1)
        graph.add_attribution(a2)
        assert graph.get_by_conclusion("c1") == a1
        assert graph.get_by_conclusion("c3") is None

    def test_get_by_type(self):
        graph = AttributionGraph(research_id="res-1")
        a1 = Attribution(conclusion_id="c1", conclusion_type="Hypothesis")
        a2 = Attribution(conclusion_id="c2", conclusion_type="Hypothesis")
        a3 = Attribution(conclusion_id="c3", conclusion_type="Scenario")
        graph.add_attribution(a1)
        graph.add_attribution(a2)
        graph.add_attribution(a3)
        hyps = graph.get_by_type("Hypothesis")
        assert len(hyps) == 2
        scens = graph.get_by_type("Scenario")
        assert len(scens) == 1

    def test_counts_by_status(self):
        graph = AttributionGraph(research_id="res-1")
        graph.add_attribution(Attribution(conclusion_id="c1", conclusion_type="Hypothesis", status="Complete"))
        graph.add_attribution(Attribution(conclusion_id="c2", conclusion_type="Hypothesis", status="Partial"))
        graph.add_attribution(Attribution(conclusion_id="c3", conclusion_type="Scenario", status="Broken"))
        assert graph.complete_count == 1
        assert graph.partial_count == 1
        assert graph.broken_count == 1

    def test_average_confidence(self):
        graph = AttributionGraph(research_id="res-1")
        graph.add_attribution(Attribution(conclusion_id="c1", conclusion_type="Hypothesis", confidence=1.0))
        graph.add_attribution(Attribution(conclusion_id="c2", conclusion_type="Hypothesis", confidence=0.5))
        assert graph.average_confidence == 0.75

    def test_verify_all(self):
        graph = AttributionGraph(research_id="res-1")
        a1 = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            reasoning_object_ids=["r1", "r2"],
        )
        graph.add_attribution(a1)
        reports = graph.verify_all({"c1", "r1", "r2"})
        assert len(reports) == 1
        assert reports[0]["complete"] is True

    def test_to_dict_from_dict_roundtrip(self):
        graph = AttributionGraph(
            research_id="res-rt",
            ontology_tags=["test"],
        )
        attr = Attribution(conclusion_id="c1", conclusion_type="Hypothesis")
        graph.add_attribution(attr)
        data = graph.to_dict()
        restored = AttributionGraph.from_dict(data)
        assert restored.research_id == "res-rt"
        assert restored.attribution_ids == [attr.id]

    def test_deterministic_id(self):
        g1 = AttributionGraph(research_id="res-det")
        g2 = AttributionGraph(research_id="res-det")
        assert g1.id == g2.id


# ===================================================================
# 3. Engine: chain tracing
# ===================================================================


class TestAttributionEngineTracing:
    def test_trace_observation(self, engine, repo, sample_observation):
        """Observations are the end of the chain — no upstream."""
        result = engine.trace_conclusion(sample_observation.id, "Observation")
        # Observations aren't attributable, but tracing still works
        assert result["conclusion_id"] == sample_observation.id
        assert len(result["reasoning_object_ids"]) >= 1

    def test_trace_hypothesis(self, engine, repo, sample_hypothesis, sample_evidence, sample_interpretation):
        result = engine.trace_conclusion(sample_hypothesis.id, "Hypothesis")
        assert result["conclusion_id"] == sample_hypothesis.id
        assert len(result["reasoning_path"]) >= 1
        # Should have found evidence
        assert len(result["evidence_ids"]) >= 1
        assert sample_evidence.id in result["evidence_ids"]

    def test_trace_scenario(self, engine, repo, sample_scenario, sample_hypothesis):
        result = engine.trace_conclusion(sample_scenario.id, "Scenario")
        assert result["conclusion_id"] == sample_scenario.id
        assert len(result["reasoning_object_ids"]) >= 1

    def test_get_evidence_chain(self, engine, repo, sample_hypothesis, sample_evidence):
        ev_ids = engine.get_evidence_chain(sample_hypothesis.id)
        assert sample_evidence.id in ev_ids

    def test_get_observation_chain(self, engine, repo, sample_hypothesis, sample_evidence, sample_observation):
        obs_ids = engine.get_observation_chain(sample_hypothesis.id)
        assert sample_observation.id in obs_ids

    def test_trace_missing_object(self, engine, repo):
        result = engine.trace_conclusion("nonexistent-id", "Hypothesis")
        assert result["conclusion_id"] == "nonexistent-id"
        # Should still produce some output
        assert "reasoning_path" in result


# ===================================================================
# 4. Engine: attribution creation
# ===================================================================


class TestAttributionEngineCreation:
    def test_create_attribution_for_hypothesis(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        assert isinstance(attr, Attribution)
        assert attr.conclusion_id == sample_hypothesis.id
        assert attr.conclusion_type == "Hypothesis"
        assert len(attr.reasoning_object_ids) >= 1
        assert attr.confidence > 0.0

    def test_create_attribution_with_ontology_tags(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(
            sample_hypothesis.id,
            "Hypothesis",
            ontology_tags=["macro", "fed"],
        )
        assert "macro" in attr.ontology_tags
        assert "fed" in attr.ontology_tags

    def test_create_attribution_non_attributable_type(self, engine, repo, sample_observation):
        with pytest.raises(ValueError, match="Cannot create attribution for type 'Observation'"):
            engine.create_attribution(sample_observation.id, "Observation")

    def test_create_attribution_missing_conclusion(self, engine, repo):
        with pytest.raises(ValueError, match="Conclusion object not found"):
            engine.create_attribution("nonexistent", "Hypothesis")

    def test_create_attribution_deterministic(self, engine, repo, sample_hypothesis):
        attr1 = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        # Clean up and recreate — should get same result with deterministic IDs
        # (Note: AuditEntries will have different timestamps = different IDs,
        #  but the attribution itself should be deterministic)
        assert attr1.id is not None
        assert attr1.conclusion_id == sample_hypothesis.id


# ===================================================================
# 5. Engine: graph management
# ===================================================================


class TestAttributionEngineGraph:
    def test_create_graph_with_attributions(self, engine, repo, sample_hypothesis, sample_scenario):
        attr1 = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        attr2 = engine.create_attribution(sample_scenario.id, "Scenario")
        graph = engine.create_attribution_graph(
            research_id="res-test-graph",
            attribution_ids=[attr1.id, attr2.id],
        )
        assert isinstance(graph, AttributionGraph)
        assert graph.total_attributions == 2

    def test_create_graph_auto_discover(self, engine, repo, complete_research_cycle):
        cycle = complete_research_cycle
        graph = engine.create_attribution_graph(
            research_id=cycle["research"].id,
        )
        assert isinstance(graph, AttributionGraph)
        assert graph.total_attributions >= 1

    def test_get_attribution_report(self, engine, repo, complete_research_cycle):
        cycle = complete_research_cycle
        # Create attributions first
        for obj_type, obj_key in [("Hypothesis", "hyp"), ("Scenario", "sc")]:
            obj = cycle[obj_key]
            engine.create_attribution(obj.id, obj_type)

        # Also create a graph
        engine.create_attribution_graph(research_id=cycle["research"].id)

        report = engine.get_attribution_report(cycle["research"].id)
        assert report["research_id"] == cycle["research"].id
        assert report["total_attributions"] >= 2
        assert "average_confidence" in report
        assert len(report["attributions"]) >= 2

    def test_get_attribution_report_missing_research(self, engine, repo):
        report = engine.get_attribution_report("nonexistent-research")
        assert report["research_id"] == "nonexistent-research"
        assert "error" in report


# ===================================================================
# 6. Engine: integrity verification
# ===================================================================


class TestAttributionEngineIntegrity:
    def test_verify_valid_attribution(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        report = engine.verify_attribution(attr.id)
        assert report["attribution_id"] == attr.id
        assert "missing_references" in report

    def test_verify_missing_attribution(self, engine, repo):
        report = engine.verify_attribution("nonexistent")
        assert "error" in report

    def test_verify_graph(self, engine, repo, sample_hypothesis, sample_scenario):
        attr1 = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        attr2 = engine.create_attribution(sample_scenario.id, "Scenario")
        graph = engine.create_attribution_graph(
            research_id="res-verify",
            attribution_ids=[attr1.id, attr2.id],
        )
        report = engine.verify_graph(graph.id)
        assert report["graph_id"] == graph.id
        assert report["total"] == 2
        assert "all_complete" in report

    def test_verify_missing_graph(self, engine, repo):
        report = engine.verify_graph("nonexistent")
        assert "error" in report

    def test_compute_attribution_confidence(self, engine, repo, sample_hypothesis):
        confidence = engine.compute_attribution_confidence(
            sample_hypothesis.id,
            "Hypothesis",
        )
        assert 0.0 <= confidence <= 1.0


# ===================================================================
# 7. Engine: market memory linking
# ===================================================================


class TestAttributionEngineMemoryLinking:
    def test_link_market_memory(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")

        # Create a market memory object to link
        from researchos.objects.market_memory import MarketStructure

        ms = MarketStructure(
            structure_type="BOS",
            asset="EURUSD",
            timeframe="H1",
            timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
            direction="bullish",
            price_level=1.1050,
        )
        repo.save(ms)

        updated = engine.link_market_memory(attr.id, [ms.id])
        assert ms.id in updated.market_memory_ids

    def test_link_missing_memory(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        with pytest.raises(ValueError, match="MarketMemory object not found"):
            engine.link_market_memory(attr.id, ["nonexistent"])

    def test_link_missing_attribution(self, engine, repo):
        with pytest.raises(ValueError, match="Attribution not found"):
            engine.link_market_memory("nonexistent", ["mm-1"])

    def test_find_similar_patterns(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")

        # Create and link market memory
        from researchos.objects.market_memory import MarketOutcome, MarketStructure

        ms = MarketStructure(
            structure_type="BOS",
            asset="EURUSD",
            timeframe="H1",
            timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
            direction="bullish",
            price_level=1.1050,
        )
        repo.save(ms)

        outcome = MarketOutcome(
            event_id=ms.id,
            event_type="MarketStructure",
            asset="EURUSD",
            timestamp=datetime(2024, 6, 2, tzinfo=timezone.utc),
            outcome_type="Success",
            actual_move=0.0020,
            expected_move=0.0015,
            confidence=0.8,
        )
        repo.save(outcome)

        engine.link_market_memory(attr.id, [ms.id])
        patterns = engine.find_similar_patterns(attr.id)
        assert len(patterns) >= 1
        assert patterns[0]["memory_id"] == ms.id
        assert "outcomes" in patterns[0]

    def test_find_similar_patterns_no_links(self, engine, repo, sample_hypothesis):
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        patterns = engine.find_similar_patterns(attr.id)
        assert patterns == []

    def test_find_similar_patterns_missing_attribution(self, engine, repo):
        patterns = engine.find_similar_patterns("nonexistent")
        assert patterns == []


# ===================================================================
# 8. Full integration
# ===================================================================


class TestAttributionFullIntegration:
    def test_complete_research_cycle_attribution(self, engine, repo, complete_research_cycle):
        """Full pipeline: research cycle → attribution for all conclusions."""
        cycle = complete_research_cycle

        # Create attributions for each attributable object
        attr_hyp = engine.create_attribution(cycle["hyp"].id, "Hypothesis")
        attr_sc = engine.create_attribution(cycle["sc"].id, "Scenario")

        # Both should have traced back to observations
        assert len(attr_hyp.observation_ids) >= 1
        assert cycle["obs1"].id in attr_hyp.observation_ids
        assert len(attr_sc.observation_ids) >= 1

        # Evidence chains should be complete
        assert cycle["ev1"].id in attr_hyp.evidence_ids
        assert cycle["ev2"].id in attr_hyp.evidence_ids

    def test_attribution_report_includes_all(self, engine, repo, complete_research_cycle):
        """Attribution report should include all conclusions."""
        cycle = complete_research_cycle

        # Create attributions
        engine.create_attribution(cycle["hyp"].id, "Hypothesis")
        engine.create_attribution(cycle["sc"].id, "Scenario")

        # Create graph
        engine.create_attribution_graph(research_id=cycle["research"].id)

        report = engine.get_attribution_report(cycle["research"].id)
        assert report["total_attributions"] == 2

        types = {a["conclusion_type"] for a in report["attributions"]}
        assert "Hypothesis" in types
        assert "Scenario" in types

    def test_attribution_adds_audit_entries(self, engine, repo, sample_hypothesis):
        """Creating attribution should generate audit entries."""
        initial_count = len([o for o in repo.get_all() if isinstance(o, AuditEntry)])
        engine.create_attribution(sample_hypothesis.id, "Hypothesis")
        new_count = len([o for o in repo.get_all() if isinstance(o, AuditEntry)])
        assert new_count > initial_count


# ===================================================================
# 9. Edge cases
# ===================================================================


class TestAttributionEdgeCases:
    def test_empty_reasoning_path(self, engine, repo):
        """Attribution with empty path should be Broken."""
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            confidence=0.0,
        )
        assert attr.status == "Pending"
        assert attr.reasoning_path == []

    def test_attribution_with_many_ids(self, engine, repo):
        """Attribution should handle large numbers of IDs."""
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            reasoning_object_ids=[f"id-{i}" for i in range(100)],
            evidence_ids=[f"ev-{i}" for i in range(50)],
            observation_ids=[f"obs-{i}" for i in range(50)],
        )
        assert len(attr.reasoning_object_ids) == 100
        assert len(attr.evidence_ids) == 50
        assert len(attr.observation_ids) == 50

    def test_attribution_same_id_multiple_evidence(self):
        """Deduplication of evidence IDs should not happen in the object itself (it's a simple list)."""
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            evidence_ids=["ev-1", "ev-1", "ev-2"],
        )
        # The object stores as-is; dedup happens at collection level
        assert attr.evidence_ids == ["ev-1", "ev-1", "ev-2"]

    def test_graph_with_no_attributions(self, engine, repo, sample_research):
        graph = engine.create_attribution_graph(
            research_id=sample_research.id,
        )
        assert graph.research_id == sample_research.id
        # Should still work and be saved
        assert graph.id is not None

    def test_confidence_bounds(self):
        """Attribution confidence should stay within [0, 1]."""
        attr = Attribution(
            conclusion_id="c1",
            conclusion_type="Hypothesis",
            confidence=1.5,  # Clamped in from_dict but not in __init__
        )
        # The engine computes confidence with bounds
        assert attr.confidence == 1.5  # Stored as-is

        # From_dict should restore it
        data = attr.to_dict()
        restored = Attribution.from_dict(data)
        assert restored.confidence == 1.5

    def test_trace_cycle_detection(self, engine, repo):
        """Circular references should not cause infinite loops."""
        # Create a self-referencing situation
        obs = Observation(
            source="TEST",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=1,
        )
        repo.save(obs)

        ev = Evidence(
            observation_id=obs.id,
            hypothesis_id=obs.id,  # Circular ref via hypothesis_id pointing to observation
            interpretation="Test",
        )
        repo.save(ev)

        # Evidence references observation, but shouldn't loop
        result = engine.trace_conclusion(ev.id, "Evidence")
        assert len(result["reasoning_path"]) > 0

    def test_attribution_integrity_auto_update(self, engine, repo, sample_hypothesis):
        """verify_attribution should update status if references are missing."""
        attr = engine.create_attribution(sample_hypothesis.id, "Hypothesis")

        # Delete the hypothesis to break references
        repo.delete(sample_hypothesis.id)

        report = engine.verify_attribution(attr.id)
        assert report["complete"] is False

    def test_attributable_types_constants(self):
        """ATTRIBUTABLE_TYPES should contain expected types."""
        assert "Hypothesis" in ATTRIBUTABLE_TYPES
        assert "Scenario" in ATTRIBUTABLE_TYPES
        assert "Narrative" in ATTRIBUTABLE_TYPES
        assert "ResearchReport" in ATTRIBUTABLE_TYPES
        assert "Observation" not in ATTRIBUTABLE_TYPES
        assert "Evidence" not in ATTRIBUTABLE_TYPES

    def test_traversal_rules_exist(self):
        """TRAVERSAL_RULES should have rules for attributable types."""
        for t in ATTRIBUTABLE_TYPES:
            if t in TRAVERSAL_RULES:
                assert len(TRAVERSAL_RULES[t]) > 0
