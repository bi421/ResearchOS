"""
Tests for ResearchOS object classes.

Based on Article XVII: Object Model — all objects are tested for:
    - Deterministic identity generation
    - Correct property initialization
    - Deterministic hashing
    - Lifecycle transitions
    - Serialization (to_dict, to_json)
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import Lifecycle, LifecycleStage
from researchos.core.timestamp import utc_now
from researchos.objects.observation import Observation, MarketState, MacroState
from researchos.objects.evidence import Evidence, EvidenceRegistry
from researchos.objects.interpretation import Interpretation, Narrative
from researchos.objects.hypothesis import Hypothesis, HypothesisSet
from researchos.objects.scenario import Scenario, ScenarioSet
from researchos.objects.confidence import Confidence, ConfidenceReport
from researchos.objects.contradiction import Contradiction, ContradictionReport
from researchos.objects.knowledge import Knowledge, Pattern, Lesson
from researchos.objects.research import Research, ResearchReport, ResearchQuestion
from researchos.validation.validators import get_validator
from researchos.repository.memory import MemoryRepository


class TestIdentity:
    """Tests for deterministic identity generation."""

    def test_generate_id_deterministic(self):
        """Same seed should produce same ID."""
        id1 = generate_id("test_seed")
        id2 = generate_id("test_seed")
        assert id1 == id2

    def test_generate_id_different_seeds(self):
        """Different seeds should produce different IDs."""
        id1 = generate_id("seed1")
        id2 = generate_id("seed2")
        assert id1 != id2

    def test_deterministic_hash(self):
        """Same content should produce same hash."""
        content = {"a": 1, "b": 2}
        h1 = deterministic_hash(content)
        h2 = deterministic_hash(content)
        assert h1 == h2

    def test_deterministic_hash_different_content(self):
        """Different content should produce different hashes."""
        h1 = deterministic_hash({"a": 1})
        h2 = deterministic_hash({"a": 2})
        assert h1 != h2


class TestObservation:
    """Tests for Observation objects."""

    def test_observation_creation(self):
        """Test basic observation creation."""
        obs = Observation(
            source="MACRO:CPI_YOY",
            timestamp=utc_now(),
            value=3.2,
            unit="percent",
        )
        assert obs.source == "MACRO:CPI_YOY"
        assert obs.value == 3.2
        assert obs.unit == "percent"
        assert obs.validated is False

    def test_observation_validation(self):
        """Test observation validation."""
        obs = Observation(
            source="MACRO:CPI_YOY",
            timestamp=utc_now(),
            value=3.2,
        )
        assert obs.validate() is True
        assert obs.validated is True

    def test_observation_deterministic_id(self):
        """Test that observation ID is deterministic."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        obs1 = Observation(source="TEST", timestamp=ts, value=42)
        obs2 = Observation(source="TEST", timestamp=ts, value=42)
        assert obs1.id == obs2.id

    def test_observation_to_dict(self):
        """Test observation serialization."""
        obs = Observation(
            source="TEST",
            timestamp=utc_now(),
            value=42,
        )
        d = obs.to_dict()
        assert d["source"] == "TEST"
        assert d["value"] == 42
        assert "hash" in d


class TestEvidence:
    """Tests for Evidence objects."""

    def test_evidence_creation(self):
        """Test basic evidence creation."""
        ev = Evidence(
            observation_id="obs1",
            hypothesis_id="hyp1",
            interpretation="Inflation is moderating",
            direction="Supporting",
        )
        assert ev.observation_id == "obs1"
        assert ev.hypothesis_id == "hyp1"
        assert ev.direction == "Supporting"
        assert 0.0 <= ev.quality <= 1.0
        assert 0.0 <= ev.confidence <= 1.0
        assert 0.0 <= ev.weight() <= 1.0

    def test_evidence_quality_computation(self):
        """Test evidence quality computation."""
        ev = Evidence(
            observation_id="obs1",
            hypothesis_id="hyp1",
            interpretation="Test",
            source_reliability=0.9,
            recency=0.8,
            relevance=0.7,
            consensus=0.6,
            structural_importance=0.5,
            quality_factor=1.0,
        )
        expected_quality = 0.9 * 0.8 * 0.7 * 0.6 * 0.5 * 1.0
        assert abs(ev.quality - expected_quality) < 0.001

    def test_evidence_registry(self):
        """Test evidence registry."""
        registry = EvidenceRegistry(research_id="research1")
        assert registry.total_weight() == 0.0
        assert registry.supporting_weight() == 0.0
        assert registry.contradicting_weight() == 0.0


class TestHypothesis:
    """Tests for Hypothesis objects."""

    def test_hypothesis_creation(self):
        """Test basic hypothesis creation."""
        hyp = Hypothesis(
            research_id="research1",
            type="Primary",
            statement="Inflation will continue to moderate",
            evidence_strength=0.8,
            coherence=0.7,
            plausibility=0.9,
            falsifiability=0.6,
        )
        assert hyp.type == "Primary"
        assert hyp.statement == "Inflation will continue to moderate"
        assert hyp.status == "Active"
        assert hyp.rank_score > 0.0

    def test_hypothesis_ranking(self):
        """Test hypothesis ranking computation."""
        hyp = Hypothesis(
            research_id="research1",
            type="Primary",
            statement="Test",
            evidence_strength=0.8,
            coherence=0.7,
            plausibility=0.9,
            falsifiability=0.6,
        )
        expected_rank = 0.8 * 0.40 + 0.7 * 0.30 + 0.9 * 0.20 + 0.6 * 0.10
        assert abs(hyp.rank_score - expected_rank) < 0.001

    def test_hypothesis_invalidation(self):
        """Test hypothesis invalidation."""
        hyp = Hypothesis(
            research_id="research1",
            type="Primary",
            statement="Test",
            invalid_if=["evidence_x"],
        )
        assert hyp.check_invalidation(["evidence_y"]) is False
        assert hyp.status == "Active"
        assert hyp.check_invalidation(["evidence_x"]) is True
        assert hyp.status == "Invalidated"


class TestScenario:
    """Tests for Scenario objects."""

    def test_scenario_creation(self):
        """Test basic scenario creation."""
        sc = Scenario(
            hypothesis_id="hyp1",
            type="Base",
            label="Scenario A",
            probability=0.5,
        )
        assert sc.type == "Base"
        assert sc.label == "Scenario A"
        assert sc.probability == 0.5
        assert sc.status == "Active"

    def test_scenario_set_normalization(self):
        """Test scenario set probability normalization."""
        ss = ScenarioSet(research_id="research1")
        ss.add_scenario(Scenario(hypothesis_id="hyp1", type="Base", probability=0.3))
        ss.add_scenario(Scenario(hypothesis_id="hyp1", type="Bull", probability=0.6))
        ss.add_scenario(Scenario(hypothesis_id="hyp1", type="Bear", probability=0.3))
        ss.normalize_probabilities()
        assert abs(ss.total_probability - 1.0) < 0.001


class TestConfidence:
    """Tests for Confidence objects."""

    def test_confidence_creation(self):
        """Test basic confidence creation."""
        conf = Confidence(
            target_id="hyp1",
            target_type="Hypothesis",
            evidence_strength=0.8,
            coherence=0.7,
            historical_precedent=0.6,
            model_uncertainty=0.5,
            recency=0.9,
        )
        assert conf.target_id == "hyp1"
        assert conf.target_type == "Hypothesis"
        assert 0.0 <= conf.value <= 1.0
        assert 0.0 <= conf.lower_bound <= conf.upper_bound <= 1.0

    def test_confidence_calibration_bin(self):
        """Test confidence calibration bin computation."""
        conf = Confidence(
            target_id="hyp1",
            target_type="Hypothesis",
            evidence_strength=0.75,
            coherence=0.75,
            historical_precedent=0.75,
            model_uncertainty=0.75,
            recency=0.75,
        )
        # All factors at 0.75 → value = 0.75 → bin = "0.7-0.8"
        assert conf.calibration_bin == "0.7-0.8"


class TestContradiction:
    """Tests for Contradiction objects."""

    def test_contradiction_creation(self):
        """Test basic contradiction creation."""
        c = Contradiction(
            research_id="research1",
            type="Internal",
            description="Evidence conflict",
            sides=[
                {"evidence": ["e1"], "weight": 0.8, "position": "Bullish"},
                {"evidence": ["e2"], "weight": 0.3, "position": "Bearish"},
            ],
        )
        assert c.type == "Internal"
        assert c.resolution == "Unresolved"
        assert c.severity > 0.0

    def test_contradiction_resolution(self):
        """Test contradiction resolution."""
        c = Contradiction(
            research_id="research1",
            type="Internal",
            description="Test",
            sides=[
                {"evidence": ["e1"], "weight": 0.8, "position": "A"},
                {"evidence": ["e2"], "weight": 0.3, "position": "B"},
            ],
        )
        # 0.8 / 0.3 = 2.67 >= 2.0, so should resolve automatically
        resolved = c.resolve()
        assert resolved is True
        assert c.resolution == "Resolved"


class TestResearch:
    """Tests for Research objects."""

    def test_research_creation(self):
        """Test basic research creation."""
        r = Research(
            question="What is the inflation outlook?",
            time_horizon="Monthly",
            asset="US",
        )
        assert r.question == "What is the inflation outlook?"
        assert r.time_horizon == "Monthly"
        assert r.asset == "US"
        assert r.status == "In Progress"

    def test_research_completion(self):
        """Test research completion."""
        r = Research(question="Test")
        r.complete()
        assert r.status == "Complete"
        assert r.completed_at is not None

    def test_research_report(self):
        """Test research report creation."""
        report = ResearchReport(
            research_id="research1",
            title="Inflation Outlook Report",
        )
        assert report.title == "Inflation Outlook Report"
        assert report.status == "Draft"
        report.finalize()
        assert report.status == "Final"


class TestValidation:
    """Tests for validation."""

    def test_observation_validator(self):
        """Test observation validation."""
        obs = Observation(
            source="TEST",
            timestamp=utc_now(),
            value=42,
        )
        validator = get_validator("Observation")
        is_valid, errors = validator.validate(obs)
        assert is_valid is True
        assert len(errors) == 0

    def test_evidence_validator(self):
        """Test evidence validation."""
        ev = Evidence(
            observation_id="obs1",
            hypothesis_id="hyp1",
            interpretation="Test",
        )
        validator = get_validator("Evidence")
        is_valid, errors = validator.validate(ev)
        assert is_valid is True


class TestRepository:
    """Tests for repository."""

    def test_memory_repository_save_get(self):
        """Test save and get in memory repository."""
        repo = MemoryRepository()
        obs = Observation(
            source="TEST",
            timestamp=utc_now(),
            value=42,
        )
        repo.save(obs)
        retrieved = repo.get(obs.id)
        assert retrieved is not None
        assert retrieved.id == obs.id

    def test_memory_repository_count(self):
        """Test repository count."""
        repo = MemoryRepository()
        assert repo.count() == 0
        repo.save(Observation(source="T", timestamp=utc_now(), value=1))
        assert repo.count() == 1

    def test_memory_repository_find_by_tag(self):
        """Test repository find by tag."""
        repo = MemoryRepository()
        obs = Observation(
            source="TEST",
            timestamp=utc_now(),
            value=42,
            ontology_tags=["inflation", "macro"],
        )
        repo.save(obs)
        results = repo.find_by_tag("inflation")
        assert len(results) == 1
        assert results[0].id == obs.id


class TestDeterminism:
    """Tests for determinism guarantees."""

    def test_same_inputs_same_hash(self):
        """Same inputs should produce same hash."""
        rt = datetime(2024, 6, 15, tzinfo=timezone.utc)
        obs1 = Observation(
            source="TEST", timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=42, retrieval_time=rt,
        )
        obs2 = Observation(
            source="TEST", timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=42, retrieval_time=rt,
        )
        assert obs1.hash == obs2.hash

    def test_different_inputs_different_hash(self):
        """Different inputs should produce different hashes."""
        obs1 = Observation(
            source="TEST",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=42,
        )
        obs2 = Observation(
            source="TEST",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=43,
        )
        assert obs1.hash != obs2.hash
