"""
Research objects — the top-level research entities.

Based on Article XVII: Object Model — Decision Support Layer.
Based on Article XVI: Scientific Reasoning Framework — Decision Support Layer.

Research is the top-level entity that encompasses an entire research cycle,
from question formulation through to report generation.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class Research(BaseObject):
    """
    The top-level research entity encompassing an entire research cycle.

    Based on Article XVII: Object Model — Research.

    A Research object contains all other research objects and tracks
    the complete research lifecycle from initiation to validation.

    Attributes:
        question: The research question
        timestamp: When research was initiated
        time_horizon: Intraday, Daily, Weekly, Monthly, Quarterly
        asset: Asset being researched
        methodology_version: Version of the methodology used
        status: In Progress, Complete, Validated, or Archived
        observation_ids: All observations collected
        evidence_registry_id: Link to EvidenceRegistry
        hypothesis_set_id: Link to HypothesisSet
        scenario_set_id: Link to ScenarioSet
        confidence_report_id: Link to ConfidenceReport
        contradiction_report_id: Link to ContradictionReport
        report_id: Link to ResearchReport
        completed_at: When research was completed
        validated_at: When research was validated
    """

    def __init__(
        self,
        question: str,
        time_horizon: str = "Daily",
        asset: str = "",
        methodology_version: str = "1.0.0",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Research|{question}|{time_horizon}|{asset}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.question = question
        self.timestamp = utc_now()
        self.time_horizon = time_horizon
        self.asset = asset
        self.methodology_version = methodology_version
        self.status = "In Progress"

        # Links to sub-objects
        self.observation_ids: List[str] = []
        self.evidence_registry_id: Optional[str] = None
        self.hypothesis_set_id: Optional[str] = None
        self.scenario_set_id: Optional[str] = None
        self.confidence_report_id: Optional[str] = None
        self.contradiction_report_id: Optional[str] = None
        self.report_id: Optional[str] = None

        # Lifecycle timestamps
        self.completed_at: Optional[datetime] = None
        self.validated_at: Optional[datetime] = None

        self.lifecycle.transition(
            LifecycleStage.IN_PROGRESS,
            reason="Research initiated",
        )

    def complete(self) -> None:
        """Mark this research as complete."""
        self.status = "Complete"
        self.completed_at = utc_now()
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason="Research completed",
        )

    def validate(self) -> None:
        """Mark this research as validated."""
        self.status = "Validated"
        self.validated_at = utc_now()
        self.lifecycle.transition(
            LifecycleStage.ARCHIVED,
            reason="Research validated and archived",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "question": self.question,
            "time_horizon": self.time_horizon,
            "asset": self.asset,
            "methodology_version": self.methodology_version,
            "status": self.status,
            "observation_ids": sorted(self.observation_ids),
            "evidence_registry_id": self.evidence_registry_id or "",
            "hypothesis_set_id": self.hypothesis_set_id or "",
            "scenario_set_id": self.scenario_set_id or "",
            "confidence_report_id": self.confidence_report_id or "",
            "contradiction_report_id": self.contradiction_report_id or "",
            "report_id": self.report_id or "",
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "question": self.question,
            "timestamp": self.timestamp.isoformat(),
            "time_horizon": self.time_horizon,
            "asset": self.asset,
            "methodology_version": self.methodology_version,
            "status": self.status,
            "observation_ids": self.observation_ids,
            "evidence_registry_id": self.evidence_registry_id,
            "hypothesis_set_id": self.hypothesis_set_id,
            "scenario_set_id": self.scenario_set_id,
            "confidence_report_id": self.confidence_report_id,
            "contradiction_report_id": self.contradiction_report_id,
            "report_id": self.report_id,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Research":
        obj = super().from_dict(data)
        obj.question = data["question"]
        obj.timestamp = parse_timestamp(data["timestamp"]) if data.get("timestamp") else None
        obj.time_horizon = data.get("time_horizon", "Daily")
        obj.asset = data.get("asset", "")
        obj.methodology_version = data.get("methodology_version", "1.0.0")
        obj.status = data.get("status", "In Progress")
        obj.observation_ids = list(data.get("observation_ids", []))
        obj.evidence_registry_id = data.get("evidence_registry_id")
        obj.hypothesis_set_id = data.get("hypothesis_set_id")
        obj.scenario_set_id = data.get("scenario_set_id")
        obj.confidence_report_id = data.get("confidence_report_id")
        obj.contradiction_report_id = data.get("contradiction_report_id")
        obj.report_id = data.get("report_id")
        obj.completed_at = parse_timestamp(data["completed_at"]) if data.get("completed_at") else None
        obj.validated_at = parse_timestamp(data["validated_at"]) if data.get("validated_at") else None
        return obj


class ResearchQuestion(BaseObject):
    """
    A specific, testable question that the research aims to answer.

    Based on Article XVII: Object Model — ResearchQuestion.

    Attributes:
        research_id: Link to Research
        question: The specific question
        sub_questions: Decomposed sub-questions
        priority: Importance ranking
        answerable: Whether the question can be answered with available data
    """

    def __init__(
        self,
        research_id: str,
        question: str,
        sub_questions: Optional[List[str]] = None,
        priority: float = 0.0,
        answerable: bool = True,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ResearchQuestion|{research_id}|{question}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.question = question
        self.sub_questions: List[str] = sub_questions or []
        self.priority = priority
        self.answerable = answerable

        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason="Research question created",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "question": self.question,
            "sub_questions": sorted(self.sub_questions),
            "priority": self.priority,
            "answerable": self.answerable,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "research_id": self.research_id,
            "question": self.question,
            "sub_questions": self.sub_questions,
            "priority": self.priority,
            "answerable": self.answerable,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchQuestion":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.question = data["question"]
        obj.sub_questions = list(data.get("sub_questions", []))
        obj.priority = data.get("priority", 0.0)
        obj.answerable = data.get("answerable", True)
        return obj


class ResearchReport(BaseObject):
    """
    The final output of the research process, presented to the human trader.

    Based on Article XVII: Object Model — ResearchReport.

    ResearchOS NEVER recommends trades. It provides:
        - Research: Analysis of market conditions
        - Scenarios: Probabilistic outcomes
        - Confidence: Assessment of certainty
        - Risks: Identification of potential pitfalls
        - Unknowns: Explicit acknowledgment of limitations

    Attributes:
        research_id: Link to Research
        title: Report title
        executive_summary: Brief summary for the trader
        research_question: The question being answered
        hypotheses: Summary of hypotheses
        evidence_summary: Summary of evidence
        analyses: Summary of macro, technical, liquidity analyses
        narrative: The market narrative
        scenarios: Summary of scenarios with probabilities
        confidence: Confidence assessment
        contradictions: Identified contradictions
        risk_factors: Key risk factors
        invalidation_conditions: Conditions that would invalidate the research
        known_unknowns: Explicitly stated unknowns
        open_questions: Questions needing further research
        methodology_version: Version of methodology used
        format: Markdown, PDF, or JSON
        status: Draft, Final, or Archived
    """

    def __init__(
        self,
        research_id: str,
        title: str = "",
        executive_summary: str = "",
        research_question: str = "",
        hypotheses: str = "",
        evidence_summary: str = "",
        analyses: str = "",
        narrative: str = "",
        scenarios: str = "",
        confidence: str = "",
        contradictions: str = "",
        risk_factors: Optional[List[str]] = None,
        invalidation_conditions: Optional[List[str]] = None,
        known_unknowns: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
        methodology_version: str = "1.0.0",
        format: str = "Markdown",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ResearchReport|{research_id}|{title}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.title = title
        self.executive_summary = executive_summary
        self.research_question = research_question
        self.hypotheses = hypotheses
        self.evidence_summary = evidence_summary
        self.analyses = analyses
        self.narrative = narrative
        self.scenarios = scenarios
        self.confidence = confidence
        self.contradictions = contradictions
        self.risk_factors: List[str] = risk_factors or []
        self.invalidation_conditions: List[str] = invalidation_conditions or []
        self.known_unknowns: List[str] = known_unknowns or []
        self.open_questions: List[str] = open_questions or []
        self.methodology_version = methodology_version
        self.format = format
        self.status = "Draft"

        self.lifecycle.transition(
            LifecycleStage.DRAFT,
            reason="Research report created",
        )

    def finalize(self) -> None:
        """Mark this report as final."""
        self.status = "Final"
        self.lifecycle.transition(
            LifecycleStage.FINAL,
            reason="Research report finalized",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "research_question": self.research_question,
            "hypotheses": self.hypotheses,
            "evidence_summary": self.evidence_summary,
            "analyses": self.analyses,
            "narrative": self.narrative,
            "scenarios": self.scenarios,
            "confidence": self.confidence,
            "contradictions": self.contradictions,
            "risk_factors": sorted(self.risk_factors),
            "invalidation_conditions": sorted(self.invalidation_conditions),
            "known_unknowns": sorted(self.known_unknowns),
            "open_questions": sorted(self.open_questions),
            "methodology_version": self.methodology_version,
            "format": self.format,
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "research_id": self.research_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "research_question": self.research_question,
            "hypotheses": self.hypotheses,
            "evidence_summary": self.evidence_summary,
            "analyses": self.analyses,
            "narrative": self.narrative,
            "scenarios": self.scenarios,
            "confidence": self.confidence,
            "contradictions": self.contradictions,
            "risk_factors": self.risk_factors,
            "invalidation_conditions": self.invalidation_conditions,
            "known_unknowns": self.known_unknowns,
            "open_questions": self.open_questions,
            "methodology_version": self.methodology_version,
            "format": self.format,
            "status": self.status,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchReport":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.title = data.get("title", "")
        obj.executive_summary = data.get("executive_summary", "")
        obj.research_question = data.get("research_question", "")
        obj.hypotheses = data.get("hypotheses", "")
        obj.evidence_summary = data.get("evidence_summary", "")
        obj.analyses = data.get("analyses", "")
        obj.narrative = data.get("narrative", "")
        obj.scenarios = data.get("scenarios", "")
        obj.confidence = data.get("confidence", "")
        obj.contradictions = data.get("contradictions", "")
        obj.risk_factors = list(data.get("risk_factors", []))
        obj.invalidation_conditions = list(data.get("invalidation_conditions", []))
        obj.known_unknowns = list(data.get("known_unknowns", []))
        obj.open_questions = list(data.get("open_questions", []))
        obj.methodology_version = data.get("methodology_version", "1.0.0")
        obj.format = data.get("format", "Markdown")
        obj.status = data.get("status", "Draft")
        return obj
