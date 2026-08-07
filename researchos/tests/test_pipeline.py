"""
Tests for the ResearchPipeline — coordinator for the object lifecycle.

Tests:
    1. ReferenceValidator works
    2. Pipeline creates a complete research lifecycle end-to-end
    3. Pipeline creates AuditEntry for each stage
    4. Reference integrity is enforced (missing IDs raise errors)
    5. Deterministic IDs are preserved through the pipeline
"""

from datetime import datetime, timezone

import pytest

from researchos.repository.memory import MemoryRepository
from researchos.pipeline import ResearchPipeline, ReferenceValidator
from researchos.objects.observation import Observation
from researchos.objects.evidence import Evidence
from researchos.objects.research import Research
from researchos.objects.process import AuditEntry


@pytest.fixture
def repo():
    return MemoryRepository()


@pytest.fixture
def pipeline(repo):
    return ResearchPipeline(repo)


class TestReferenceValidator:
    """Phase 3 — Reference integrity validation."""

    def test_exists_returns_false_for_missing(self, repo):
        v = ReferenceValidator(repo)
        assert not v.exists("nonexistent-id")

    def test_exists_returns_true_for_saved(self, repo):
        v = ReferenceValidator(repo)
        obj = Observation(source="T", timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc), value=1.0)
        repo.save(obj)
        assert v.exists(obj.id)

    def test_require_exists_raises_for_missing(self, repo):
        v = ReferenceValidator(repo)
        with pytest.raises(ValueError, match="not found in repository"):
            v.require_exists("bad-id", "TestObject")

    def test_require_exists_returns_id_for_found(self, repo):
        v = ReferenceValidator(repo)
        obj = Observation(source="T", timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc), value=1.0)
        repo.save(obj)
        assert v.require_exists(obj.id, "Observation") == obj.id

    def test_require_all_exist_raises_for_any_missing(self, repo):
        v = ReferenceValidator(repo)
        obj = Observation(source="T", timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc), value=1.0)
        repo.save(obj)
        with pytest.raises(ValueError, match="not found in repository"):
            v.require_all_exist([obj.id, "bad-id"], "Evidence")


class TestPipelineEndToEnd:
    """Phase 4+5 — Full pipeline lifecycle with audit."""

    def _ts(self, year=2024, month=1, day=1):
        return datetime(year, month, day, tzinfo=timezone.utc)

    def test_start_research_creates_research_and_cycle_and_audit(self, pipeline, repo):
        research = pipeline.start_research(
            question="What is inflation?",
            time_horizon="Monthly",
            asset="US",
        )
        assert isinstance(research, Research)
        assert research.question == "What is inflation?"
        assert repo.get(research.id) is not None

        # Audit entry was created
        audits = [o for o in repo.get_all() if isinstance(o, AuditEntry)]
        assert len(audits) >= 1
        assert audits[0].action == "RESEARCH_STARTED"

    def test_add_observation_links_to_research(self, pipeline, repo):
        research = pipeline.start_research("Test Q")
        obs = pipeline.add_observation(
            research_id=research.id,
            source="MACRO:CPI",
            timestamp=self._ts(),
            value=3.2,
        )
        assert isinstance(obs, Observation)
        assert obs.id in research.observation_ids

    def test_create_evidence_validates_observation_exists(self, pipeline, repo):
        research = pipeline.start_research("Test Q")
        obs = pipeline.add_observation(research.id, "MACRO:CPI", self._ts(), 3.2)

        # First need a hypothesis for evidence to link to
        hyp = pipeline.create_hypothesis(
            research_id=research.id,
            type="Primary",
            statement="Inflation is moderating",
        )

        ev = pipeline.create_evidence(
            observation_id=obs.id,
            hypothesis_id=hyp.id,
            interpretation="CPI is declining",
            research_id=research.id,
        )
        assert isinstance(ev, Evidence)
        assert ev.observation_id == obs.id
        assert ev.hypothesis_id == hyp.id

    def test_create_evidence_raises_for_missing_observation(self, pipeline, repo):
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.create_evidence(
                observation_id="bad-obs",
                hypothesis_id="bad-hyp",
                interpretation="test",
            )

    def test_complete_pipeline_end_to_end(self, pipeline, repo):
        """Full lifecycle: Research → Obs → Hyp → Evidence → Scenario → Confidence → Report → Validation → Knowledge."""
        # Start
        research = pipeline.start_research("Will inflation fall?", "Monthly", "US")

        # Observation
        obs = pipeline.add_observation(research.id, "MACRO:CPI", self._ts(2024, 6, 1), 3.2)

        # Hypothesis
        hyp = pipeline.create_hypothesis(
            research_id=research.id,
            type="Primary",
            statement="Inflation will fall to 2%",
        )

        # Evidence
        ev = pipeline.create_evidence(
            observation_id=obs.id,
            hypothesis_id=hyp.id,
            interpretation="CPI trend is downward",
            direction="Supporting",
            research_id=research.id,
        )

        # Scenario
        scenario = pipeline.create_scenario(
            research_id=research.id,
            hypothesis_id=hyp.id,
            type="Base",
            label="Soft Landing",
            probability=0.6,
        )

        # Confidence
        confidence = pipeline.register_confidence(
            target_id=hyp.id,
            target_type="Hypothesis",
            evidence_strength=0.8,
            research_id=research.id,
        )

        # Contradiction
        contradiction = pipeline.detect_contradiction(
            research_id=research.id,
            type="Internal",
            description="CPI data conflicts with growth data",
            sides=[
                {"name": "CPI falling", "weight": 0.8, "evidence": [ev.id]},
                {"name": "Growth slowing", "weight": 0.3, "evidence": []},
            ],
        )

        # Report
        report = pipeline.generate_report(
            research_id=research.id,
            title="Inflation Analysis",
            executive_summary="Summary",
        )

        # Validation
        validation = pipeline.validate_research(
            research_id=research.id,
            research_report_id=report.id,
            overall_status="Accurate",
            quality_score=0.85,
        )

        # Knowledge
        knowledge = pipeline.extract_knowledge(
            type="Relationship_Strength",
            subject="CPI",
            predicate="impacts",
            object="FedPolicy",
            confidence=0.85,
            source_references=[research.id],
        )

        # Cognitive
        assessment = pipeline.assess_cognitive(
            trader_id="trader-1",
            research_id=research.id,
            knowledge_score=0.8,
            reasoning_score=0.7,
        )

        # Verify all objects exist in repo
        assert repo.get(research.id) is not None
        assert repo.get(obs.id) is not None
        assert repo.get(hyp.id) is not None
        assert repo.get(ev.id) is not None
        assert repo.get(scenario.id) is not None
        assert repo.get(confidence.id) is not None
        assert repo.get(contradiction.id) is not None
        assert repo.get(report.id) is not None
        assert repo.get(validation.id) is not None
        assert repo.get(knowledge.id) is not None
        assert repo.get(assessment.id) is not None

        # Verify audit entries created
        audits = [o for o in repo.get_all() if isinstance(o, AuditEntry)]
        assert len(audits) >= 10

        # Verify deterministic: same pipeline inputs produce same objects
        repo2 = MemoryRepository()
        pipeline2 = ResearchPipeline(repo2)
        research2 = pipeline2.start_research("Will inflation fall?", "Monthly", "US")
        assert research2.id == research.id

    def test_evidence_registry_auto_created(self, pipeline, repo):
        """EvidenceRegistry should be auto-created when first evidence is added."""
        research = pipeline.start_research("Test", "Daily", "US")
        obs = pipeline.add_observation(research.id, "T", self._ts(), 1.0)
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test")
        pipeline.create_evidence(
            observation_id=obs.id, hypothesis_id=hyp.id,
            interpretation="test", research_id=research.id,
        )

        # Verify registry exists
        research = repo.get(research.id)
        assert research.evidence_registry_id is not None
        registry = repo.get(research.evidence_registry_id)
        assert registry is not None
        assert len(registry.evidence) > 0

    def test_hypothesis_auto_added_to_set(self, pipeline, repo):
        """HypothesisSet should be auto-created when hypothesis is added."""
        research = pipeline.start_research("Test", "Daily", "US")
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test hyp")
        research = repo.get(research.id)
        assert research.hypothesis_set_id is not None
        hs = repo.get(research.hypothesis_set_id)
        assert hs is not None
        assert hyp.id in [h.id for h in hs.hypotheses]

    def test_integrity_violation_raises_error(self, pipeline, repo):
        """Referencing a non-existent ID should raise ValueError."""
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.add_observation(
                research_id="nonexistent-research",
                source="T",
                timestamp=self._ts(),
                value=1.0,
            )


class TestSqlitePipeline:
    """Phase 4 — SQLite integration tests (Finding 10)."""

    @pytest.fixture(autouse=True)
    def sqlite_repo(self, tmp_path):
        db_path = str(tmp_path / "test_researchos.db")
        from researchos.storage.repository import ResearchRepository
        repo = ResearchRepository(db_path)
        return repo

    def test_full_pipeline_with_sqlite(self, sqlite_repo):
        """Full pipeline end-to-end with SQLite storage."""
        pipeline = ResearchPipeline(sqlite_repo)
        research = pipeline.start_research("Test Q", "Daily", "US")
        assert sqlite_repo.get(research.id) is not None

        obs = pipeline.add_observation(research.id, "MACRO:CPI", datetime(2024, 6, 1, tzinfo=timezone.utc), 3.2)
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test")
        ev = pipeline.create_evidence(obs.id, hyp.id, "test", research_id=research.id)
        pipeline.create_scenario(research.id, hyp.id, "Base", "Test", 0.5)
        pipeline.register_confidence(hyp.id, "Hypothesis", 0.7, research_id=research.id)
        pipeline.detect_contradiction(research.id, "Internal", "test", sides=[])
        report = pipeline.generate_report(research.id, "Report", "Summary")
        pipeline.validate_research(research.id, report.id, "Accurate", 0.8)
        pipeline.extract_knowledge("Relationship_Strength", "CPI", "impacts", "Fed", 0.7, source_references=[research.id])
        pipeline.assess_cognitive("trader-1", research.id, 0.8, 0.7)

        # All objects present
        assert sqlite_repo.get(research.id) is not None
        assert sqlite_repo.get(obs.id) is not None
        assert sqlite_repo.get(hyp.id) is not None
        assert sqlite_repo.get(ev.id) is not None

    def test_audit_chain_integrity_sqlite(self, sqlite_repo):
        """Audit chain verification passes with SQLite storage."""
        pipeline = ResearchPipeline(sqlite_repo)
        pipeline.start_research("Test Q")
        assert sqlite_repo.verify_audit_chain()

    def test_audit_entries_in_objects_table(self, sqlite_repo):
        """AuditEntry objects are discoverable via load_by_type (Finding 2 fix)."""
        pipeline = ResearchPipeline(sqlite_repo)
        pipeline.start_research("Test Q")

        entries = sqlite_repo.load_by_type("AuditEntry")
        assert len(entries) >= 1
        assert entries[0]["object_type"] == "AuditEntry"

    def test_load_audit_entries_method(self, sqlite_repo):
        """load_audit_entries() reads from audit_logs directly."""
        pipeline = ResearchPipeline(sqlite_repo)
        pipeline.start_research("Test Q")

        entries = sqlite_repo.load_audit_entries()
        assert len(entries) >= 1
        assert entries[0].entry_hash != ""

    def test_save_audit_entry_does_not_mutate_caller_object(self, sqlite_repo):
        """save_audit_entry() does not set previous_entry or entry_hash on caller's object (Finding 7 fix)."""
        from researchos.objects.process import AuditEntry

        entry = AuditEntry(actor="system", action="TEST", object_id="obj1", object_type="Test")
        prev_hash_before = entry.previous_entry
        entry_hash_before = entry.entry_hash

        sqlite_repo.save_audit_entry(entry)

        # Caller's object should not be mutated
        assert entry.previous_entry == prev_hash_before
        assert entry.entry_hash == entry_hash_before
        assert sqlite_repo.verify_audit_chain()

    def test_verify_audit_chain_honors_reasoning_chain_id(self, sqlite_repo):
        """verify_audit_chain() uses stored reasoning_chain_id and ontology_tags (Finding 3 fix)."""
        from researchos.objects.process import AuditEntry

        entry = AuditEntry(
            actor="system", action="TEST",
            object_id="obj1", object_type="Test",
            reasoning_chain_id="chain-123",
            ontology_tags=["tag1", "tag2"],
        )
        sqlite_repo.save_audit_entry(entry)
        assert sqlite_repo.verify_audit_chain()

    def test_rehydration_round_trip_sqlite(self, sqlite_repo):
        """Objects survive save → load → rehydration with SQLite."""
        pipeline = ResearchPipeline(sqlite_repo)
        research = pipeline.start_research("Test Q")
        obs = pipeline.add_observation(research.id, "MACRO:CPI", datetime(2024, 6, 1, tzinfo=timezone.utc), 3.2)

        loaded = sqlite_repo.load_object(obs.id)
        assert loaded is not None
        assert loaded.id == obs.id
        assert loaded.source == obs.source
        assert loaded.value == obs.value

    def test_deterministic_ids_sqlite(self, sqlite_repo):
        """Same pipeline inputs produce same IDs with SQLite."""
        pipeline1 = ResearchPipeline(sqlite_repo)
        r1 = pipeline1.start_research("Identical Q", "Daily", "US")

        from researchos.storage.repository import ResearchRepository
        repo2 = ResearchRepository(sqlite_repo.db_path + ".2")
        pipeline2 = ResearchPipeline(repo2)
        r2 = pipeline2.start_research("Identical Q", "Daily", "US")

        assert r1.id == r2.id
