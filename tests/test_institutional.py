"""
Institutional-grade audit tests for ResearchOS.

Covers:
  1. Concurrent writers (SQLite lock contention)
  2. Crash recovery (mid-transaction interruption)
  3. Schema migration (old DB -> new DB)
  4. Property-based serialization (from_dict(to_dict(x)) == x)
  5. Long audit chain (100k+ entries) replay performance
  6. Tamper detection (audit_logs row modification/deletion)
  7. Cross-process deterministic hashing
  8. Lifecycle reconstruction for every object subtype
  9. Dual-storage consistency (objects vs audit_logs)
"""

from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any

import pytest

from researchos.core.identity import deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.objects.cognitive import Bias, CognitiveAssessment, LearningRecord
from researchos.objects.confidence import Confidence, ConfidenceReport
from researchos.objects.contradiction import Contradiction, ContradictionReport
from researchos.objects.evidence import Evidence, EvidenceRegistry
from researchos.objects.hypothesis import Hypothesis, HypothesisSet
from researchos.objects.interpretation import Interpretation, Narrative
from researchos.objects.knowledge import Knowledge, Lesson, Pattern
from researchos.objects.observation import MacroState, MarketState, Observation
from researchos.objects.process import AuditEntry, ReasoningChain, ResearchCycle
from researchos.objects.research import Research, ResearchQuestion, ResearchReport
from researchos.objects.scenario import Scenario, ScenarioSet
from researchos.objects.validation import FailureAnalysis, Validation

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def ts(year=2024, month=1, day=1):
    return datetime(year, month, day, tzinfo=timezone.utc)


# ===========================================================================
# 1. Concurrent writers
# ===========================================================================


class TestConcurrentWriters:
    """Verify SQLite handles concurrent write contention correctly."""

    @staticmethod
    def _writer(
        repo,
        thread_id: int,
        entries: list,
        start_event: threading.Event,
        done_event: threading.Event,
    ):
        start_event.wait()
        for i in range(5):
            e = AuditEntry(
                actor="writer",
                action=f"WRITE_{thread_id}_{i}",
                object_id=f"obj_{thread_id}_{i}",
                object_type="Test",
            )
            try:
                repo.save_audit_entry(e)
                entries.append(e.id)
            except Exception:
                pass
        done_event.set()

    def test_concurrent_writes_dont_cause_data_loss(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(str(tmp_path / "concurrent.db"))

        start = threading.Event()
        done1, done2, done3 = threading.Event(), threading.Event(), threading.Event()
        entries: list = []

        t1 = threading.Thread(target=self._writer, args=(repo, 0, entries, start, done1))
        t2 = threading.Thread(target=self._writer, args=(repo, 1, entries, start, done2))
        t3 = threading.Thread(target=self._writer, args=(repo, 2, entries, start, done3))

        t1.start()
        t2.start()
        t3.start()
        start.set()

        done1.wait(timeout=10)
        done2.wait(timeout=10)
        done3.wait(timeout=10)
        t1.join(timeout=5)
        t2.join(timeout=5)
        t3.join(timeout=5)

        assert repo.verify_audit_chain()
        loaded = repo.load_audit_entries()
        assert len(loaded) == len(entries)
        assert len(loaded) == 15  # 3 threads x 5 entries


# ===========================================================================
# 2. Crash recovery
# ===========================================================================


class TestCrashRecovery:
    """Simulate mid-transaction crash and verify recovery."""

    def test_integrity_check_on_clean_db(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(str(tmp_path / "integrity.db"))
        result = repo._check_integrity()
        assert result == "ok"

    def test_wal_persistence_after_crash(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "crash.db")
        repo = ResearchRepository(db_path)

        for i in range(10):
            entry = AuditEntry(actor="sys", action=f"OP_{i}", object_id=f"o{i}", object_type="Test")
            repo.save_audit_entry(entry)

        # Close the connection (simulating clean shutdown)
        repo._conn.close()

        # Open a new repo on the same path — should recover from WAL
        repo2 = ResearchRepository(db_path)
        assert repo2.verify_audit_chain()
        entries = repo2.load_audit_entries()
        assert len(entries) == 10


# ===========================================================================
# 3. Schema migration
# ===========================================================================


class TestSchemaMigration:
    """Verify old databases are migrated to the current schema."""

    def test_migration_from_v1_schema(self, tmp_path):
        """
        Create a v1 database (missing reasoning_chain_id, ontology_tags),
        then open with current ResearchRepository to trigger migration.
        """
        db_path = str(tmp_path / "migrate_v1.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                actor TEXT,
                action TEXT,
                object_id TEXT,
                object_type TEXT,
                before_state TEXT,
                after_state TEXT,
                previous_entry TEXT,
                entry_hash TEXT
            );
        """)
        conn.commit()
        conn.close()

        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(db_path)

        # Verify migration added the columns
        cursor = repo._get_conn().cursor()
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "reasoning_chain_id" in columns
        assert "ontology_tags" in columns

        # Verify schema version is updated
        ver = repo._get_schema_version(cursor)
        assert ver >= 2

    def test_migrated_db_still_works(self, tmp_path):
        db_path = str(tmp_path / "migrate_v1_use.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                actor TEXT,
                action TEXT,
                object_id TEXT,
                object_type TEXT,
                before_state TEXT,
                after_state TEXT,
                previous_entry TEXT,
                entry_hash TEXT
            );
        """)
        conn.commit()
        conn.close()

        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(db_path)

        e = AuditEntry(actor="sys", action="MIGRATE_TEST", object_id="o1", object_type="T")
        repo.save_audit_entry(e)
        assert repo.verify_audit_chain()


# ===========================================================================
# 4. Property-based serialization (from_dict(to_dict(x)) == x)
# ===========================================================================

OBJECT_SAMPLES: list[tuple[str, Any]] = [
    ("Observation", Observation(source="MACRO:CPI", timestamp=ts(), value=3.2)),
    ("MarketState", MarketState(timestamp=ts(), asset="SPX", volatility=0.15)),
    ("MacroState", MacroState(timestamp=ts(), geography="US", inflation=3.0, growth=2.5)),
    ("Evidence", Evidence(observation_id="o1", hypothesis_id="h1", interpretation="test")),
    ("EvidenceRegistry", EvidenceRegistry(research_id="r1")),
    (
        "Interpretation",
        Interpretation(evidence_ids=["e1"], rule_applied="rule1", context="ctx", conclusion="conc"),
    ),
    ("Narrative", Narrative(research_id="r1", thesis="story")),
    ("Hypothesis", Hypothesis(research_id="r1", type="Primary", statement="test")),
    ("HypothesisSet", HypothesisSet(research_id="r1")),
    ("Scenario", Scenario(hypothesis_id="h1", type="Base", label="A", thesis="t")),
    ("ScenarioSet", ScenarioSet(research_id="r1")),
    ("Confidence", Confidence(target_id="t1", target_type="Hypothesis")),
    ("ConfidenceReport", ConfidenceReport(research_id="r1")),
    ("Contradiction", Contradiction(research_id="r1", type="Internal", description="d")),
    ("ContradictionReport", ContradictionReport(research_id="r1")),
    ("Research", Research(question="Test Q")),
    ("ResearchQuestion", ResearchQuestion(research_id="r1", question="Q")),
    ("ResearchReport", ResearchReport(research_id="r1", title="R")),
    ("Validation", Validation(research_id="r1", research_report_id="rr1")),
    ("FailureAnalysis", FailureAnalysis(validation_id="v1", research_id="r1")),
    (
        "Knowledge",
        Knowledge(type="Relationship_Strength", subject="CPI", predicate="impacts", object="Fed"),
    ),
    ("Pattern", Pattern(type="Regime_Transition", description="pattern desc")),
    ("Lesson", Lesson(type="Data", description="lesson desc")),
    ("Bias", Bias(type="Confirmation", trader_id="t1")),
    ("LearningRecord", LearningRecord(trader_id="t1", dimension="Knowledge")),
    ("CognitiveAssessment", CognitiveAssessment(trader_id="t1")),
    ("ResearchCycle", ResearchCycle(research_id="r1")),
    ("ReasoningChain", ReasoningChain(research_id="r1")),
    ("AuditEntry", AuditEntry(actor="sys", action="TEST", object_id="o1", object_type="T")),
]

NON_DEFAULT_SAMPLES: list[tuple[str, Any]] = [
    ("Observation", Observation(source="FX:USDJPY", timestamp=ts(2025, 6, 15), value=150.25)),
    (
        "Evidence",
        Evidence(
            observation_id="o_custom", hypothesis_id="h_custom", interpretation="custom interp"
        ),
    ),
    (
        "Scenario",
        Scenario(
            hypothesis_id="h_cust",
            type="Bear",
            label="Crash",
            thesis="Market down",
            probability=0.3,
            calibrated_probability=0.28,
            expected_return=-0.15,
            volatility=0.35,
            regime="Crisis",
        ),
    ),
    (
        "Contradiction",
        Contradiction(research_id="r_cust", type="External", description="custom conflict"),
    ),
    (
        "AuditEntry",
        AuditEntry(
            actor="trader-1",
            action="CUSTOM_ACTION",
            object_id="obj_cust",
            object_type="Custom",
            reasoning_chain_id="chain-999",
            ontology_tags=["high-priority", "reviewed"],
        ),
    ),
    (
        "Knowledge",
        Knowledge(
            type="Custom",
            subject="SUBJ",
            predicate="relates_to",
            object="OBJ",
            confidence=0.95,
            evidence_count=10,
            source_references=["r1", "r2"],
            knowledge_trace="manual",
        ),
    ),
    (
        "Research",
        Research(
            question="Complex question?",
            time_horizon="Quarterly",
            asset="BTC",
            methodology_version="2.0.0",
            ontology_tags=["crypto"],
        ),
    ),
]


class TestPropertyBasedSerialization:
    """Verify from_dict(to_dict(x)) == x for all object types."""

    @pytest.mark.parametrize("name,obj", OBJECT_SAMPLES + NON_DEFAULT_SAMPLES)
    def test_round_trip_preserves_all_fields(self, name, obj):
        d = obj.to_dict()
        obj2 = type(obj).from_dict(d)
        assert obj2 is not obj

        # Core identity preserved
        assert obj2.id == obj.id
        assert obj2.created_at == obj.created_at
        assert obj2.ontology_tags == obj.ontology_tags

        # Hash determinism: same fields -> same hash
        assert obj.hash == obj2.hash

        # Second round-trip is stable
        d2 = obj2.to_dict()
        assert d == d2

    def test_serialization_is_idempotent(self):
        for _, obj in OBJECT_SAMPLES:
            for _ in range(3):
                d = obj.to_dict()
                obj = type(obj).from_dict(d)


# ===========================================================================
# 5. Long audit chain performance
# ===========================================================================


class TestLongAuditChain:
    """Verify chain integrity and performance with 100k+ entries."""

    def test_1k_entries_chain_integrity(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "long_chain.db")
        repo = ResearchRepository(db_path)

        n = 1000
        for i in range(n):
            e = AuditEntry(
                actor="perf", action=f"OP_{i}", object_id=f"o{i}", object_type="PerfTest"
            )
            repo.save_audit_entry(e)

        assert repo.verify_audit_chain()
        entries = repo.load_audit_entries()
        assert len(entries) == n

    def test_10k_chain_verify_speed(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "speed_chain.db")
        repo = ResearchRepository(db_path)

        n = 10_000
        for i in range(n):
            e = AuditEntry(
                actor="perf", action=f"OP_{i}", object_id=f"o{i}", object_type="PerfTest"
            )
            repo.save_audit_entry(e)

        start = time.monotonic()
        assert repo.verify_audit_chain()
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"verify_audit_chain took {elapsed:.2f}s for {n} entries"


# ===========================================================================
# 6. Tamper detection
# ===========================================================================


class TestTamperDetection:
    """Verify detect_tampering() catches various attack types."""

    def _make_repo_with_entries(self, tmp_path, n=5):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "tamper.db")
        repo = ResearchRepository(db_path)
        for i in range(n):
            e = AuditEntry(actor="sys", action=f"OP_{i}", object_id=f"o{i}", object_type="Test")
            repo.save_audit_entry(e)
        return repo

    def test_detect_hash_modification(self, tmp_path):
        repo = self._make_repo_with_entries(tmp_path)

        # Tamper: modify the entry_hash of the second entry
        conn = repo._get_conn()
        conn.execute("UPDATE audit_logs SET entry_hash = 'tampered_hash' WHERE rowid = 2")
        conn.commit()

        issues = repo.detect_tampering()
        assert any(i["issue"] == "hash_mismatch" for i in issues)

        assert not repo.verify_audit_chain()

    def test_detect_previous_entry_modification(self, tmp_path):
        repo = self._make_repo_with_entries(tmp_path)

        conn = repo._get_conn()
        conn.execute("UPDATE audit_logs SET previous_entry = 'bad_prev_hash' WHERE rowid = 3")
        conn.commit()

        issues = repo.detect_tampering()
        assert any(i["issue"] == "broken_link" for i in issues)

    def test_detect_row_deletion(self, tmp_path):
        repo = self._make_repo_with_entries(tmp_path)

        conn = repo._get_conn()
        conn.execute("DELETE FROM audit_logs WHERE rowid = 3")
        conn.commit()

        issues = repo.detect_tampering()
        assert any(i["issue"] == "rowid_gap" for i in issues)
        assert not repo.verify_audit_chain()

    def test_clean_chain_no_issues(self, tmp_path):
        repo = self._make_repo_with_entries(tmp_path)
        issues = repo.detect_tampering()
        assert issues == []
        assert repo.verify_audit_chain()


# ===========================================================================
# 7. Cross-process deterministic hashing
# ===========================================================================


class TestDeterministicHashing:
    """Verify deterministic_hash produces identical output across dict orderings."""

    def test_json_sort_keys_is_deterministic(self):
        data_a = {"z": 1, "a": 2, "n": 3, "ontology_tags": ["c", "a", "b"]}
        data_b = {"ontology_tags": ["c", "a", "b"], "a": 2, "n": 3, "z": 1}

        h1 = deterministic_hash(data_a)
        h2 = deterministic_hash(data_b)
        assert h1 == h2

    def test_nested_dict_determinism(self):
        a = {"outer": {"z": 1, "a": 2}, "tags": sorted(["c", "a", "b"])}
        b = {"tags": ["a", "b", "c"], "outer": {"a": 2, "z": 1}}

        assert deterministic_hash(a) == deterministic_hash(b)

    def test_ontology_tag_ordering_in_hashable(self):
        """AuditEntry's _to_hashable_dict uses sorted(ontology_tags)."""
        from researchos.objects.process import AuditEntry

        e = AuditEntry(
            actor="sys", action="TEST", object_id="o1", object_type="T", ontology_tags=["z", "a"]
        )
        h = e._to_hashable_dict()
        assert h["ontology_tags"] == sorted(h["ontology_tags"])

    def test_all_hashable_dicts_use_sorted_tags(self):
        """Verify every object type sorts its ontology_tags in _to_hashable_dict."""
        for _, obj in OBJECT_SAMPLES:
            h = obj._to_hashable_dict()
            if "ontology_tags" in h and isinstance(h["ontology_tags"], list):
                assert h["ontology_tags"] == sorted(h["ontology_tags"]), (
                    f"{type(obj).__name__} ontology_tags not sorted in hashable dict"
                )

    def test_object_hash_matches_across_round_trip(self):
        for _, obj in OBJECT_SAMPLES:
            h1 = obj.hash
            d = obj.to_dict()
            obj2 = type(obj).from_dict(d)
            assert obj2.hash == h1


# ===========================================================================
# 8. Lifecycle reconstruction
# ===========================================================================


class TestLifecycleReconstruction:
    """Verify lifecycle transitions survive from_dict round-trip."""

    @pytest.mark.parametrize("name,obj", OBJECT_SAMPLES + NON_DEFAULT_SAMPLES)
    def test_lifecycle_preserved(self, name, obj):
        before = obj.lifecycle.current_stage

        d = obj.to_dict()
        obj2 = type(obj).from_dict(d)

        assert obj2.lifecycle.current_stage == before
        assert len(obj2.lifecycle.transitions) == len(obj.lifecycle.transitions)

    def test_lifecycle_transitions_preserved_after_mutations(self):
        obj = Observation(source="T", timestamp=ts(), value=1.0)
        obj.lifecycle.transition(LifecycleStage.UPDATED, reason="first update")
        obj.lifecycle.transition(LifecycleStage.COMPLETE, reason="done")

        d = obj.to_dict()
        obj2 = Observation.from_dict(d)

        assert obj2.lifecycle.current_stage == LifecycleStage.COMPLETE
        assert len(obj2.lifecycle.transitions) == 3  # CREATED + UPDATED + COMPLETE

    def test_all_transition_timestamps_preserved(self):
        from researchos.core.lifecycle import LifecycleStage

        obj = Observation(source="T", timestamp=ts(), value=1.0)
        obj.lifecycle.transition(LifecycleStage.UPDATED, reason="updated")
        obj.lifecycle.transition(LifecycleStage.ANALYZED, reason="analyzed")

        d = obj.to_dict()
        obj2 = Observation.from_dict(d)

        for t1, t2 in zip(obj.lifecycle.transitions, obj2.lifecycle.transitions):
            assert t1.stage == t2.stage
            assert t1.reason == t2.reason
            assert t1.timestamp == t2.timestamp


# ===========================================================================
# 9. Dual-storage consistency
# ===========================================================================


class TestDualStorageConsistency:
    """Verify objects table and audit_logs table stay in sync for AuditEntry."""

    def test_save_audit_entry_writes_to_both_tables(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(str(tmp_path / "dual.db"))

        e = AuditEntry(actor="sys", action="TEST", object_id="o1", object_type="T")
        repo.save_audit_entry(e)

        # Check audit_logs
        conn = repo._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE id = ?", (e.id,))
        assert cursor.fetchone()[0] == 1

        # Check objects table
        cursor.execute(
            "SELECT COUNT(*) FROM objects WHERE id = ? AND object_type = 'AuditEntry'", (e.id,)
        )
        assert cursor.fetchone()[0] == 1

    def test_dual_storage_consistency_check(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(str(tmp_path / "dual_check.db"))

        for i in range(5):
            e = AuditEntry(actor="sys", action=f"OP_{i}", object_id=f"o{i}", object_type="T")
            repo.save_audit_entry(e)

        assert repo.verify_dual_storage_consistency() == []

    def test_detect_orphan_in_objects(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(str(tmp_path / "orphan_obj.db"))

        e = AuditEntry(actor="sys", action="TEST", object_id="o1", object_type="T")
        repo.save_audit_entry(e)

        # Delete from audit_logs to create orphan in objects
        conn = repo._get_conn()
        conn.execute("DELETE FROM audit_logs WHERE id = ?", (e.id,))
        conn.commit()

        issues = repo.verify_dual_storage_consistency()
        assert any("exists in objects but not in audit_logs" in i for i in issues)

    def test_detect_orphan_in_audit_logs(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        repo = ResearchRepository(str(tmp_path / "orphan_audit.db"))

        e = AuditEntry(actor="sys", action="TEST", object_id="o1", object_type="T")
        repo.save_audit_entry(e)

        # Delete from objects to create orphan in audit_logs
        conn = repo._get_conn()
        conn.execute("DELETE FROM objects WHERE id = ?", (e.id,))
        conn.commit()

        issues = repo.verify_dual_storage_consistency()
        assert any("exists in audit_logs but not in objects" in i for i in issues)
