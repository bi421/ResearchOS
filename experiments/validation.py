"""
ExperimentValidation — validate experiment results against expected outcomes.

Purpose:
    ExperimentValidation compares the results of an experiment run against
    expected outcomes, benchmarks, or statistical criteria. This is the
    "Result → Validation" step in the experiment workflow.

Based on Article XVII: Object Model — Experiment Layer.
Based on Article XII: Validation Engine.

Guarantees:
    - Deterministic: Same results + criteria → same validation outcome
    - Auditable: Full lifecycle tracking
    - Repeatable: All criteria captured for re-validation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.experiments.contracts import MetricDefinition, ValidationStatus


class ExperimentValidation(BaseObject):
    """
    Validation of experiment results against expected outcomes.

    Compares computed metrics against:
        - Target values (did we hit the expected metric?)
        - Benchmarks (how did we compare to a baseline?)
        - Statistical significance (is the result meaningful?)
        - Consistency (are results stable across runs?)

    Attributes:
        experiment_id: Link to the Experiment being validated.
        run_id: Link to the specific ExperimentRun (optional — can validate across runs).
        hypothesis_id: Link to the QuantHypothesis being tested.
        validation_type: Type of validation (Target, Benchmark, Statistical, Consistency).
        criteria: Dict of validation criteria (metric_name -> expected/tolerance).
        results: Dict of validation results per metric.
        overall_status: Overall validation outcome (Passed, Failed, Inconclusive).
        confidence: Confidence in the validation (0.0-1.0).
        findings: List of findings from validation.
        validation_trace: How validation was performed.
    """

    def __init__(
        self,
        experiment_id: str,
        hypothesis_id: str,
        run_id: Optional[str] = None,
        validation_type: str = "Target",
        criteria: Optional[Dict[str, Dict[str, Any]]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ExperimentValidation|{experiment_id}|{validation_type}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.experiment_id = experiment_id
        self.hypothesis_id = hypothesis_id
        self.run_id = run_id
        self.validation_type = validation_type
        self.criteria: Dict[str, Dict[str, Any]] = criteria or {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.overall_status = ValidationStatus.PENDING
        self.confidence: float = 0.0
        self.findings: List[str] = []
        self.validation_trace: str = ""

        self.lifecycle.transition(
            LifecycleStage.INITIATED,
            reason="Experiment validation initiated",
        )

    def validate_against_benchmark(
        self,
        result_metrics: Dict[str, float],
        benchmark_metrics: Dict[str, float],
        metric_definitions: Optional[List[MetricDefinition]] = None,
    ) -> None:
        """
        Validate results against a benchmark.

        Compares each metric in the result against the benchmark value
        using the metric definitions (higher_is_better) to determine pass/fail.

        Args:
            result_metrics: Dict of metric_name -> computed value.
            benchmark_metrics: Dict of metric_name -> benchmark value.
            metric_definitions: Optional list of metric definitions for context.
        """
        passed_count = 0
        total_count = 0
        metric_defs = {m.name: m for m in (metric_definitions or [])}

        for metric_name, result_value in result_metrics.items():
            if metric_name not in benchmark_metrics:
                continue

            benchmark_value = benchmark_metrics[metric_name]
            total_count += 1

            # Determine pass/fail based on higher_is_better
            higher_is_better = True
            if metric_name in metric_defs:
                higher_is_better = metric_defs[metric_name].higher_is_better

            if higher_is_better:
                passed = result_value >= benchmark_value
            else:
                passed = result_value <= benchmark_value

            self.results[metric_name] = {
                "result": result_value,
                "benchmark": benchmark_value,
                "passed": passed,
                "higher_is_better": higher_is_better,
            }

            if passed:
                passed_count += 1

        # Determine overall status
        if total_count == 0:
            self.overall_status = ValidationStatus.INCONCLUSIVE
            self.findings.append("No comparable metrics found between result and benchmark")
        elif passed_count == total_count:
            self.overall_status = ValidationStatus.PASSED
            self.findings.append(f"All {passed_count}/{total_count} metrics met benchmark")
        elif passed_count >= total_count * 0.5:
            self.overall_status = ValidationStatus.PASSED
            self.findings.append(f"Majority {passed_count}/{total_count} metrics met benchmark")
        else:
            self.overall_status = ValidationStatus.FAILED
            self.findings.append(f"Only {passed_count}/{total_count} metrics met benchmark")

        self.confidence = passed_count / max(total_count, 1)
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Benchmark validation: {self.overall_status.value} "
            f"({passed_count}/{total_count} metrics passed)",
        )

    def validate_against_targets(
        self,
        result_metrics: Dict[str, float],
        metric_definitions: Optional[List[MetricDefinition]] = None,
    ) -> None:
        """
        Validate results against target values defined in metric definitions.

        Args:
            result_metrics: Dict of metric_name -> computed value.
            metric_definitions: List of metric definitions with target/tolerance.
        """
        if not metric_definitions:
            self.overall_status = ValidationStatus.INCONCLUSIVE
            self.findings.append("No metric definitions with targets provided")
            return

        passed_count = 0
        total_count = 0

        for metric_def in metric_definitions:
            if metric_def.target is None:
                continue
            if metric_def.name not in result_metrics:
                continue

            total_count += 1
            result_value = result_metrics[metric_def.name]
            tolerance = metric_def.tolerance or 0.0

            lower = metric_def.target - tolerance
            upper = metric_def.target + tolerance
            passed = lower <= result_value <= upper

            self.results[metric_def.name] = {
                "result": result_value,
                "target": metric_def.target,
                "tolerance": tolerance,
                "passed": passed,
            }

            if passed:
                passed_count += 1

        if total_count == 0:
            self.overall_status = ValidationStatus.INCONCLUSIVE
            self.findings.append("No metrics with targets found in results")
        elif passed_count == total_count:
            self.overall_status = ValidationStatus.PASSED
        elif passed_count == 0:
            self.overall_status = ValidationStatus.FAILED
        else:
            self.overall_status = ValidationStatus.INCONCLUSIVE

        self.confidence = passed_count / max(total_count, 1)
        self.validation_trace = (
            f"Target validation: {self.overall_status.value} "
            f"({passed_count}/{total_count} targets met)"
        )

        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=self.validation_trace,
        )

    def validate_statistical_significance(
        self,
        result_value: float,
        expected_value: float,
        std_dev: float,
        significance_level: float = 0.05,
        metric_name: str = "",
    ) -> None:
        """
        Validate statistical significance of a result.

        Uses a simple z-test equivalent: if the result is more than
        `z_critical` standard deviations from the expected value, the
        difference is considered statistically significant.

        Args:
            result_value: The computed result value.
            expected_value: The expected value under null hypothesis.
            std_dev: Standard deviation of the metric.
            significance_level: Alpha level (default 0.05).
            metric_name: Optional name for the metric being validated.
        """
        if std_dev <= 0:
            self.results[metric_name or "statistical"] = {
                "result": result_value,
                "expected": expected_value,
                "passed": False,
                "reason": "Zero standard deviation — cannot assess significance",
            }
            return

        # Z-critical for two-tailed test at given significance level
        # Approximate: 1.96 for alpha=0.05, 1.645 for alpha=0.10, 2.576 for alpha=0.01
        z_critical_map = {0.01: 2.576, 0.05: 1.96, 0.10: 1.645}
        z_critical = z_critical_map.get(significance_level, 1.96)

        z_score = abs(result_value - expected_value) / std_dev
        is_significant = z_score > z_critical

        metric_key = metric_name or "statistical"
        self.results[metric_key] = {
            "result": result_value,
            "expected": expected_value,
            "std_dev": std_dev,
            "z_score": round(z_score, 4),
            "z_critical": z_critical,
            "significance_level": significance_level,
            "is_significant": is_significant,
        }

        if is_significant:
            self.overall_status = ValidationStatus.PASSED
            self.findings.append(
                f"Result {result_value} is significantly different "
                f"from expected {expected_value} (z={z_score:.2f}, "
                f"critical={z_critical})"
            )
        else:
            self.overall_status = ValidationStatus.INCONCLUSIVE
            self.findings.append(
                f"Result {result_value} is NOT significantly different "
                f"from expected {expected_value} (z={z_score:.2f}, "
                f"critical={z_critical})"
            )

        self.confidence = min(abs(z_score) / (z_critical * 2), 1.0)
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Statistical validation: {'significant' if is_significant else 'not significant'}",
        )

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "hypothesis_id": self.hypothesis_id,
            "run_id": self.run_id or "",
            "validation_type": self.validation_type,
            "criteria": dict(sorted(self.criteria.items())) if self.criteria else {},
            "results": dict(sorted(self.results.items())) if self.results else {},
            "overall_status": self.overall_status.value,
            "confidence": self.confidence,
            "findings": sorted(self.findings),
            "validation_trace": self.validation_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "experiment_id": self.experiment_id,
                "hypothesis_id": self.hypothesis_id,
                "run_id": self.run_id,
                "validation_type": self.validation_type,
                "criteria": self.criteria,
                "results": self.results,
                "overall_status": self.overall_status.value,
                "confidence": self.confidence,
                "findings": self.findings,
                "validation_trace": self.validation_trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentValidation":
        obj = super().from_dict(data)
        obj.experiment_id = data["experiment_id"]
        obj.hypothesis_id = data["hypothesis_id"]
        obj.run_id = data.get("run_id")
        obj.validation_type = data.get("validation_type", "Target")
        obj.criteria = dict(data.get("criteria", {}))
        obj.results = dict(data.get("results", {}))
        obj.overall_status = ValidationStatus(data.get("overall_status", "Pending"))
        obj.confidence = float(data.get("confidence", 0.0))
        obj.findings = list(data.get("findings", []))
        obj.validation_trace = data.get("validation_trace", "")
        return obj
