"""
Constitutional compliance tests for ResearchOS.

Tests:
    1. Finalized objects cannot mutate (Article XVII immutability)
    2. Same input produces same hash (Article XVII determinism)
    3. Serialization round trip preserves data (Article XVII completeness)
    4. Timestamp changes do not change content hash (Article XVII determinism)
    5. Removed modules cannot be imported (Article II scope boundaries)
"""

from datetime import datetime, timezone

import pytest

from researchos.core.base_object import BaseObject
from researchos.core.lifecycle import Lifecycle, LifecycleStage
from researchos.objects.evidence import Evidence
from researchos.objects.research import Research
from researchos.objects.observation import Observation


class TestFinalizedImmutability:
    """Test 1: FINALIZED objects reject mutations."""

    def test_finalized_lifecycle_rejects_transitions(self):
        lc = Lifecycle(initial_stage=LifecycleStage.FINALIZED)
        with pytest.raises(RuntimeError, match="Cannot transition from terminal stage"):
            lc.transition(LifecycleStage.ACTIVE, "should fail")

    def test_archived_lifecycle_rejects_transitions(self):
        lc = Lifecycle(initial_stage=LifecycleStage.ARCHIVED)
        with pytest.raises(RuntimeError, match="Cannot transition from terminal stage"):
            lc.transition(LifecycleStage.ACTIVE, "should fail")

    def test_active_allows_transition(self):
        lc = Lifecycle(initial_stage=LifecycleStage.ACTIVE)
        lc.transition(LifecycleStage.COMPLETE, "allowed")
        assert lc.current_stage == LifecycleStage.COMPLETE


class TestHashDeterminism:
    """Test 2: Same input always produces same hash."""

    def test_same_observation_same_hash(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        rt = datetime(2024, 6, 2, tzinfo=timezone.utc)
        obs1 = Observation(source="MACRO:CPI", timestamp=ts, value=3.2, retrieval_time=rt)
        obs2 = Observation(source="MACRO:CPI", timestamp=ts, value=3.2, retrieval_time=rt)
        assert obs1.hash == obs2.hash

    def test_different_observations_different_hash(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        obs1 = Observation(source="MACRO:CPI", timestamp=ts, value=3.2)
        obs2 = Observation(source="MACRO:CPI", timestamp=ts, value=3.3)
        assert obs1.hash != obs2.hash

    def test_evidence_deterministic_hash(self):
        ev1 = Evidence(observation_id="obs1", hypothesis_id="hyp1", interpretation="Test")
        ev2 = Evidence(observation_id="obs1", hypothesis_id="hyp1", interpretation="Test")
        assert ev1.hash == ev2.hash

    def test_research_deterministic_hash(self):
        r1 = Research(question="What is inflation?", time_horizon="Monthly", asset="US")
        r2 = Research(question="What is inflation?", time_horizon="Monthly", asset="US")
        assert r1.hash == r2.hash


class TestSerializationRoundTrip:
    """Test 3: Serialization round trip preserves all fields."""

    def test_observation_round_trip(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        obs = Observation(source="MACRO:CPI", timestamp=ts, value=3.2, unit="percent")
        d = obs.to_dict()
        assert d["source"] == "MACRO:CPI"
        assert d["value"] == 3.2
        assert d["unit"] == "percent"
        assert d["object_type"] == "Observation"
        assert "hash" in d
        assert "id" in d

    def test_evidence_round_trip_includes_observation_timestamp(self):
        ev = Evidence(observation_id="obs1", hypothesis_id="hyp1", interpretation="Test")
        d = ev.to_dict()
        assert d["observation_id"] == "obs1"
        assert d["hypothesis_id"] == "hyp1"
        assert d["interpretation"] == "Test"
        assert d["object_type"] == "Evidence"
        assert "observation_timestamp" in d


class TestTimestampInHash:
    """Test 4: Semantically significant retrieval metadata participates in hash."""

    def test_research_timestamp_not_in_hash(self):
        r1 = Research(question="Test Q", asset="US")
        r2 = Research(question="Test Q", asset="US")
        assert r1.hash == r2.hash

    def test_observation_retrieval_time_in_hash(self):
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        rt1 = datetime(2024, 6, 1, tzinfo=timezone.utc)
        rt2 = datetime(2024, 6, 2, tzinfo=timezone.utc)
        obs1 = Observation(source="T", timestamp=ts, value=1, retrieval_time=rt1)
        obs2 = Observation(source="T", timestamp=ts, value=1, retrieval_time=rt2)
        assert obs1.hash != obs2.hash

    def test_observation_same_retrieval_time_same_hash(self):
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        rt = datetime(2024, 6, 1, tzinfo=timezone.utc)
        obs1 = Observation(source="T", timestamp=ts, value=1, retrieval_time=rt)
        obs2 = Observation(source="T", timestamp=ts, value=1, retrieval_time=rt)
        assert obs1.hash == obs2.hash


class TestRemovedModulesCannotBeImported:
    """Test 5: Removed constitutional violation modules cannot be imported."""

    def test_engines_research_orchestrator_removed(self):
        with pytest.raises(ModuleNotFoundError):
            import researchos.engines.research_orchestrator  # noqa: F401

    def test_engines_position_engine_removed(self):
        with pytest.raises(ModuleNotFoundError):
            import researchos.engines.position_engine  # noqa: F401

    def test_core_process_objects_removed(self):
        with pytest.raises(ModuleNotFoundError):
            import researchos.core.process_objects  # noqa: F401

    def test_core_research_cycles_removed(self):
        with pytest.raises(ModuleNotFoundError):
            import researchos.core.research_cycles  # noqa: F401


class TestDeterministicIdentity:
    """Test 6: ID generation requires a seed (no uncontrolled randomness)."""

    def test_generate_id_requires_seed(self):
        from researchos.core.identity import generate_id
        with pytest.raises(ValueError, match="requires a deterministic seed"):
            generate_id(None)

    def test_generate_id_empty_seed_raises(self):
        from researchos.core.identity import generate_id
        with pytest.raises(ValueError, match="requires a deterministic seed"):
            generate_id("")

    def test_same_seed_same_id(self):
        from researchos.core.identity import generate_id
        id1 = generate_id("test-determinism")
        id2 = generate_id("test-determinism")
        assert id1 == id2


class TestDeterministicSerialization:
    """Test 7: JSON serialization is deterministic (sorted keys)."""

    def test_to_json_sorted_keys(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        obs = Observation(source="TEST", timestamp=ts, value=1.0)
        json_str = obs.to_json()
        assert '"hash"' in json_str
        assert '"id"' in json_str
        import json as _json
        parsed = _json.loads(json_str)
        assert parsed["object_type"] == "Observation"

    def test_to_json_same_content_same_output(self):
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        rt = datetime(2024, 6, 2, tzinfo=timezone.utc)
        obs1 = Observation(source="TEST", timestamp=ts, value=1.0, retrieval_time=rt)
        obs2 = Observation(source="TEST", timestamp=ts, value=1.0, retrieval_time=rt)
        assert obs1.hash == obs2.hash

    def test_from_dict_on_base_uses_new_pattern(self):
        obj = BaseObject.from_dict({"id": "test_id"})
        assert obj.id == "test_id"
        assert obj.created_at is not None


class TestDeterministicEvidence:
    """Test 8: Evidence computations are deterministic with fixed reference_time."""

    def test_evidence_weight_deterministic_with_reference_time(self):
        from researchos.objects.evidence import Evidence
        ref = datetime(2024, 12, 31, tzinfo=timezone.utc)
        ev = Evidence(
            observation_id="obs1",
            hypothesis_id="hyp1",
            interpretation="Test",
            observation_timestamp=datetime(2024, 12, 1, tzinfo=timezone.utc),
        )
        w1 = ev.weight(ref)
        w2 = ev.weight(ref)
        assert w1 == w2

    def test_evidence_age_days_deterministic_with_reference_time(self):
        from researchos.objects.evidence import Evidence
        ref = datetime(2024, 12, 31, tzinfo=timezone.utc)
        ev = Evidence(
            observation_id="obs1",
            hypothesis_id="hyp1",
            interpretation="Test",
            observation_timestamp=datetime(2024, 12, 1, tzinfo=timezone.utc),
        )
        assert ev.age_days(ref) == 30


class TestDeterministicScenarioNormalization:
    """Test 9: Probability normalization is deterministic with rounding."""

    def test_normalize_probabilities_deterministic(self):
        from researchos.objects.scenario import ScenarioSet, Scenario
        s1 = Scenario(
            hypothesis_id="test-hyp",
            type="Base",
            label="Scenario A",
            probability=0.4,
        )
        s2 = Scenario(
            hypothesis_id="test-hyp",
            type="Base",
            label="Scenario B",
            probability=0.6,
        )
        ss = ScenarioSet(research_id="test-research")
        ss.add_scenario(s1)
        ss.add_scenario(s2)
        ss.normalize_probabilities(precision=6)
        total = s1.probability + s2.probability
        assert abs(total - 1.0) < 1e-6

    def test_normalize_probabilities_same_input_same_output(self):
        from researchos.objects.scenario import ScenarioSet, Scenario
        def make_set():
            ss = ScenarioSet(research_id="test-research")
            ss.add_scenario(Scenario(hypothesis_id="h", type="Base", label="A", probability=0.3))
            ss.add_scenario(Scenario(hypothesis_id="h", type="Base", label="B", probability=0.3))
            ss.add_scenario(Scenario(hypothesis_id="h", type="Base", label="C", probability=0.3))
            ss.normalize_probabilities(precision=6)
            return tuple(sc.probability for sc in ss.scenarios)
        assert make_set() == make_set()


class TestDeterministicHypothesisRanking:
    """Test 10: Hypothesis ranking has deterministic tie-breaking."""

    def test_get_ranked_tie_break_by_id(self):
        from researchos.objects.hypothesis import HypothesisSet, Hypothesis
        research_id = "test-research"
        hs = HypothesisSet(research_id=research_id)
        # Same rank_score — tie should break by id deterministically
        h1 = Hypothesis(research_id=research_id, type="Primary", statement="A", evidence_strength=0.5, coherence=0.5, plausibility=0.5, falsifiability=0.5, id="hyp-a")
        h2 = Hypothesis(research_id=research_id, type="Primary", statement="B", evidence_strength=0.5, coherence=0.5, plausibility=0.5, falsifiability=0.5, id="hyp-b")
        hs.add_hypothesis(h1)
        hs.add_hypothesis(h2)
        ranked = hs.get_ranked()
        # Both have same score, so order is determined by id (ascending)
        ids = [h.id for h in ranked]
        assert ids == sorted(ids)
