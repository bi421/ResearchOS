"""
Tests: Pipeline Repository Layer (Q15).

Verifies deterministic, immutable, stdlib-only persistence of
``PipelineReport`` objects produced by the orchestration layer.

Test matrix:
    - contract design (frozen, hashable, serializable, immutable metadata)
    - storage engine (save/load/list/delete/count/clear)
    - determinism (same report -> same id; equal repos -> equal serialized)
    - immutability (FrozenInstanceError / MappingProxyType TypeError)
    - failure cases (missing pipeline, invalid report, malformed payloads)
    - dependency audit (no forbidden third-party imports in module source)
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import FrozenInstanceError

from researchos.orchestration.contracts import (
    EvidenceEdgeDescriptor,
    EvidenceNodeDescriptor,
    PipelineReport,
    PipelineStatus,
)
from researchos.pipeline_repository import (
    InvalidPipelineRecordError,
    PipelineNotFoundError,
    PipelineRecord,
    PipelineRepository,
    PipelineRepositoryError,
)
from researchos.pipeline_repository.contracts import PIPELINE_REPOSITORY_VERSION
from researchos.quant_engine.models.contracts import (
    ModelContract as RegistryModelContract,
)
from researchos.quant_engine.training.contracts import (
    ModelContract as TrainingModelContract,
)
from researchos.quant_engine.training.contracts import (
    ModelType,
)
from researchos.quant_engine.training.training_result import TrainingResult
from researchos.quant_engine.validation.contracts import (
    FoldResult,
    ValidationResult,
)


def _make_report(
    *,
    pipeline_id: str = "pipeline_a",
    status: str = "completed",
    label_name: str = "direction",
    dataset_hash: str = "dsethash1",
    model_id: str = "model_v1",
) -> PipelineReport:
    """Build a valid deterministic ``PipelineReport`` fixture."""
    training_model = TrainingModelContract(
        model_id=model_id,
        name=model_id,
        version="1.0.0",
        model_type=ModelType.FEATURE_WEIGHT,
        feature_names=("returns", "rsi_14"),
        label_name=label_name,
        parameters={"weights": [0.5, 0.5]},
        metadata={"source": "test"},
        created_at="2024-01-01T00:00:00Z",
        training_hash="trainhash1",
    )
    training = TrainingResult(
        model=training_model,
        metrics={"accuracy": 0.75},
        dataset_hash=dataset_hash,
        n_samples=100,
        n_features=2,
        predictions=(0.5, 0.6),
        metadata={"fold": 1},
    )
    fold = FoldResult(
        fold_id=1,
        train_range=(0, 79),
        validation_range=(80, 99),
        metrics={"accuracy": 0.75},
        sample_count=20,
    )
    validation = ValidationResult(
        train_size=80,
        validation_size=20,
        test_size=0,
        fold_count=1,
        fold_results=(fold,),
        metrics={"accuracy": 0.75},
        metadata={"window": "walk_forward"},
    )
    registry_model = RegistryModelContract(
        model_id=model_id,
        name=model_id,
        version="1.0.0",
        algorithm="feature_weight",
        feature_names=("returns", "rsi_14"),
        label_name=label_name,
        dataset_hash=dataset_hash,
        validation_hash="valhash1",
        parameters={"weights": [0.5, 0.5]},
        created_at="2024-01-01T00:00:00Z",
        metadata={"orchestration_version": "1.0.0"},
    )
    node = EvidenceNodeDescriptor(
        node_id="node_1",
        node_type="dataset",
        metadata={"hash": dataset_hash},
    )
    edge = EvidenceEdgeDescriptor(
        edge_id="edge_1",
        source_id="node_1",
        target_id="node_2",
        relationship="trains",
        metadata={"model_id": model_id},
    )
    return PipelineReport(
        pipeline_id=pipeline_id,
        status=PipelineStatus(status),
        dataset_hash=dataset_hash,
        feature_names=("returns", "rsi_14"),
        label_name=label_name,
        sample_count=100,
        feature_count=2,
        validation=validation,
        training=training,
        model_contract=registry_model,
        nodes=(node,),
        edges=(edge,),
        metadata={"author": "researchos"},
        created_at="2024-01-01T00:00:00Z",
    )


class TestPipelineRecordContract(unittest.TestCase):
    """Phase 1 — contract design."""

    def test_frozen_dataclass(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="2024-01-01T00:00:00Z",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        with self.assertRaises(FrozenInstanceError):
            record.pipeline_id = "changed"  # type: ignore[misc]

    def test_metadata_is_immutable_mapping(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
            metadata={"a": 1},
        )
        with self.assertRaises(TypeError):
            record.metadata["x"] = 1  # type: ignore[index]

    def test_hashable(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        self.assertEqual(hash(record), hash(record))

    def test_equal_reports_same_hash(self):
        r1 = PipelineRecord(
            pipeline_id="pid_1",
            report=_make_report(),
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        r2 = PipelineRecord(
            pipeline_id="pid_1",
            report=_make_report(),
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        self.assertEqual(hash(r1), hash(r2))

    def test_rejects_non_report(self):
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRecord(
                pipeline_id="pid_1",
                report="not a report",  # type: ignore[arg-type]
                stored_at="",
                version=PIPELINE_REPOSITORY_VERSION,
            )

    def test_rejects_blank_id(self):
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRecord(
                pipeline_id="   ",
                report=_make_report(),
                stored_at="",
                version=PIPELINE_REPOSITORY_VERSION,
            )

    def test_rejects_non_mapping_metadata(self):
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRecord(
                pipeline_id="pid_1",
                report=_make_report(),
                stored_at="",
                version=PIPELINE_REPOSITORY_VERSION,
                metadata=[1, 2],  # type: ignore[arg-type]
            )

    def test_errors_are_related(self):
        self.assertTrue(issubclass(PipelineNotFoundError, PipelineRepositoryError))
        self.assertTrue(issubclass(InvalidPipelineRecordError, PipelineRepositoryError))

    def test_to_dict_from_dict_roundtrip(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="2024-01-01T00:00:00Z",
            version=PIPELINE_REPOSITORY_VERSION,
            metadata={"tag": "test"},
        )
        restored = PipelineRecord.from_dict(record.to_dict())
        self.assertEqual(restored, record)
        self.assertEqual(restored.report, report)
        self.assertEqual(restored.metadata["tag"], "test")


class TestPipelineRepositoryStorage(unittest.TestCase):
    """Phase 2 — storage engine."""

    def setUp(self):
        self.repo = PipelineRepository(path="unused_default.json")

    def test_save_returns_deterministic_id(self):
        report = _make_report()
        pid1 = self.repo.save(report)
        pid2 = self.repo.save(_make_report())
        self.assertEqual(pid1, pid2)
        self.assertEqual(len(pid1), 64)  # SHA-256 hex

    def test_save_is_idempotent(self):
        report = _make_report()
        self.repo.save(report)
        self.repo.save(report)
        self.assertEqual(self.repo.count(), 1)

    def test_load_returns_equal_record(self):
        report = _make_report()
        pid = self.repo.save(report, stored_at="2024-01-01T00:00:00Z")
        record = self.repo.load(pid)
        self.assertEqual(record.pipeline_id, pid)
        self.assertEqual(record.report, report)
        self.assertEqual(record.stored_at, "2024-01-01T00:00:00Z")
        self.assertEqual(record.version, PIPELINE_REPOSITORY_VERSION)

    def test_load_missing_raises(self):
        with self.assertRaises(PipelineNotFoundError):
            self.repo.load("does_not_exist")

    def test_delete(self):
        pid = self.repo.save(_make_report())
        self.repo.delete(pid)
        self.assertEqual(self.repo.count(), 0)
        with self.assertRaises(PipelineNotFoundError):
            self.repo.delete(pid)

    def test_count_clear(self):
        self.assertEqual(self.repo.count(), 0)
        self.repo.save(_make_report(pipeline_id="p1"))
        self.repo.save(_make_report(pipeline_id="p2", label_name="regime"))
        self.assertEqual(self.repo.count(), 2)
        self.repo.clear()
        self.assertEqual(self.repo.count(), 0)

    def test_list_sorted_and_limited(self):
        # Distinct reports (different dataset_hash) produce distinct ids.
        self.repo.save(_make_report(dataset_hash="aaa"))
        self.repo.save(_make_report(dataset_hash="bbb"))
        self.repo.save(_make_report(dataset_hash="ccc"))
        all_records = self.repo.list()
        self.assertEqual(len(all_records), 3)
        ids = [r.pipeline_id for r in all_records]
        self.assertEqual(ids, sorted(ids))
        limited = self.repo.list(limit=2)
        self.assertEqual(len(limited), 2)

    def test_list_filter_by_status(self):
        self.repo.save(_make_report(status="completed"))
        self.repo.save(_make_report(status="failed", dataset_hash="failed1"))
        completed = self.repo.list(status="completed")
        self.assertEqual(len(completed), 1)
        failed = self.repo.list(status="failed")
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].report.status.value, "failed")

    def test_has(self):
        pid = self.repo.save(_make_report())
        self.assertTrue(self.repo.has(pid))
        self.assertFalse(self.repo.has("nope"))

    def test_iteration(self):
        self.repo.save(_make_report(dataset_hash="aaa"))
        self.repo.save(_make_report(dataset_hash="bbb"))
        self.assertEqual(len(list(self.repo)), 2)
        self.assertEqual(len(self.repo), 2)

    def test_save_rejects_non_report(self):
        with self.assertRaises(InvalidPipelineRecordError):
            self.repo.save("not a report")  # type: ignore[arg-type]

    def test_save_rejects_none(self):
        with self.assertRaises(InvalidPipelineRecordError):
            self.repo.save(None)  # type: ignore[arg-type]


class TestPipelineRepositorySerialization(unittest.TestCase):
    """Phase 3 — serialization."""

    def test_to_dict_from_dict_roundtrip(self):
        self.repo = PipelineRepository()
        self.repo.save(_make_report(pipeline_id="p1", dataset_hash="aaa"))
        self.repo.save(_make_report(pipeline_id="p2", dataset_hash="bbb"))
        restored = PipelineRepository.from_dict(self.repo.to_dict())
        self.assertEqual(restored.serialize(), self.repo.serialize())
        self.assertEqual(restored.count(), 2)
        self.assertEqual(
            restored.load(self.repo.list()[0].pipeline_id).report,
            self.repo.list()[0].report,
        )

    def test_serialize_deserialize_roundtrip(self):
        self.repo = PipelineRepository()
        self.repo.save(_make_report())
        text = self.repo.serialize()
        restored = PipelineRepository.deserialize(text)
        self.assertEqual(restored.serialize(), text)

    def test_serialized_is_valid_json(self):
        self.repo = PipelineRepository()
        self.repo.save(_make_report())
        parsed = json.loads(self.repo.serialize())
        self.assertEqual(parsed["version"], PIPELINE_REPOSITORY_VERSION)
        self.assertIn("records", parsed)

    def test_deserialize_rejects_bad_json(self):
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRepository.deserialize("{ not json")

    def test_deserialize_rejects_non_mapping(self):
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRepository.deserialize("[1, 2, 3]")

    def test_deserialize_rejects_bad_record_key(self):
        data = {
            "version": PIPELINE_REPOSITORY_VERSION,
            "records": {
                "key_a": {"not": "valid"},
            },
        }
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRepository.from_dict(data)

    def test_disk_roundtrip(self):
        self.repo = PipelineRepository()
        self.repo.save(_make_report(pipeline_id="p1", dataset_hash="aaa"))
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "repo.json")
            self.repo.save_to_disk(target)
            loaded = PipelineRepository.load_from_disk(target)
            self.assertEqual(loaded.serialize(), self.repo.serialize())
            self.assertEqual(loaded.count(), 1)

    def test_load_from_disk_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "missing.json")
            with self.assertRaises(FileNotFoundError):
                PipelineRepository.load_from_disk(target)
            empty = PipelineRepository.load_from_disk(target, missing_ok=True)
            self.assertEqual(empty.count(), 0)


class TestPipelineRepositoryDeterminism(unittest.TestCase):
    """Phase 4 — determinism."""

    def test_same_report_identical_id(self):
        r1 = PipelineRepository()
        r2 = PipelineRepository()
        id1 = r1.save(_make_report())
        id2 = r2.save(_make_report())
        self.assertEqual(id1, id2)

    def test_same_content_identical_serialization(self):
        repo_a = PipelineRepository()
        repo_b = PipelineRepository()
        repo_a.save(_make_report(pipeline_id="p1", dataset_hash="aaa"))
        repo_a.save(_make_report(pipeline_id="p2", dataset_hash="bbb"))
        repo_b.save(_make_report(pipeline_id="p1", dataset_hash="aaa"))
        repo_b.save(_make_report(pipeline_id="p2", dataset_hash="bbb"))
        self.assertEqual(repo_a.serialize(), repo_b.serialize())

    def test_id_does_not_use_timestamp_or_uuid(self):
        report = _make_report()
        pid = PipelineRepository().save(report)
        # Deterministic hash is 64 hex chars, independent of storage time.
        self.assertRegex(pid, r"^[0-9a-f]{64}$")
        pid2 = PipelineRepository().save(report)
        self.assertEqual(pid, pid2)

    def test_reports_with_different_content_differ(self):
        r = PipelineRepository()
        id1 = r.save(_make_report(dataset_hash="aaa"))
        id2 = r.save(_make_report(dataset_hash="bbb"))
        self.assertNotEqual(id1, id2)


class TestPipelineRepositoryImmutability(unittest.TestCase):
    """Phase 5 — immutability."""

    def test_record_field_assignment_raises(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        with self.assertRaises(FrozenInstanceError):
            record.pipeline_id = "x"  # type: ignore[misc]

    def test_record_metadata_readonly(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
            metadata={"a": 1},
        )
        with self.assertRaises(TypeError):
            record.metadata["x"] = 1  # type: ignore[index]

    def test_report_metadata_readonly(self):
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=_make_report(),
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        with self.assertRaises(TypeError):
            record.report.metadata["x"] = 1  # type: ignore[index]

    def test_stored_report_unchanged_after_save(self):
        report = _make_report()
        original = report.to_dict()
        PipelineRepository().save(report)
        self.assertEqual(report.to_dict(), original)


class TestPipelineRepositoryFailure(unittest.TestCase):
    """Phase 6 — failure tests."""

    def test_loading_missing_raises_pipeline_not_found(self):
        with self.assertRaises(PipelineNotFoundError):
            PipelineRepository().load("missing_id")

    def test_invalid_report_raises_invalid_record(self):
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRepository().save(12345)  # type: ignore[arg-type]

    def test_delete_missing_raises(self):
        with self.assertRaises(PipelineNotFoundError):
            PipelineRepository().delete("missing_id")

    def test_from_dict_missing_report(self):
        data = {
            "version": PIPELINE_REPOSITORY_VERSION,
            "records": {
                "abc": {
                    "pipeline_id": "abc",
                    "stored_at": "",
                    "version": "1.0.0",
                    "metadata": {},
                    # missing "report" key
                }
            },
        }
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRepository.from_dict(data)

    def test_from_dict_mismatched_key(self):
        report = _make_report()
        record = PipelineRecord(
            pipeline_id="pid_1",
            report=report,
            stored_at="",
            version=PIPELINE_REPOSITORY_VERSION,
        )
        d = record.to_dict()
        data = {"version": "1.0.0", "records": {"different_key": d}}
        with self.assertRaises(InvalidPipelineRecordError):
            PipelineRepository.from_dict(data)


class TestDependencyAudit(unittest.TestCase):
    """Phase 7 — dependency audit: forbidden libs in module source."""

    FORBIDDEN = [
        "numpy",
        "pandas",
        "sklearn",
        "scikit",
        "torch",
        "tensorflow",
        "openai",
        "llm",
        "import random",
        "from random",
        "uuid4",
        "pickle",
        "sqlite3",
    ]

    def _module_sources(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pkg = os.path.join(base, "pipeline_repository")
        for name in ("__init__.py", "contracts.py", "repository.py"):
            path = os.path.join(pkg, name)
            with open(path, encoding="utf-8") as handle:
                yield name, handle.read()

    def _import_lines(self, source):
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                yield stripped

    def test_no_forbidden_imports(self):
        for name, source in self._module_sources():
            for line in self._import_lines(source):
                for token in self.FORBIDDEN:
                    self.assertNotIn(
                        token,
                        line,
                        msg=f"forbidden token {token!r} found in {name}: {line}",
                    )

    def test_stdlib_only_imports(self):
        allowed_roots = {
            "__future__",
            "json",
            "hashlib",
            "os",
            "typing",
            "dataclasses",
            "types",
            "researchos",
        }
        import re

        for name, source in self._module_sources():
            for line in self._import_lines(source):
                # Skip relative intra-package imports (e.g. "from .contracts").
                if line.startswith("from ."):
                    continue
                match = re.match(r"^(?:import|from)\s+([A-Za-z0-9_]+)", line)
                if match is None:
                    self.fail(f"unparsable import in {name}: {line}")
                root = match.group(1).split(".")[0]
                self.assertIn(
                    root,
                    allowed_roots,
                    msg=f"non-stdlib import root {root!r} in {name}: {line}",
                )


if __name__ == "__main__":
    unittest.main()
