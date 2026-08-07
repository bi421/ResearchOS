"""
Tests: Research Evaluation Engine (Q16).

All tests are deterministic. No randomness, no external state.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import FrozenInstanceError
from typing import Dict, List, Optional, Tuple

from researchos.evaluation import (
    EVALUATION_VERSION,
    EvaluationReport,
    EvaluationScore,
    InvalidEvaluationError,
    PipelineEvaluationError,
    ResearchEvaluator,
)
from researchos.evaluation.contracts import _grade
from researchos.evaluation.engine import (
    _compute_evidence,
    _compute_overall,
    _compute_reproducibility,
    _compute_stability,
    _evaluation_id,
)
from researchos.orchestration.contracts import (
    EvidenceEdgeDescriptor,
    EvidenceNodeDescriptor,
    PipelineReport,
    PipelineStatus,
)
from researchos.pipeline_repository.repository import PipelineRepository
from researchos.quant_engine.models.contracts import (
    ModelContract as RegistryModelContract,
)
from researchos.quant_engine.training.contracts import (
    ModelContract as TrainingModelContract,
    ModelType,
)
from researchos.quant_engine.training.training_result import TrainingResult
from researchos.quant_engine.validation.contracts import (
    FoldResult,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_model() -> RegistryModelContract:
    return RegistryModelContract(
        model_id="test_model_v1",
        name="Test Model",
        version="1.0.0",
        algorithm="rule_based",
        feature_names=("f1", "f2"),
        label_name="label",
        dataset_hash="abc123",
        validation_hash="def456",
        parameters={"threshold": 0.5},
        metadata={"source": "test"},
    )


def _make_training_model() -> TrainingModelContract:
    """Create a training-framework ModelContract for TrainingResult."""
    return TrainingModelContract(
        model_id="test_model_v1",
        name="Test Model",
        version="1.0.0",
        model_type=ModelType.RULE_BASED,
        feature_names=("f1", "f2"),
        label_name="label",
        parameters={"threshold": 0.5},
        metadata={"source": "test"},
        training_hash="abc123",
    )


def _make_training(metrics: Optional[Dict[str, float]] = None) -> TrainingResult:
    return TrainingResult(
        model=_make_training_model(),
        metrics=metrics or {"accuracy": 0.85, "precision": 0.80},
        dataset_hash="abc123",
        n_samples=100,
        n_features=2,
        predictions=(0.5, 0.6, 0.7),
        metadata={"trainer": "test"},
    )


def _make_fold(fold_id: int, metrics: Optional[Dict[str, float]] = None) -> FoldResult:
    return FoldResult(
        fold_id=fold_id,
        train_range=(0, 80),
        validation_range=(80, 100),
        metrics=metrics or {"accuracy": 0.85, "loss": 0.15},
        sample_count=20,
    )


def _make_validation(
    fold_count: int = 3,
    fold_metrics: Optional[List[Dict[str, float]]] = None,
) -> ValidationResult:
    if fold_metrics is None:
        fold_metrics = [{"accuracy": 0.85, "loss": 0.15}] * fold_count
    return ValidationResult(
        train_size=80,
        validation_size=20,
        test_size=0,
        fold_count=fold_count,
        fold_results=tuple(
            _make_fold(i + 1, m) for i, m in enumerate(fold_metrics)
        ),
        metrics={"mean_accuracy": 0.85},
        metadata={"method": "walk_forward"},
    )


def _make_report(
    pipeline_id: str = "test_pipeline",
    status: PipelineStatus = PipelineStatus.COMPLETED,
    validation: Optional[ValidationResult] = None,
    training: Optional[TrainingResult] = None,
    nodes: Tuple[EvidenceNodeDescriptor, ...] = (),
    edges: Tuple[EvidenceEdgeDescriptor, ...] = (),
) -> PipelineReport:
    return PipelineReport(
        pipeline_id=pipeline_id,
        status=status,
        dataset_hash="def456",
        feature_names=("f1", "f2"),
        label_name="label",
        sample_count=100,
        feature_count=2,
        validation=validation or _make_validation(),
        training=training or _make_training(),
        model_contract=_make_model(),
        nodes=nodes,
        edges=edges,
        metadata={"created_by": "test"},
        created_at="2024-01-01T00:00:00Z",
    )


def _make_repo(reports: List[PipelineReport]) -> PipelineRepository:
    repo = PipelineRepository()
    for report in reports:
        repo.save(report)
    return repo


# ===================================================================
# TestEvaluationScoreContract
# ===================================================================


class TestEvaluationScoreContract(unittest.TestCase):
    def test_frozen_dataclass(self):
        score = EvaluationScore(
            pipeline_id="p1",
            reproducibility_score=0.8,
            stability_score=0.7,
            evidence_score=0.6,
            overall_score=0.72,
            grade="B+",
        )
        with self.assertRaises(FrozenInstanceError):
            score.pipeline_id = "x"  # type: ignore

    def test_metadata_is_immutable_mapping(self):
        score = EvaluationScore(
            pipeline_id="p1",
            reproducibility_score=0.8,
            stability_score=0.7,
            evidence_score=0.6,
            overall_score=0.72,
            grade="B+",
            metadata={"key": "value"},
        )
        with self.assertRaises(TypeError):
            score.metadata["key"] = "new_value"  # type: ignore

    def test_hashable(self):
        s1 = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        s2 = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        self.assertEqual(hash(s1), hash(s2))

    def test_to_dict_from_dict_roundtrip(self):
        original = EvaluationScore(
            pipeline_id="p1",
            reproducibility_score=0.8,
            stability_score=0.7,
            evidence_score=0.6,
            overall_score=0.72,
            grade="B+",
            metadata={"src": "test"},
        )
        d = original.to_dict()
        restored = EvaluationScore.from_dict(d)
        self.assertEqual(original, restored)
        self.assertEqual(hash(original), hash(restored))

    def test_rejects_non_mapping_metadata(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationScore(
                pipeline_id="p1",
                reproducibility_score=0.8,
                stability_score=0.7,
                evidence_score=0.6,
                overall_score=0.72,
                grade="B+",
                metadata="not_a_mapping",  # type: ignore
            )

    def test_clamps_scores_to_01(self):
        score = EvaluationScore(
            pipeline_id="p1",
            reproducibility_score=1.5,
            stability_score=-0.5,
            evidence_score=0.6,
            overall_score=0.72,
            grade="B+",
        )
        self.assertEqual(score.reproducibility_score, 1.0)
        self.assertEqual(score.stability_score, 0.0)

    def test_rejects_blank_pipeline_id(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationScore("", 0.8, 0.7, 0.6, 0.72, "B+")

    def test_rejects_blank_grade(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "")

    def test_serializable(self):
        score = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        text = json.dumps(score.to_dict(), sort_keys=True)
        restored = EvaluationScore.from_dict(json.loads(text))
        self.assertEqual(score, restored)

    def test_deterministic_serialization(self):
        s1 = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        s2 = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        self.assertEqual(
            json.dumps(s1.to_dict(), sort_keys=True),
            json.dumps(s2.to_dict(), sort_keys=True),
        )


# ===================================================================
# TestEvaluationReportContract
# ===================================================================


class TestEvaluationReportContract(unittest.TestCase):
    def setUp(self):
        self.score = EvaluationScore(
            "p1", 0.8, 0.7, 0.6, 0.72, "B+", metadata={"src": "test"}
        )
        self.eid = _evaluation_id(self.score, "2024-01-01T00:00:00Z")

    def test_frozen_dataclass(self):
        report = EvaluationReport(
            evaluation_id=self.eid,
            pipeline_id="p1",
            score=self.score,
            created_at="2024-01-01T00:00:00Z",
            version=EVALUATION_VERSION,
        )
        with self.assertRaises(FrozenInstanceError):
            report.pipeline_id = "x"  # type: ignore

    def test_hashable(self):
        r1 = EvaluationReport(
            self.eid, "p1", self.score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
        )
        r2 = EvaluationReport(
            self.eid, "p1", self.score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
        )
        self.assertEqual(hash(r1), hash(r2))

    def test_to_dict_from_dict_roundtrip(self):
        original = EvaluationReport(
            self.eid, "p1", self.score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
        )
        d = original.to_dict()
        restored = EvaluationReport.from_dict(d)
        self.assertEqual(original, restored)
        self.assertEqual(hash(original), hash(restored))

    def test_rejects_blank_evaluation_id(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationReport(
                "", "p1", self.score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
            )

    def test_rejects_non_score(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationReport(
                self.eid, "p1", "not_a_score", "2024-01-01T00:00:00Z", EVALUATION_VERSION  # type: ignore
            )

    def test_serializable(self):
        report = EvaluationReport(
            self.eid, "p1", self.score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
        )
        text = json.dumps(report.to_dict(), sort_keys=True)
        restored = EvaluationReport.from_dict(json.loads(text))
        self.assertEqual(report, restored)


# ===================================================================
# TestGradeFunction
# ===================================================================


class TestGradeFunction(unittest.TestCase):
    def test_grade_A_plus(self):
        self.assertEqual(_grade(0.95), "A+")
        self.assertEqual(_grade(1.0), "A+")

    def test_grade_A(self):
        self.assertEqual(_grade(0.85), "A")

    def test_grade_B_plus(self):
        self.assertEqual(_grade(0.75), "B+")

    def test_grade_B(self):
        self.assertEqual(_grade(0.65), "B")

    def test_grade_C_plus(self):
        self.assertEqual(_grade(0.55), "C+")

    def test_grade_C(self):
        self.assertEqual(_grade(0.45), "C")

    def test_grade_D_plus(self):
        self.assertEqual(_grade(0.35), "D+")

    def test_grade_D(self):
        self.assertEqual(_grade(0.25), "D")

    def test_grade_F(self):
        self.assertEqual(_grade(0.0), "F")
        self.assertEqual(_grade(0.24), "F")

    def test_deterministic(self):
        for v in [0.0, 0.1, 0.5, 0.9, 1.0]:
            self.assertEqual(_grade(v), _grade(v))


# ===================================================================
# TestScoreComputation
# ===================================================================


class TestScoreComputation(unittest.TestCase):
    def test_reproducibility_default(self):
        report = _make_report()
        score = _compute_reproducibility(report)
        self.assertGreaterEqual(score, 0.7)
        self.assertLessEqual(score, 1.0)

    def test_reproducibility_with_evidence(self):
        nodes = (
            EvidenceNodeDescriptor("n1", "dataset", {"hash": "abc"}),
            EvidenceNodeDescriptor("n2", "model", {"name": "m1"}),
        )
        edges = (
            EvidenceEdgeDescriptor("e1", "n1", "n2", "trains"),
        )
        report = _make_report(nodes=nodes, edges=edges)
        score = _compute_reproducibility(report)
        self.assertAlmostEqual(score, 0.95, places=10)

    def test_reproducibility_deterministic(self):
        report = _make_report()
        self.assertEqual(
            _compute_reproducibility(report),
            _compute_reproducibility(report),
        )

    def test_stability_no_folds(self):
        validation = _make_validation(fold_count=0)
        report = _make_report(validation=validation)
        score = _compute_stability(report)
        self.assertEqual(score, 0.5)

    def test_stability_perfect(self):
        fold_metrics = [{"accuracy": 0.85}] * 5
        validation = _make_validation(fold_count=5, fold_metrics=fold_metrics)
        report = _make_report(validation=validation)
        score = _compute_stability(report)
        self.assertAlmostEqual(score, 1.0, places=10)

    def test_stability_deterministic(self):
        report = _make_report()
        self.assertEqual(
            _compute_stability(report),
            _compute_stability(report),
        )

    def test_evidence_no_nodes(self):
        report = _make_report()
        score = _compute_evidence(report)
        self.assertAlmostEqual(score, 0.7, places=10)

    def test_evidence_with_nodes(self):
        nodes = (
            EvidenceNodeDescriptor("n1", "dataset", {"hash": "abc"}),
        )
        edges = (
            EvidenceEdgeDescriptor("e1", "n1", "n2", "trains"),
        )
        report = _make_report(nodes=nodes, edges=edges)
        score = _compute_evidence(report)
        self.assertAlmostEqual(score, 1.0, places=10)

    def test_evidence_deterministic(self):
        report = _make_report()
        self.assertEqual(
            _compute_evidence(report),
            _compute_evidence(report),
        )

    def test_overall_formula(self):
        score = _compute_overall(0.8, 0.7, 0.6)
        self.assertAlmostEqual(score, 0.71, places=10)

    def test_overall_deterministic(self):
        self.assertEqual(
            _compute_overall(0.8, 0.7, 0.6),
            _compute_overall(0.8, 0.7, 0.6),
        )


# ===================================================================
# TestResearchEvaluator
# ===================================================================


class TestResearchEvaluator(unittest.TestCase):
    def setUp(self):
        self.report = _make_report()
        self.repo = _make_repo([self.report])
        pid = self.repo.list()[0].pipeline_id
        self.pipeline_id = pid
        self.evaluator = ResearchEvaluator(self.repo)

    def test_constructor_rejects_non_repository(self):
        with self.assertRaises(PipelineEvaluationError):
            ResearchEvaluator("not_a_repo")  # type: ignore

    def test_evaluate_returns_report(self):
        report = self.evaluator.evaluate(self.pipeline_id)
        self.assertIsInstance(report, EvaluationReport)
        self.assertEqual(report.pipeline_id, self.pipeline_id)

    def test_evaluate_determinism(self):
        r1 = self.evaluator.evaluate(self.pipeline_id)
        r2 = self.evaluator.evaluate(self.pipeline_id)
        self.assertEqual(r1, r2)
        self.assertEqual(hash(r1), hash(r2))
        self.assertEqual(r1.to_dict(), r2.to_dict())

    def test_evaluate_missing_pipeline(self):
        with self.assertRaises(PipelineEvaluationError):
            self.evaluator.evaluate("nonexistent")

    def test_evaluate_all_empty(self):
        empty_repo = PipelineRepository()
        ev = ResearchEvaluator(empty_repo)
        self.assertEqual(ev.evaluate_all(), ())

    def test_evaluate_all_returns_sorted(self):
        reports = self.evaluator.evaluate_all()
        self.assertGreater(len(reports), 0)
        for i in range(1, len(reports)):
            self.assertGreaterEqual(
                reports[i].evaluation_id, reports[i - 1].evaluation_id
            )

    def test_evaluate_all_deterministic(self):
        r1 = self.evaluator.evaluate_all()
        r2 = self.evaluator.evaluate_all()
        self.assertEqual(r1, r2)

    def test_compare_same(self):
        r = self.evaluator.evaluate(self.pipeline_id)
        result = ResearchEvaluator.compare(r, r)
        self.assertEqual(result["winner"], "tie")
        self.assertEqual(result["overall_delta"], 0.0)

    def test_compare_different(self):
        report2 = _make_report(pipeline_id="test_pipeline_2")
        repo2 = _make_repo([self.report, report2])
        ev = ResearchEvaluator(repo2)
        results = ev.evaluate_all()
        self.assertEqual(len(results), 2)
        result = ResearchEvaluator.compare(results[0], results[1])
        self.assertIn(result["winner"], ["a", "b", "tie"])

    def test_compare_rejects_non_reports(self):
        with self.assertRaises(PipelineEvaluationError):
            ResearchEvaluator.compare("not_a_report", "not_a_report")  # type: ignore

    def test_repository_property(self):
        self.assertIs(self.evaluator.repository, self.repo)


# ===================================================================
# TestEvaluationImmutability
# ===================================================================


class TestEvaluationImmutability(unittest.TestCase):
    def test_report_frozen(self):
        score = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        eid = _evaluation_id(score, "")
        report = EvaluationReport(
            eid, "p1", score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
        )
        with self.assertRaises(FrozenInstanceError):
            report.pipeline_id = "x"  # type: ignore

    def test_metadata_mutation_raises(self):
        score = EvaluationScore(
            "p1", 0.8, 0.7, 0.6, 0.72, "B+", metadata={"key": "value"}
        )
        with self.assertRaises(TypeError):
            score.metadata["key"] = "new_value"  # type: ignore

    def test_immutable_after_deserialization(self):
        score = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        eid = _evaluation_id(score, "")
        original = EvaluationReport(
            eid, "p1", score, "2024-01-01T00:00:00Z", EVALUATION_VERSION
        )
        restored = EvaluationReport.from_dict(original.to_dict())
        with self.assertRaises(FrozenInstanceError):
            restored.pipeline_id = "x"  # type: ignore


# ===================================================================
# TestEvaluationFailures
# ===================================================================


class TestEvaluationFailures(unittest.TestCase):
    def test_missing_pipeline_raises(self):
        repo = PipelineRepository()
        ev = ResearchEvaluator(repo)
        with self.assertRaises(PipelineEvaluationError):
            ev.evaluate("nonexistent")

    def test_invalid_score_raises(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationScore(
                pipeline_id="p1",
                reproducibility_score="invalid",  # type: ignore
                stability_score=0.7,
                evidence_score=0.6,
                overall_score=0.72,
                grade="B+",
            )

    def test_empty_metadata_handled(self):
        score = EvaluationScore(
            pipeline_id="p1",
            reproducibility_score=0.8,
            stability_score=0.7,
            evidence_score=0.6,
            overall_score=0.72,
            grade="B+",
            metadata={},
        )
        self.assertEqual(dict(score.metadata), {})

    def test_from_dict_missing_key_raises(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationScore.from_dict({"pipeline_id": "p1"})

    def test_from_dict_malformed_raises(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationScore.from_dict("not_a_mapping")  # type: ignore

    def test_report_from_dict_missing_key_raises(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationReport.from_dict({"evaluation_id": "e1"})

    def test_report_from_dict_malformed_score_raises(self):
        with self.assertRaises(InvalidEvaluationError):
            EvaluationReport.from_dict({
                "evaluation_id": "e1",
                "pipeline_id": "p1",
                "score": "not_a_score",
                "created_at": "",
                "version": "1.0.0",
            })


# ===================================================================
# TestEvaluationDeterminism
# ===================================================================


class TestEvaluationDeterminism(unittest.TestCase):
    """Prove: same PipelineRecord -> identical EvaluationReport across calls."""

    def test_identical_calls_identical_report(self):
        report = _make_report()
        repo = _make_repo([report])
        ev = ResearchEvaluator(repo)
        pid = repo.list()[0].pipeline_id

        r1 = ev.evaluate(pid)
        r2 = ev.evaluate(pid)

        self.assertEqual(r1, r2)
        self.assertEqual(hash(r1), hash(r2))
        self.assertEqual(r1.to_dict(), r2.to_dict())
        self.assertEqual(
            json.dumps(r1.to_dict(), sort_keys=True),
            json.dumps(r2.to_dict(), sort_keys=True),
        )

    def test_identical_calls_identical_hash(self):
        report = _make_report()
        repo = _make_repo([report])
        ev = ResearchEvaluator(repo)
        pid = repo.list()[0].pipeline_id

        r1 = ev.evaluate(pid)
        r2 = ev.evaluate(pid)

        s1 = json.dumps(r1.to_dict(), sort_keys=True, separators=(",", ":"))
        s2 = json.dumps(r2.to_dict(), sort_keys=True, separators=(",", ":"))
        self.assertEqual(s1, s2)
        self.assertEqual(
            hashlib.sha256(s1.encode("utf-8")).hexdigest(),
            hashlib.sha256(s2.encode("utf-8")).hexdigest(),
        )

    def test_identical_scores_identical_evaluation_id(self):
        score = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        eid1 = _evaluation_id(score, "2024-01-01T00:00:00Z")
        eid2 = _evaluation_id(score, "2024-01-01T00:00:00Z")
        self.assertEqual(eid1, eid2)

    def test_different_metadata_different_evaluation_id(self):
        score = EvaluationScore("p1", 0.8, 0.7, 0.6, 0.72, "B+")
        eid1 = _evaluation_id(score, "")
        score2 = EvaluationScore("p2", 0.8, 0.7, 0.6, 0.72, "B+")
        eid2 = _evaluation_id(score2, "")
        self.assertNotEqual(eid1, eid2)


# ===================================================================
# TestEvaluationDependencyAudit
# ===================================================================


class TestEvaluationDependencyAudit(unittest.TestCase):
    """Verify evaluation module uses only stdlib."""

    def test_no_forbidden_imports(self):
        import ast
        import os

        forbidden = {
            "numpy", "pandas", "sklearn", "torch", "tensorflow",
            "openai", "llm", "pickle", "sqlite", "random", "uuid",
            "time",
        }
        eval_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "evaluation",
        )
        for root, dirs, files in os.walk(eval_dir):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_name = alias.name.split(".")[0]
                            if root_name in forbidden:
                                self.fail(
                                    f"forbidden import in {fn}: {alias.name}"
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_name = node.module.split(".")[0]
                            if root_name in forbidden:
                                self.fail(
                                    f"forbidden import in {fn}: {node.module}"
                                )

    def test_stdlib_only_imports(self):
        import ast
        import os

        allowed_roots = {
            "__future__",
            "hashlib",
            "json",
            "dataclasses",
            "typing",
            "enum",
            "math",
            "types",
            "researchos",
        }
        eval_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "evaluation",
        )
        for root, dirs, files in os.walk(eval_dir):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_name = alias.name.split(".")[0]
                            if root_name not in allowed_roots:
                                self.fail(
                                    f"non-stdlib import in {fn}: {alias.name}"
                                )
                    elif isinstance(node, ast.ImportFrom):
                        # Only audit absolute imports (node.level == 0).
                        # Relative imports (e.g. ``from .contracts import ...``)
                        # carry the module name without a leading dot, so they
                        # must be skipped to avoid false positives.
                        if node.level == 0 and node.module:
                            root_name = node.module.split(".")[0]
                            if root_name not in allowed_roots:
                                self.fail(
                                    f"non-stdlib import in {fn}: {node.module}"
                                )


if __name__ == "__main__":
    unittest.main()
