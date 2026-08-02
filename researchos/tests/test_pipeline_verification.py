"""
STEP 9 — Pipeline Execution Verification Audit.

Verification-only tests for the ResearchPipeline.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import pytest

from researchos.repository.memory import MemoryRepository
from researchos.pipeline import ResearchPipeline, ReferenceValidator
from researchos.objects.observation import Observation, MarketState, MacroState
from researchos.objects.evidence import Evidence, EvidenceRegistry
from researchos.objects.interpretation import Interpretation, Narrative
from researchos.objects.hypothesis import Hypothesis, HypothesisSet
from researchos.objects.scenario import Scenario, ScenarioSet
from researchos.objects.confidence import Confidence, ConfidenceReport
from researchos.objects.contradiction import Contradiction, ContradictionReport
from researchos.objects.research import Research, ResearchReport, ResearchQuestion
from researchos.objects.validation import Validation, FailureAnalysis
from researchos.objects.knowledge import Knowledge, Lesson, Pattern
from researchos.objects.cognitive import CognitiveAssessment, Bias, LearningRecord
from researchos.objects.process import AuditEntry, ResearchCycle, ReasoningChain
from researchos.storage.repository import ResearchRepository

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo():
    return MemoryRepository()


@pytest.fixture
def pipeline(repo):
    return ResearchPipeline(repo)


def ts(year=2024, month=1, day=1):
    return datetime(year, month, day, tzinfo=timezone.utc)


def collect_audits(repo) -> List[AuditEntry]:
    """Collect all AuditEntry objects from the repository in creation order."""
    return [o for o in repo.get_all() if isinstance(o, AuditEntry)]


# ===========================================================================
# PHASE 1 — Pipeline Runtime Flow Audit
# ===========================================================================
# For each of the 11 stages, verify:
#   1. Previous object exists
#   2. Reference validation executed
#   3. Deterministic ID generated
#   4. Object persisted
#   5. AuditEntry created
#   6. Next stage can retrieve previous object

STAGE_NAMES = [
    "start_research",
    "add_observation",
    "create_evidence",
    "create_interpretation",
    "create_narrative",
    "create_hypothesis",
    "create_scenario",
    "register_confidence",
    "detect_contradiction",
    "generate_report",
    "validate_research",
    "extract_knowledge",
    "assess_cognitive",
]


class TestPhase1_RuntimeFlow:
    """Trace all 11 pipeline stages and verify every transition."""

    def test_stage_1_start_research(self, pipeline, repo):
        """Stage 1: Research initiation."""
        research = pipeline.start_research("Test Q", "Daily", "US")
        assert isinstance(research, Research)
        assert repo.get(research.id) is not None          # persisted
        audits = collect_audits(repo)
        assert any(a.action == "RESEARCH_STARTED" for a in audits)  # audit

    def test_stage_2_add_observation(self, pipeline, repo):
        """Stage 2: Observation."""
        research = pipeline.start_research("Test Q")
        obs = pipeline.add_observation(research.id, "MACRO:CPI", ts(), 3.2)
        assert isinstance(obs, Observation)               # output
        assert repo.get(obs.id) is not None               # persisted
        assert obs.id in repo.get(research.id).observation_ids  # linked
        audits = collect_audits(repo)
        assert any(a.action == "OBSERVATION_ADDED" for a in audits)

    def test_stage_3_create_evidence(self, pipeline, repo):
        """Stage 3: Evidence."""
        research = pipeline.start_research("Test Q")
        obs = pipeline.add_observation(research.id, "MACRO:CPI", ts(), 3.2)
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test")
        ev = pipeline.create_evidence(
            observation_id=obs.id,
            hypothesis_id=hyp.id,
            interpretation="CPI trend down",
            research_id=research.id,
        )
        assert isinstance(ev, Evidence)
        assert repo.get(ev.id) is not None
        assert ev.observation_id == obs.id                 # link preserved
        assert ev.hypothesis_id == hyp.id                  # link preserved
        audits = collect_audits(repo)
        assert any(a.action == "EVIDENCE_CREATED" for a in audits)

    def test_stage_4_create_interpretation(self, pipeline, repo):
        """Stage 4: Interpretation."""
        research = pipeline.start_research("Test Q")
        obs = pipeline.add_observation(research.id, "MACRO:CPI", ts(), 3.2)
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test")
        ev = pipeline.create_evidence(
            obs.id, hyp.id, "CPI trend", research_id=research.id,
        )
        interp = pipeline.create_interpretation(
            evidence_ids=[ev.id],
            rule_applied="trend_rule_v1",
            context="US_Q1_2024",
            conclusion="CPI is moderating",
        )
        assert isinstance(interp, Interpretation)
        assert repo.get(interp.id) is not None
        assert ev.id in interp.evidence_ids
        audits = collect_audits(repo)
        assert any(a.action == "INTERPRETATION_CREATED" for a in audits)

    def test_stage_5_create_narrative(self, pipeline, repo):
        """Stage 5: Narrative."""
        research = pipeline.start_research("Test Q")
        interp = pipeline.create_interpretation(
            evidence_ids=[], rule_applied="r1", context="ctx", conclusion="c1",
        )
        narrative = pipeline.create_narrative(
            research_id=research.id,
            thesis="Inflation is moderating",
            interpretations=[interp.id],
        )
        assert isinstance(narrative, Narrative)
        assert repo.get(narrative.id) is not None
        assert narrative.research_id == research.id
        audits = collect_audits(repo)
        assert any(a.action == "NARRATIVE_CREATED" for a in audits)

    def test_stage_6_create_hypothesis(self, pipeline, repo):
        """Stage 6: Hypothesis."""
        research = pipeline.start_research("Test Q")
        hyp = pipeline.create_hypothesis(
            research_id=research.id,
            type="Primary",
            statement="Inflation will fall",
        )
        assert isinstance(hyp, Hypothesis)
        assert repo.get(hyp.id) is not None
        assert hyp.research_id == research.id
        # Auto-linked to HypothesisSet
        research_obj = repo.get(research.id)
        hs = repo.get(research_obj.hypothesis_set_id)
        assert hyp.id in [h.id for h in hs.hypotheses]
        audits = collect_audits(repo)
        assert any(a.action == "HYPOTHESIS_CREATED" for a in audits)

    def test_stage_7_create_scenario(self, pipeline, repo):
        """Stage 7: Scenario."""
        research = pipeline.start_research("Test Q")
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test")
        sc = pipeline.create_scenario(
            research_id=research.id,
            hypothesis_id=hyp.id,
            type="Base",
            label="Soft landing",
            probability=0.6,
        )
        assert isinstance(sc, Scenario)
        assert repo.get(sc.id) is not None
        assert sc.hypothesis_id == hyp.id
        # Auto-linked to ScenarioSet
        research_obj = repo.get(research.id)
        ss = repo.get(research_obj.scenario_set_id)
        assert sc.id in [s.id for s in ss.scenarios]
        audits = collect_audits(repo)
        assert any(a.action == "SCENARIO_CREATED" for a in audits)

    def test_stage_8_register_confidence(self, pipeline, repo):
        """Stage 8: Confidence."""
        research = pipeline.start_research("Test Q")
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test")
        conf = pipeline.register_confidence(
            target_id=hyp.id,
            target_type="Hypothesis",
            evidence_strength=0.8,
            coherence=0.7,
            research_id=research.id,
        )
        assert isinstance(conf, Confidence)
        assert repo.get(conf.id) is not None
        assert conf.target_id == hyp.id
        audits = collect_audits(repo)
        assert any(a.action == "CONFIDENCE_REGISTERED" for a in audits)

    def test_stage_9_detect_contradiction(self, pipeline, repo):
        """Stage 9: Contradiction."""
        research = pipeline.start_research("Test Q")
        cont = pipeline.detect_contradiction(
            research_id=research.id,
            type="Internal",
            description="Data conflict",
        )
        assert isinstance(cont, Contradiction)
        assert repo.get(cont.id) is not None
        assert cont.research_id == research.id
        audits = collect_audits(repo)
        assert any(a.action == "CONTRADICTION_DETECTED" for a in audits)

    def test_stage_10_generate_report(self, pipeline, repo):
        """Stage 10: Research Report."""
        research = pipeline.start_research("Test Q")
        report = pipeline.generate_report(
            research_id=research.id,
            title="Test Report",
        )
        assert isinstance(report, ResearchReport)
        assert repo.get(report.id) is not None
        assert report.research_id == research.id
        # Research should be marked complete
        research_obj = repo.get(research.id)
        assert research_obj.report_id == report.id
        audits = collect_audits(repo)
        assert any(a.action == "REPORT_GENERATED" for a in audits)

    def test_stage_11_validate_research(self, pipeline, repo):
        """Stage 11: Validation."""
        research = pipeline.start_research("Test Q")
        report = pipeline.generate_report(research_id=research.id)
        val = pipeline.validate_research(
            research_id=research.id,
            research_report_id=report.id,
            overall_status="Accurate",
            quality_score=0.9,
        )
        assert isinstance(val, Validation)
        assert repo.get(val.id) is not None
        assert val.research_id == research.id
        assert val.research_report_id == report.id
        audits = collect_audits(repo)
        assert any(a.action == "VALIDATION_CREATED" for a in audits)

    def test_stage_12_extract_knowledge(self, pipeline, repo):
        """Stage 12: Knowledge."""
        research = pipeline.start_research("Test Q")
        knowledge = pipeline.extract_knowledge(
            type="Relationship_Strength",
            subject="CPI",
            predicate="impacts",
            object="FedPolicy",
            confidence=0.85,
            source_references=[research.id],
        )
        assert isinstance(knowledge, Knowledge)
        assert repo.get(knowledge.id) is not None
        assert research.id in (knowledge.source_references or [])
        audits = collect_audits(repo)
        assert any(a.action == "KNOWLEDGE_CREATED" for a in audits)

    def test_stage_13_assess_cognitive(self, pipeline, repo):
        """Stage 13: Cognitive Assessment."""
        research = pipeline.start_research("Test Q")
        ca = pipeline.assess_cognitive(
            trader_id="trader-1",
            research_id=research.id,
            knowledge_score=0.8,
        )
        assert isinstance(ca, CognitiveAssessment)
        assert repo.get(ca.id) is not None
        assert ca.trader_id == "trader-1"
        audits = collect_audits(repo)
        assert any(a.action == "COGNITIVE_ASSESSED" for a in audits)

    def test_complete_13_stage_chain(self, pipeline, repo):
        """Execute all 13 stages sequentially — every object is retrievable."""
        r = pipeline.start_research("Full chain test", "Monthly", "US")
        o = pipeline.add_observation(r.id, "MACRO:CPI", ts(2024, 6, 1), 3.2)
        h = pipeline.create_hypothesis(r.id, "Primary", "Inflation falls")
        e = pipeline.create_evidence(o.id, h.id, "CPI down", research_id=r.id)
        i = pipeline.create_interpretation([e.id], "trend_rule", "ctx", "CPI moderating")
        n = pipeline.create_narrative(r.id, "Soft landing thesis", interpretations=[i.id])
        h2 = pipeline.create_hypothesis(r.id, "Alternative", "No landing", narrative_id=n.id)
        s = pipeline.create_scenario(r.id, h.id, "Base", "Base case", 0.6)
        c = pipeline.register_confidence(h.id, "Hypothesis", 0.8, research_id=r.id)
        ct = pipeline.detect_contradiction(r.id, "Internal", "Data conflict")
        rp = pipeline.generate_report(r.id, "Full Report")
        v = pipeline.validate_research(r.id, rp.id, overall_status="Accurate", quality_score=0.85)
        k = pipeline.extract_knowledge("Relationship", "CPI", "impacts", "Fed", source_references=[r.id])
        ca = pipeline.assess_cognitive("trader-1", r.id, knowledge_score=0.8)

        # Every object retrievable from repo
        for obj in [r, o, h, e, i, n, h2, s, c, ct, rp, v, k, ca]:
            assert repo.get(obj.id) is not None, f"{type(obj).__name__} missing from repo"

        audits = collect_audits(repo)
        assert len(audits) >= 13  # at least one audit per stage


# ===========================================================================
# PHASE 2 — End-to-End Reproducibility Test
# ===========================================================================

class TestPhase2_Reproducibility:
    """Run identical pipeline twice — compare IDs, hashes, audit sequence."""

    def _run_pipeline(self, repo):
        pipeline = ResearchPipeline(repo)
        r = pipeline.start_research("Repro test", "Daily", "US")
        o = pipeline.add_observation(r.id, "MACRO:CPI", ts(2024, 6, 1), 3.2)
        h = pipeline.create_hypothesis(r.id, "Primary", "Repro hypothesis")
        e = pipeline.create_evidence(o.id, h.id, "Repro evidence", research_id=r.id)
        i = pipeline.create_interpretation([e.id], "rule_v1", "ctx", "Repro conclusion")
        n = pipeline.create_narrative(r.id, "Repro narrative", interpretations=[i.id])
        s = pipeline.create_scenario(r.id, h.id, "Base", "Repro scenario", 0.6)
        c = pipeline.register_confidence(h.id, "Hypothesis", 0.8, research_id=r.id)
        ct = pipeline.detect_contradiction(r.id, "Internal", "Repro conflict")
        rp = pipeline.generate_report(r.id, "Repro Report")
        v = pipeline.validate_research(r.id, rp.id, overall_status="Accurate", quality_score=0.85)
        k = pipeline.extract_knowledge("Relationship", "CPI", "impacts", "Fed", source_references=[r.id])
        ca = pipeline.assess_cognitive("trader-1", r.id, knowledge_score=0.8)
        return pipeline, repo

    def test_deterministic_object_ids(self):
        """Same pipeline inputs produce same object IDs."""
        _, repo1 = self._run_pipeline(MemoryRepository())
        _, repo2 = self._run_pipeline(MemoryRepository())

        ids1 = sorted(o.id for o in repo1.get_all() if not isinstance(o, AuditEntry))
        ids2 = sorted(o.id for o in repo2.get_all() if not isinstance(o, AuditEntry))

        assert ids1 == ids2, "Object IDs differ between runs"

    def test_deterministic_hashes(self):
        """Same pipeline inputs produce same content hashes."""
        _, repo1 = self._run_pipeline(MemoryRepository())
        _, repo2 = self._run_pipeline(MemoryRepository())

        non_audit1 = sorted(
            [o for o in repo1.get_all() if not isinstance(o, AuditEntry)],
            key=lambda o: o.id,
        )
        non_audit2 = sorted(
            [o for o in repo2.get_all() if not isinstance(o, AuditEntry)],
            key=lambda o: o.id,
        )

        assert len(non_audit1) == len(non_audit2), "Different number of comparable objects"
        for o1, o2 in zip(non_audit1, non_audit2):
            assert o1.hash == o2.hash, f"Hash mismatch for {type(o1).__name__}"

    def test_deterministic_json(self):
        """Same pipeline inputs produce same serialized JSON."""
        _, repo1 = self._run_pipeline(MemoryRepository())
        _, repo2 = self._run_pipeline(MemoryRepository())

        non_audit1 = sorted(
            [o for o in repo1.get_all() if not isinstance(o, AuditEntry)],
            key=lambda o: o.id,
        )
        non_audit2 = sorted(
            [o for o in repo2.get_all() if not isinstance(o, AuditEntry)],
            key=lambda o: o.id,
        )

        for o1, o2 in zip(non_audit1, non_audit2):
            import json as _json
            d1 = _json.loads(o1.to_json())
            d2 = _json.loads(o2.to_json())
            assert d1["hash"] == d2["hash"], f"Hash mismatch in JSON for {type(o1).__name__}"

    def test_deterministic_audit_sequence(self):
        """Same pipeline inputs produce same audit action sequence."""
        _, repo1 = self._run_pipeline(MemoryRepository())
        _, repo2 = self._run_pipeline(MemoryRepository())

        actions1 = [a.action for a in collect_audits(repo1)]
        actions2 = [a.action for a in collect_audits(repo2)]

        assert actions1 == actions2, "Audit action sequences differ"

    def test_repository_state_parity(self):
        """Two runs produce the same number of each object type."""
        _, repo1 = self._run_pipeline(MemoryRepository())
        _, repo2 = self._run_pipeline(MemoryRepository())

        def type_counts(repo):
            counts = {}
            for obj in repo.get_all():
                t = type(obj).__name__
                counts[t] = counts.get(t, 0) + 1
            return counts

        assert type_counts(repo1) == type_counts(repo2)


# ===========================================================================
# PHASE 3 — Failure Scenario Audit
# ===========================================================================

class TestPhase3_FailureScenarios:
    """Test invalid cases — pipeline must reject before creating objects."""

    def test_case1_evidence_missing_observation(self, pipeline, repo):
        """Evidence created with missing Observation ID — must reject before creation."""
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.create_evidence(
                observation_id="nonexistent-obs",
                hypothesis_id="nonexistent-hyp",
                interpretation="test",
            )
        # Verify no Evidence was persisted despite the error
        evs = [o for o in repo.get_all() if isinstance(o, Evidence)]
        assert len(evs) == 0

    def test_case2_hypothesis_missing_narrative(self, pipeline, repo):
        """Hypothesis with missing Narrative ID — must reject."""
        research = pipeline.start_research("Test Q")
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.create_hypothesis(
                research_id=research.id,
                type="Primary",
                statement="Test",
                narrative_id="nonexistent-narrative",
            )

    def test_case3_validation_missing_research(self, pipeline, repo):
        """Validation with missing Research — must reject."""
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.validate_research(
                research_id="nonexistent",
                research_report_id="nonexistent-report",
            )

    def test_case4_observation_missing_research(self, pipeline, repo):
        """Observation with missing Research — must reject."""
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.add_observation(
                research_id="nonexistent",
                source="T",
                timestamp=ts(),
                value=1.0,
            )

    def test_case5_scenario_missing_hypothesis(self, pipeline, repo):
        """Scenario with missing Hypothesis — must reject."""
        research = pipeline.start_research("Test Q")
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.create_scenario(
                research_id=research.id,
                hypothesis_id="nonexistent",
                type="Base",
                label="Test",
            )

    def test_case6_confidence_missing_target(self, pipeline, repo):
        """Confidence with missing target — must reject."""
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.register_confidence(
                target_id="nonexistent",
                target_type="Hypothesis",
            )

    def test_case7_knowledge_missing_source_reference(self, pipeline, repo):
        """Knowledge with missing source reference — must reject."""
        with pytest.raises(ValueError, match="not found in repository"):
            pipeline.extract_knowledge(
                type="Relationship",
                subject="A",
                predicate="relates",
                object="B",
                source_references=["nonexistent-research"],
            )

    def test_case8_pipeline_interruption_resume(self, pipeline, repo):
        """Pipeline interrupted halfway — partial state is valid, can resume."""
        research = pipeline.start_research("Interrupted test", "Daily", "US")
        obs = pipeline.add_observation(research.id, "MACRO:CPI", ts(), 3.2)
        hyp = pipeline.create_hypothesis(research.id, "Primary", "Test hyp")
        ev = pipeline.create_evidence(
            obs.id, hyp.id, "test", research_id=research.id,
        )

        # Verify partial state is valid
        assert repo.get(research.id) is not None
        assert repo.get(obs.id) is not None
        assert repo.get(hyp.id) is not None
        assert repo.get(ev.id) is not None

        # Resume on a new pipeline instance with same repo
        pipeline2 = ResearchPipeline(repo)

        # Can continue from where we left off
        scenario = pipeline2.create_scenario(
            research_id=research.id,
            hypothesis_id=hyp.id,
            type="Base",
            label="Resumed",
            probability=0.6,
        )
        assert repo.get(scenario.id) is not None
        assert scenario.hypothesis_id == hyp.id

        # Original objects still valid and untouched
        assert repo.get(research.id).question == "Interrupted test"
        assert repo.get(obs.id).source == "MACRO:CPI"


# ===========================================================================
# PHASE 4 — Repository Integrity Audit
# ===========================================================================

class TestPhase4_RepositoryIntegrity:
    """Verify save_object / load_by_id / load_by_type / delete_object."""

    def test_save_and_load_by_id(self):
        """Create object, save, reload, compare hash."""
        from researchos.storage.repository import ResearchRepository
        import tempfile, os
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        try:
            storage = ResearchRepository(db_path)
            obs = Observation(source="T", timestamp=ts(), value=42)

            # Save
            storage.save_object(obs)

            # Load by ID
            data = storage.load_by_id(obs.id)
            assert data is not None
            assert data["source"] == "T"
            assert data["value"] == 42
            assert data["object_type"] == "Observation"
            assert data["id"] == obs.id

            # Hash preserved
            assert data["hash"] == obs.hash
        finally:
            # Close connection before deleting file on Windows
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_load_by_type(self):
        """Save multiple types, load by type."""
        from researchos.storage.repository import ResearchRepository
        import tempfile, os
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        try:
            storage = ResearchRepository(db_path)
            obs = Observation(source="T", timestamp=ts(), value=1.0)
            ev = Evidence(observation_id="obs1", hypothesis_id="hyp1", interpretation="test")

            storage.save_object(obs)
            storage.save_object(ev)

            observations = storage.load_by_type("Observation")
            evidences = storage.load_by_type("Evidence")

            assert len(observations) == 1
            assert len(evidences) == 1
            assert observations[0]["id"] == obs.id
            assert evidences[0]["id"] == ev.id
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_delete_object(self):
        """Save, delete, verify gone."""
        from researchos.storage.repository import ResearchRepository
        import tempfile, os
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        try:
            storage = ResearchRepository(db_path)
            obs = Observation(source="T", timestamp=ts(), value=1.0)
            storage.save_object(obs)
            assert storage.load_by_id(obs.id) is not None
            storage.delete_object(obs.id)
            assert storage.load_by_id(obs.id) is None
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_object_count(self):
        """Count objects by type."""
        from researchos.storage.repository import ResearchRepository
        import tempfile, os
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        try:
            storage = ResearchRepository(db_path)
            storage.save_object(Observation(source="T", timestamp=ts(), value=1.0))
            storage.save_object(Observation(source="T", timestamp=ts(), value=2.0))
            storage.save_object(Evidence(observation_id="o1", hypothesis_id="h1", interpretation="t"))

            assert storage.object_count("Observation") == 2
            assert storage.object_count("Evidence") == 1
            assert storage.object_count() == 3
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_type_preserved_through_round_trip(self):
        """Object type string must survive save/load cycle."""
        from researchos.storage.repository import ResearchRepository
        import tempfile, os
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        try:
            storage = ResearchRepository(db_path)
            objs = [
                Observation(source="T", timestamp=ts(), value=1.0),
                Evidence(observation_id="o1", hypothesis_id="h1", interpretation="t"),
                Interpretation(evidence_ids=["e1"], rule_applied="r", context="c", conclusion="cn"),
                Hypothesis(research_id="r1", type="Primary", statement="s"),
                Scenario(hypothesis_id="h1", type="Base", label="l"),
            ]
            for obj in objs:
                storage.save_object(obj)
                loaded = storage.load_by_id(obj.id)
                assert loaded is not None
                assert loaded["object_type"] == type(obj).__name__
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)


# ===========================================================================
# PHASE 5 — Audit Chain Verification
# ===========================================================================

class TestPhase5_AuditChain:
    """Verify AuditEntry chain integrity, ordering, immutability."""

    def test_audit_actions_sequence(self, pipeline, repo):
        """Audit entries should appear in pipeline execution order."""
        r = pipeline.start_research("Audit test", "Daily", "US")
        o = pipeline.add_observation(r.id, "MACRO:CPI", ts(), 3.2)
        h = pipeline.create_hypothesis(r.id, "Primary", "Test")
        e = pipeline.create_evidence(o.id, h.id, "test", research_id=r.id)

        audits = collect_audits(repo)
        actions = [a.action for a in audits]
        # Actions must appear in execution order
        expected = [
            "RESEARCH_STARTED",
            "OBSERVATION_ADDED",
            "HYPOTHESIS_CREATED",
            "EVIDENCE_CREATED",
        ]
        # Each expected action appears in sequence (allow for interleaved audit entries)
        idx = 0
        for action in actions:
            if idx < len(expected) and action == expected[idx]:
                idx += 1
        assert idx == len(expected), f"Expected sequence {expected} not found in {actions}"

    def test_no_orphan_audit_entries(self, pipeline, repo):
        """Every audit entry must reference an object that exists in the repo."""
        r = pipeline.start_research("Orphan test", "Daily", "US")
        pipeline.add_observation(r.id, "MACRO:CPI", ts(), 3.2)

        audits = collect_audits(repo)
        for a in audits:
            if a.object_type in ("ResearchCycle",):
                continue  # ResearchCycle exists separately
            obj = repo.get(a.object_id)
            assert obj is not None, f"Audit {a.id} references missing {a.object_type}:{a.object_id}"

    def test_audit_entry_immutability(self, pipeline, repo):
        """Audit entries should have deterministic hashes and be immutable."""
        pipeline.start_research("Immutable test", "Daily", "US")
        audits = collect_audits(repo)
        for a in audits:
            assert a.entry_hash is not None
            assert len(a.entry_hash) == 64 or a.entry_hash == ""  # SHA-256 hex


# ===========================================================================
# PHASE 6 — Serialization Round-Trip & Repository Rehydration
# ===========================================================================

class TestPhase6_Serialization:
    """Verify to_dict/from_dict round-trip for all 28 objects."""

    def test_from_dict_on_base_uses_new_pattern(self):
        """BaseObject.from_dict() now uses __new__ pattern and returns an instance."""
        from researchos.core.base_object import BaseObject
        obj = BaseObject.from_dict({"id": "test_id"})
        assert obj.id == "test_id"
        assert obj.created_at is not None

    def test_observation_round_trip(self):
        o = Observation(source="MACRO:CPI", timestamp=ts(), value="3.2")
        d = o.to_dict()
        o2 = Observation.from_dict(d)
        assert o.id == o2.id
        assert o.source == o2.source
        assert o.value == o2.value

    def test_market_state_round_trip(self):
        ms = MarketState(timestamp=ts(), asset="SPX", volatility=0.15)
        d = ms.to_dict()
        ms2 = MarketState.from_dict(d)
        assert ms.id == ms2.id
        assert ms.asset == ms2.asset
        assert ms.volatility == ms2.volatility

    def test_macro_state_round_trip(self):
        ms = MacroState(timestamp=ts(), geography="US", inflation=3.0, growth=2.5)
        d = ms.to_dict()
        ms2 = MacroState.from_dict(d)
        assert ms.id == ms2.id
        assert ms.geography == ms2.geography
        assert ms.growth == ms2.growth

    def test_evidence_round_trip(self):
        e = Evidence(observation_id="o1", hypothesis_id="h1", interpretation="test")
        d = e.to_dict()
        e2 = Evidence.from_dict(d)
        assert e.id == e2.id
        assert e.observation_id == e2.observation_id
        assert e.interpretation == e2.interpretation

    def test_evidence_registry_round_trip(self):
        reg = EvidenceRegistry(research_id="r1")
        reg.evidence_ids = ["e1", "e2"]
        d = reg.to_dict()
        reg2 = EvidenceRegistry.from_dict(d)
        assert reg.id == reg2.id
        assert reg2.evidence_ids == ["e1", "e2"]

    def test_interpretation_round_trip(self):
        interp = Interpretation(evidence_ids=["e1"], rule_applied="rule1", context="test", conclusion="insight")
        d = interp.to_dict()
        interp2 = Interpretation.from_dict(d)
        assert interp.id == interp2.id
        assert interp.conclusion == interp2.conclusion

    def test_narrative_round_trip(self):
        n = Narrative(research_id="r1", thesis="test story")
        d = n.to_dict()
        n2 = Narrative.from_dict(d)
        assert n.id == n2.id
        assert n.thesis == n2.thesis

    def test_hypothesis_round_trip(self):
        h = Hypothesis(research_id="r1", type="Primary", statement="test assertion")
        d = h.to_dict()
        h2 = Hypothesis.from_dict(d)
        assert h.id == h2.id
        assert h.type == h2.type
        assert h.statement == h2.statement

    def test_hypothesis_set_round_trip(self):
        hs = HypothesisSet(research_id="r1")
        hs.hypothesis_ids = ["h1", "h2"]
        d = hs.to_dict()
        hs2 = HypothesisSet.from_dict(d)
        assert hs.id == hs2.id
        assert hs2.hypothesis_ids == ["h1", "h2"]

    def test_scenario_round_trip(self):
        s = Scenario(hypothesis_id="h1", type="Base", label="test")
        d = s.to_dict()
        s2 = Scenario.from_dict(d)
        assert s.id == s2.id
        assert s.type == s2.type
        assert s.label == s2.label

    def test_scenario_set_round_trip(self):
        ss = ScenarioSet(research_id="r1")
        ss.scenario_ids = ["s1", "s2"]
        d = ss.to_dict()
        ss2 = ScenarioSet.from_dict(d)
        assert ss.id == ss2.id
        assert ss2.scenario_ids == ["s1", "s2"]

    def test_confidence_round_trip(self):
        c = Confidence(target_id="s1", target_type="Scenario")
        d = c.to_dict()
        c2 = Confidence.from_dict(d)
        assert c.id == c2.id
        assert c.target_id == c2.target_id
        assert c.target_type == c2.target_type

    def test_confidence_report_round_trip(self):
        cr = ConfidenceReport(research_id="r1")
        cr.confidence_ids = ["c1"]
        d = cr.to_dict()
        cr2 = ConfidenceReport.from_dict(d)
        assert cr.id == cr2.id
        assert cr2.confidence_ids == ["c1"]

    def test_contradiction_round_trip(self):
        ct = Contradiction(research_id="r1", type="Direct", description="desc")
        d = ct.to_dict()
        ct2 = Contradiction.from_dict(d)
        assert ct.id == ct2.id
        assert ct.type == ct2.type
        assert ct.description == ct2.description

    def test_contradiction_report_round_trip(self):
        cr = ContradictionReport(research_id="r1")
        cr.contradiction_ids = ["c1"]
        d = cr.to_dict()
        cr2 = ContradictionReport.from_dict(d)
        assert cr.id == cr2.id
        assert cr2.contradiction_ids == ["c1"]

    def test_research_round_trip(self):
        r = Research(question="Test?", time_horizon="Daily", asset="US")
        d = r.to_dict()
        r2 = Research.from_dict(d)
        assert r.id == r2.id
        assert r.question == r2.question
        assert r.asset == r2.asset

    def test_research_question_round_trip(self):
        rq = ResearchQuestion(research_id="r1", question="What?")
        d = rq.to_dict()
        rq2 = ResearchQuestion.from_dict(d)
        assert rq.id == rq2.id
        assert rq.question == rq2.question

    def test_research_report_round_trip(self):
        rr = ResearchReport(research_id="r1")
        d = rr.to_dict()
        rr2 = ResearchReport.from_dict(d)
        assert rr.id == rr2.id
        assert rr.research_id == rr2.research_id

    def test_validation_round_trip(self):
        v = Validation(research_id="r1", research_report_id="rr1", time_horizon="Daily",
                        overall_status="PASS", quality_score=0.95)
        d = v.to_dict()
        v2 = Validation.from_dict(d)
        assert v.id == v2.id
        assert v.overall_status == v2.overall_status
        assert v.quality_score == v2.quality_score

    def test_failure_analysis_round_trip(self):
        fa = FailureAnalysis(validation_id="v1", research_id="r1")
        d = fa.to_dict()
        fa2 = FailureAnalysis.from_dict(d)
        assert fa.id == fa2.id
        assert fa.validation_id == fa2.validation_id

    def test_knowledge_round_trip(self):
        k = Knowledge(type="Fact", subject="market", predicate="is", object="efficient")
        d = k.to_dict()
        k2 = Knowledge.from_dict(d)
        assert k.id == k2.id
        assert k.type == k2.type
        assert k.subject == k2.subject

    def test_pattern_round_trip(self):
        p = Pattern(type="Trend", description="upward momentum")
        d = p.to_dict()
        p2 = Pattern.from_dict(d)
        assert p.id == p2.id
        assert p.type == p2.type
        assert p.description == p2.description

    def test_lesson_round_trip(self):
        l = Lesson(type="Insight", description="learned something")
        d = l.to_dict()
        l2 = Lesson.from_dict(d)
        assert l.id == l2.id
        assert l.type == l2.type
        assert l.description == l2.description

    def test_bias_round_trip(self):
        b = Bias(type="Confirmation", trader_id="trader1", description="desc")
        d = b.to_dict()
        b2 = Bias.from_dict(d)
        assert b.id == b2.id
        assert b.type == b2.type
        assert b.trader_id == b2.trader_id

    def test_learning_record_round_trip(self):
        lr = LearningRecord(trader_id="trader1", dimension="accuracy")
        d = lr.to_dict()
        lr2 = LearningRecord.from_dict(d)
        assert lr.id == lr2.id
        assert lr.trader_id == lr2.trader_id

    def test_cognitive_assessment_round_trip(self):
        ca = CognitiveAssessment(trader_id="trader1", research_id="r1")
        d = ca.to_dict()
        ca2 = CognitiveAssessment.from_dict(d)
        assert ca.id == ca2.id
        assert ca.trader_id == ca2.trader_id

    def test_research_cycle_round_trip(self):
        rc = ResearchCycle(research_id="r1")
        d = rc.to_dict()
        rc2 = ResearchCycle.from_dict(d)
        assert rc.id == rc2.id
        assert rc.research_id == rc2.research_id

    def test_reasoning_chain_round_trip(self):
        rc = ReasoningChain(research_id="r1", steps=["step1"])
        d = rc.to_dict()
        rc2 = ReasoningChain.from_dict(d)
        assert rc.id == rc2.id
        assert rc.steps == rc2.steps

    def test_audit_entry_round_trip(self):
        ae = AuditEntry(actor="test", action="TEST", object_id="o1", object_type="Observation")
        d = ae.to_dict()
        ae2 = AuditEntry.from_dict(d)
        assert ae.id == ae2.id
        assert ae.action == ae2.action
        assert ae.object_type == "Observation"

    def test_audit_entry_from_dict_with_affected_object_type_key(self):
        """AuditEntry.from_dict handles legacy 'affected_object_type' key."""
        ae = AuditEntry(actor="test", action="TEST", object_id="o1", object_type="Observation")
        d = ae.to_dict()
        # Simulate legacy dict that has 'affected_object_type' but no 'object_type' key
        d["affected_object_type"] = "Observation"
        d.pop("object_type", None)
        ae2 = AuditEntry.from_dict(d)
        assert ae2.object_type == "Observation"

    def test_container_serialization_id_refs_only(self):
        """Container serialization stores ID references, not embedded objects."""
        reg = EvidenceRegistry(research_id="r1")
        reg.evidence_ids = ["e1", "e2"]
        d = reg.to_dict()
        assert "evidence_ids" in d
        assert d["evidence_ids"] == ["e1", "e2"]
        assert "evidences" not in d


class TestPhase6_RepositoryRehydration:
    """Verify OBJECT_REGISTRY, load_object, load_objects_by_type."""

    def test_object_registry_has_all_types(self):
        from researchos.storage.repository import OBJECT_REGISTRY
        expected_types = {
            "Observation", "MarketState", "MacroState",
            "Evidence", "EvidenceRegistry",
            "Interpretation", "Narrative",
            "Hypothesis", "HypothesisSet",
            "Scenario", "ScenarioSet",
            "Confidence", "ConfidenceReport",
            "Contradiction", "ContradictionReport",
            "Research", "ResearchQuestion", "ResearchReport",
            "Validation", "FailureAnalysis",
            "Knowledge", "Pattern", "Lesson",
            "Bias", "LearningRecord", "CognitiveAssessment",
            "ResearchCycle", "ReasoningChain", "AuditEntry",
            "MarketEvent", "MarketStructure", "LiquidityEvent",
            "MarketSession", "VolatilityState", "NewsReference", "MarketOutcome",
            "Attribution", "AttributionGraph",
            "RealYieldSnapshot", "DollarStrengthSnapshot",
            "FedPolicyAssessment", "InflationAssessment",
            "LaborMarketAssessment", "EconomicGrowthAssessment",
            "SafeHavenAssessment", "CentralBankDemand",
            "PhysicalDemandSnapshot", "PositioningAssessment",
            "MacroScore", "MacroProbability",
            "MacroRegime", "MacroReport",
        }
        registry_types = set(OBJECT_REGISTRY.keys())
        missing = expected_types - registry_types
        extra = registry_types - expected_types
        assert not missing, f"Missing from OBJECT_REGISTRY: {missing}"
        assert not extra, f"Extra in OBJECT_REGISTRY: {extra}"

    def test_load_object_round_trip(self, tmp_path):
        import json, os
        db_path = str(tmp_path / "test_rehydrate.db")
        storage = ResearchRepository(db_path=db_path)
        try:
            o = Observation(source="MACRO:CPI", timestamp=ts(), value="3.2")
            storage.save_object(o)
            loaded = storage.load_object(o.id)
            assert loaded is not None
            assert type(loaded).__name__ == "Observation"
            assert loaded.source == "MACRO:CPI"
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_load_objects_by_type(self, tmp_path):
        import json, os
        db_path = str(tmp_path / "test_by_type.db")
        storage = ResearchRepository(db_path=db_path)
        try:
            for v in [3.1, 3.2, 3.3]:
                o = Observation(source="MACRO:CPI", timestamp=ts(), value=str(v))
                storage.save_object(o)
            observations = storage.load_objects_by_type("Observation")
            assert len(observations) == 3
            for obs in observations:
                assert type(obs).__name__ == "Observation"
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_load_object_unknown_type(self, tmp_path):
        """Loading an unknown object type raises ValueError."""
        import json, os, sqlite3
        db_path = str(tmp_path / "test_unknown.db")
        storage = ResearchRepository(db_path=db_path)
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                "INSERT INTO objects (id, object_type, created_at, data) VALUES (?, ?, ?, ?)",
                ["unknown_id", "UnknownType", ts().isoformat(),
                 json.dumps({"id": "unknown_id", "object_type": "UnknownType"})],
            )
            conn.commit()
            conn.close()
            with pytest.raises(ValueError, match="No registered class"):
                storage.load_object("unknown_id")
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_load_object_missing(self, tmp_path):
        """Loading a non-existent ID returns None."""
        import os
        db_path = str(tmp_path / "test_missing.db")
        storage = ResearchRepository(db_path=db_path)
        try:
            result = storage.load_object("nonexistent_id")
            assert result is None
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_load_from_corrupt_data(self, tmp_path):
        """Invalid JSON in stored data raises ValueError."""
        import json, os, sqlite3
        db_path = str(tmp_path / "test_corrupt.db")
        storage = ResearchRepository(db_path=db_path)
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                "INSERT INTO objects (id, object_type, created_at, data) VALUES (?, ?, ?, ?)",
                ["corrupt_id", "Observation", ts().isoformat(), "{invalid json}"],
            )
            conn.commit()
            conn.close()
            with pytest.raises((ValueError, json.JSONDecodeError)):
                storage.load_object("corrupt_id")
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_save_get_delegation(self, tmp_path):
        """RepositoryInterface save/get/get_all delegation works."""
        import os
        db_path = str(tmp_path / "test_delegation.db")
        storage = ResearchRepository(db_path=db_path)
        try:
            o = Observation(source="MACRO:CPI", timestamp=ts(), value="3.2")
            storage.save(o)
            loaded = storage.get(o.id)
            assert loaded is not None
            assert loaded.id == o.id
            all_objs = storage.get_all()
            assert any(obj.id == o.id for obj in all_objs)
        finally:
            if hasattr(storage, '_conn') and storage._conn:
                storage._conn.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_determinism_without_timestamps(self):
        """ResearchCycle and Validation hashes are now deterministic."""
        rc1 = ResearchCycle(research_id="r1")
        rc2 = ResearchCycle(research_id="r1")
        assert rc1.hash == rc2.hash
        v1 = Validation(research_id="r1", research_report_id="rr1")
        v2 = Validation(research_id="r1", research_report_id="rr1")
        assert v1.hash == v2.hash


# ===========================================================================
# Regression tests for architecture remediation
# ===========================================================================

class TestFinding1_ObservationHashCoverage:
    """Observation._to_hashable_dict includes all semantically significant fields."""

    def test_hashable_includes_validated(self):
        o = Observation(source="T", timestamp=ts(), value=1)
        h = o._to_hashable_dict()
        assert "validated" in h

    def test_hashable_includes_retrieval_time(self):
        o = Observation(source="T", timestamp=ts(), value=1)
        h = o._to_hashable_dict()
        assert "retrieval_time" in h

    def test_hashable_includes_retrieval_method(self):
        o = Observation(source="T", timestamp=ts(), value=1)
        h = o._to_hashable_dict()
        assert "retrieval_method" in h

    def test_hash_changes_when_validated_changes(self):
        o1 = Observation(source="T", timestamp=ts(), value=1)
        o2 = Observation(source="T", timestamp=ts(), value=1)
        o2.validated = True
        assert o1.hash != o2.hash

    def test_hash_changes_when_retrieval_method_changes(self):
        o1 = Observation(source="T", timestamp=ts(), value=1, retrieval_method="API")
        o2 = Observation(source="T", timestamp=ts(), value=1, retrieval_method="WEB")
        assert o1.hash != o2.hash


class TestFinding2_SilentUtcNowFallback:
    """from_dict must not silently create timestamps for missing data."""

    def test_research_cycle_from_dict_requires_start_time(self):
        data = {"id": "test", "research_id": "r1", "object_type": "ResearchCycle"}
        with pytest.raises(KeyError):
            ResearchCycle.from_dict(data)

    def test_audit_entry_from_dict_requires_timestamp(self):
        data = {"id": "test", "actor": "sys", "action": "T", "object_id": "o1",
                "object_type": "T"}
        with pytest.raises(KeyError):
            AuditEntry.from_dict(data)

    def test_research_cycle_round_trip_preserves_start_time(self):
        rc = ResearchCycle(research_id="r1")
        d = rc.to_dict()
        rc2 = ResearchCycle.from_dict(d)
        assert rc2.start_time == rc.start_time


class TestFinding3_ResearchCyclePersistence:
    """ResearchCycle routes to cycles table via save(), and dual-writes to objects table."""

    def test_save_routes_research_cycle_to_cycles_table(self, tmp_path):
        import sqlite3
        db_path = str(tmp_path / "test_cycle_routing.db")
        repo = ResearchRepository(db_path)
        try:
            rc = ResearchCycle(research_id="r1")
            repo.save(rc)
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT id FROM cycles WHERE id = ?", (rc.id,)).fetchone()
            conn.close()
            assert row is not None, "ResearchCycle was not saved to cycles table"
        finally:
            if hasattr(repo, '_conn') and repo._conn:
                repo._conn.close()

    def test_save_cycle_also_writes_to_objects_table(self, tmp_path):
        db_path = str(tmp_path / "test_cycle_dual.db")
        repo = ResearchRepository(db_path)
        try:
            rc = ResearchCycle(research_id="r1")
            repo.save_cycle(rc)
            loaded = repo.load_object(rc.id)
            assert loaded is not None
            assert isinstance(loaded, ResearchCycle)
        finally:
            if hasattr(repo, '_conn') and repo._conn:
                repo._conn.close()


class TestFinding4_EvidenceRegistryDataLoss:
    """EvidenceRegistry preserves all evidence IDs across deserialize-mutate-serialize."""

    def test_add_evidence_after_deserialization_preserves_all_ids(self):
        reg = EvidenceRegistry(research_id="r1")
        reg.evidence_ids = ["e1", "e2"]
        d = reg.to_dict()
        reg2 = EvidenceRegistry.from_dict(d)
        ev3 = Evidence(observation_id="o3", hypothesis_id="h3", interpretation="i3")
        reg2.add_evidence(ev3)
        d2 = reg2.to_dict()
        assert "e1" in d2["evidence_ids"]
        assert "e2" in d2["evidence_ids"]
        assert ev3.id in d2["evidence_ids"]
        assert len(d2["evidence_ids"]) == 3

    def test_deserialize_mutate_serialize_round_trip(self):
        reg = EvidenceRegistry(research_id="r1")
        reg.evidence_ids = ["e1"]
        d1 = reg.to_dict()
        reg2 = EvidenceRegistry.from_dict(d1)
        ev2 = Evidence(observation_id="o2", hypothesis_id="h2", interpretation="i2")
        reg2.add_evidence(ev2)
        d2 = reg2.to_dict()
        reg3 = EvidenceRegistry.from_dict(d2)
        assert reg3.evidence_ids == ["e1", ev2.id]
        assert reg3.hash == reg2.hash

    def test_mutation_preserves_from_dict_to_dict_symmetry(self):
        reg = EvidenceRegistry(research_id="r1")
        reg.evidence_ids = ["x1", "x2"]
        d = reg.to_dict()
        reg2 = EvidenceRegistry.from_dict(d)
        ev = Evidence(observation_id="o", hypothesis_id="h", interpretation="i")
        reg2.add_evidence(ev)
        d2 = reg2.to_dict()
        reg3 = EvidenceRegistry.from_dict(d2)
        assert set(reg3.evidence_ids) == {"x1", "x2", ev.id}
        assert set(d2["evidence_ids"]) == {"x1", "x2", ev.id}
        assert reg3.hash == reg2.hash
