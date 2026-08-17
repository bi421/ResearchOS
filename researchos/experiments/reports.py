"""
ExperimentReport — comprehensive reporting for experiment results.

Purpose:
    ExperimentReport generates structured reports that consolidate all
    aspects of an experiment: hypothesis, runs, results, validation,
    and learning. Reports are deterministic and auditable.

Based on Article XVII: Object Model — Experiment Layer.

Guarantees:
    - Deterministic: Same inputs → same report
    - Auditable: Full lifecycle tracking
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import deterministic_hash, generate_id
from researchos.core.lifecycle import LifecycleStage


class ExperimentReport(BaseObject):
    """
    Comprehensive report for an experiment.

    Consolidates all aspects of an experiment into a single report:
        - Experiment definition summary
        - Hypothesis summary
        - Run summaries (best, average, worst)
        - Metrics summary
        - Validation summary
        - Learning summary

    Attributes:
        experiment_id: Link to the Experiment.
        hypothesis_id: Link to the QuantHypothesis.
        title: Report title.
        summary: Executive summary of the experiment.
        run_ids: IDs of all runs included in the report.
        best_run_id: ID of the best-performing run.
        metrics_summary: Summary of key metrics across runs.
        validation_summary: Summary of validation results.
        learning_summary: Summary of learning records.
        num_runs: Total number of runs.
        num_passed_runs: Number of successful runs.
        num_failed_runs: Number of failed runs.
        report_hash: Deterministic hash of the report content.
        report_trace: How this report was generated.
        status: Draft or Final.
    """

    def __init__(
        self,
        experiment_id: str,
        hypothesis_id: str,
        title: str = "",
        summary: str = "",
        run_ids: Optional[List[str]] = None,
        best_run_id: Optional[str] = None,
        metrics_summary: Optional[Dict[str, Any]] = None,
        validation_summary: Optional[Dict[str, Any]] = None,
        learning_summary: Optional[Dict[str, Any]] = None,
        report_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ExperimentReport|{experiment_id}|{title}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.experiment_id = experiment_id
        self.hypothesis_id = hypothesis_id
        self.title = title
        self.summary = summary
        self.run_ids: List[str] = run_ids or []
        self.best_run_id = best_run_id
        self.metrics_summary: Dict[str, Any] = metrics_summary or {}
        self.validation_summary: Dict[str, Any] = validation_summary or {}
        self.learning_summary: Dict[str, Any] = learning_summary or {}
        self.num_runs: int = 0
        self.num_passed_runs: int = 0
        self.num_failed_runs: int = 0
        self.report_hash: str = ""
        self.report_trace = report_trace
        self.status = "Draft"

        self.lifecycle.transition(
            LifecycleStage.DRAFT,
            reason="Experiment report created",
        )

    def finalize(self) -> None:
        """Mark the report as final."""
        self.status = "Final"
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.FINAL,
            reason="Experiment report finalized",
        )

    def _update_hash(self) -> None:
        """Compute the deterministic hash of this report."""
        content = self._to_hashable_dict()
        self.report_hash = deterministic_hash(content)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "summary": self.summary,
            "run_ids": sorted(self.run_ids),
            "best_run_id": self.best_run_id or "",
            "metrics_summary": dict(sorted(self.metrics_summary.items()))
            if self.metrics_summary
            else {},
            "validation_summary": dict(sorted(self.validation_summary.items()))
            if self.validation_summary
            else {},
            "learning_summary": dict(sorted(self.learning_summary.items()))
            if self.learning_summary
            else {},
            "num_runs": self.num_runs,
            "num_passed_runs": self.num_passed_runs,
            "num_failed_runs": self.num_failed_runs,
            "report_trace": self.report_trace,
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "experiment_id": self.experiment_id,
                "hypothesis_id": self.hypothesis_id,
                "title": self.title,
                "summary": self.summary,
                "run_ids": self.run_ids,
                "best_run_id": self.best_run_id,
                "metrics_summary": self.metrics_summary,
                "validation_summary": self.validation_summary,
                "learning_summary": self.learning_summary,
                "num_runs": self.num_runs,
                "num_passed_runs": self.num_passed_runs,
                "num_failed_runs": self.num_failed_runs,
                "report_hash": self.report_hash,
                "report_trace": self.report_trace,
                "status": self.status,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentReport":
        obj = super().from_dict(data)
        obj.experiment_id = data["experiment_id"]
        obj.hypothesis_id = data["hypothesis_id"]
        obj.title = data.get("title", "")
        obj.summary = data.get("summary", "")
        obj.run_ids = list(data.get("run_ids", []))
        obj.best_run_id = data.get("best_run_id")
        obj.metrics_summary = dict(data.get("metrics_summary", {}))
        obj.validation_summary = dict(data.get("validation_summary", {}))
        obj.learning_summary = dict(data.get("learning_summary", {}))
        obj.num_runs = int(data.get("num_runs", 0))
        obj.num_passed_runs = int(data.get("num_passed_runs", 0))
        obj.num_failed_runs = int(data.get("num_failed_runs", 0))
        obj.report_hash = data.get("report_hash", "")
        obj.report_trace = data.get("report_trace", "")
        obj.status = data.get("status", "Draft")
        return obj
