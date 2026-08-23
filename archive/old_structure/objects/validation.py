"""
Validation objects — the evaluation of research against actual market outcomes.

Based on Article XVII: Object Model — Validation Layer.
Based on Article XII: Validation Engine.

Validation is the systematic comparison of research outputs with actual
market outcomes to measure quality, identify errors, and calibrate confidence.
"""

from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class Validation(BaseObject):
    """
    The evaluation of research against actual market outcomes.

    Based on Article XVII: Object Model — Validation.

    Validation compares each research scenario and target prediction
    against what actually happened in the market, producing quality
    scores and error analysis.

    Attributes:
        research_id: Link to Research being validated
        research_report_id: Link to ResearchReport
        validation_date: When validation was performed
        time_horizon: The time period being validated
        overall_status: Accurate, Partially Accurate, or Inaccurate
        quality_score: Overall quality score (0.0-1.0)
        scenario_results: Results for each scenario
        target_results: Results for each target prediction
        failure_analysis_id: Link to FailureAnalysis (if applicable)
        statistics_update_id: Link to statistics update
        validation_trace: How validation was performed
    """

    def __init__(
        self,
        research_id: str,
        research_report_id: str,
        time_horizon: str = "",
        overall_status: str = "In Progress",
        quality_score: float = 0.0,
        scenario_results: list[dict[str, Any]] | None = None,
        target_results: list[dict[str, Any]] | None = None,
        failure_analysis_id: str | None = None,
        statistics_update_id: str | None = None,
        validation_trace: str = "",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"Validation|{research_id}|{research_report_id}|{time_horizon}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.research_report_id = research_report_id
        self.validation_date = utc_now()
        self.time_horizon = time_horizon
        self.overall_status = overall_status
        self.quality_score = quality_score
        self.scenario_results: list[dict[str, Any]] = scenario_results or []
        self.target_results: list[dict[str, Any]] = target_results or []
        self.failure_analysis_id = failure_analysis_id
        self.statistics_update_id = statistics_update_id
        self.validation_trace = validation_trace

        self.lifecycle.transition(
            LifecycleStage.IN_PROGRESS,
            reason="Validation initiated",
        )

    def complete(self, quality_score: float, overall_status: str) -> None:
        """Complete the validation with a quality score and status."""
        self.quality_score = quality_score
        self.overall_status = overall_status
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Validation completed: {overall_status} ({quality_score:.2f})",
        )

    def add_scenario_result(self, result: dict[str, Any]) -> None:
        """Add a scenario validation result."""
        self.scenario_results.append(result)

    def add_target_result(self, result: dict[str, Any]) -> None:
        """Add a target prediction validation result."""
        self.target_results.append(result)

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "research_report_id": self.research_report_id,
            "time_horizon": self.time_horizon,
            "overall_status": self.overall_status,
            "quality_score": self.quality_score,
            "scenario_results": self.scenario_results,
            "target_results": self.target_results,
            "failure_analysis_id": self.failure_analysis_id or "",
            "statistics_update_id": self.statistics_update_id or "",
            "validation_trace": self.validation_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "research_report_id": self.research_report_id,
                "validation_date": self.validation_date.isoformat(),
                "time_horizon": self.time_horizon,
                "overall_status": self.overall_status,
                "quality_score": self.quality_score,
                "scenario_results": self.scenario_results,
                "target_results": self.target_results,
                "failure_analysis_id": self.failure_analysis_id,
                "statistics_update_id": self.statistics_update_id,
                "validation_trace": self.validation_trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> Validation:
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.research_report_id = data["research_report_id"]
        obj.validation_date = parse_timestamp(data["validation_date"]) if data.get("validation_date") else None
        obj.time_horizon = data.get("time_horizon", "")
        obj.overall_status = data.get("overall_status", "In Progress")
        obj.quality_score = data.get("quality_score", 0.0)
        obj.scenario_results = list(data.get("scenario_results", []))
        obj.target_results = list(data.get("target_results", []))
        obj.failure_analysis_id = data.get("failure_analysis_id")
        obj.statistics_update_id = data.get("statistics_update_id")
        obj.validation_trace = data.get("validation_trace", "")
        return obj


class FailureAnalysis(BaseObject):
    """
    Root cause analysis of research failures.

    Based on Article XVII: Object Model — FailureAnalysis.

    FailureAnalysis identifies why research was wrong by categorizing
    errors into root causes and assessing their severity. Each failure
    is analyzed for preventability and improvement potential.

    Attributes:
        validation_id: Link to Validation
        research_id: Link to Research
        failures: List of failure details with root causes
        root_causes: Identified root causes
        severity_scores: Severity assessment per failure
        improvement_areas: Areas for improvement
        failure_trace: How the analysis was performed
    """

    def __init__(
        self,
        validation_id: str,
        research_id: str,
        failures: list[dict[str, Any]] | None = None,
        root_causes: list[str] | None = None,
        severity_scores: list[dict[str, Any]] | None = None,
        improvement_areas: list[str] | None = None,
        failure_trace: str = "",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"FailureAnalysis|{validation_id}|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.validation_id = validation_id
        self.research_id = research_id
        self.failures: list[dict[str, Any]] = failures or []
        self.root_causes: list[str] = root_causes or []
        self.severity_scores: list[dict[str, Any]] = severity_scores or []
        self.improvement_areas: list[str] = improvement_areas or []
        self.failure_trace = failure_trace

        self.lifecycle.transition(
            LifecycleStage.INITIATED,
            reason="Failure analysis initiated",
        )

    def add_failure(
        self,
        description: str,
        category: str,
        severity: float,
        root_cause: str,
        preventable: bool = False,
    ) -> None:
        """Add a failure record to the analysis."""
        failure = {
            "description": description,
            "category": category,
            "severity": severity,
            "root_cause": root_cause,
            "preventable": preventable,
        }
        self.failures.append(failure)
        self.severity_scores.append(
            {
                "failure": description,
                "severity": severity,
                "category": category,
            }
        )
        if root_cause not in self.root_causes:
            self.root_causes.append(root_cause)

    def complete(self) -> None:
        """Mark the failure analysis as complete."""
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Failure analysis completed: {len(self.failures)} failures, {len(self.root_causes)} root causes",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "validation_id": self.validation_id,
            "research_id": self.research_id,
            "failures": self.failures,
            "root_causes": sorted(self.root_causes),
            "severity_scores": self.severity_scores,
            "improvement_areas": sorted(self.improvement_areas),
            "failure_trace": self.failure_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "validation_id": self.validation_id,
                "research_id": self.research_id,
                "failures": self.failures,
                "root_causes": self.root_causes,
                "severity_scores": self.severity_scores,
                "improvement_areas": self.improvement_areas,
                "failure_trace": self.failure_trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> FailureAnalysis:
        obj = super().from_dict(data)
        obj.validation_id = data["validation_id"]
        obj.research_id = data["research_id"]
        obj.failures = list(data.get("failures", []))
        obj.root_causes = list(data.get("root_causes", []))
        obj.severity_scores = list(data.get("severity_scores", []))
        obj.improvement_areas = list(data.get("improvement_areas", []))
        obj.failure_trace = data.get("failure_trace", "")
        return obj
