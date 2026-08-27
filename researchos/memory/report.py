"""
MarketMemoryReport — consolidated report of market memory analysis.

Every generated report contains:
    - Evidence references
    - Historical sources
    - Calculation method
    - Timestamp
    - Audit entry

Based on the ResearchOS reporting framework with full auditability.
"""

from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class MarketMemoryReport(BaseObject):
    """
    A consolidated report of market memory analysis.

    Combines scenario matching results, outcome analysis, and
    full audit trail for institutional use.

    Attributes:
        report_type: Type of report ("ScenarioMatch", "OutcomeAnalysis", "FullAnalysis")
        target_snapshot_id: The MarketSnapshot ID that was analyzed
        matched_scenarios: List of MatchResult dicts
        outcome_analysis: OutcomeAnalysisResult dict or None
        feature_weights: The feature weights used for matching
        calculation_method: Description of the calculation method
        evidence_ids: Evidence references supporting this report
        historical_sources: Source dataset identifiers
        confidence_basis: Explanation of confidence determination
        limitations: Known limitations of this analysis
        audit_entries: Audit trail entries
        generated_at: When the report was generated
        status: Draft, Final, or Archived
    """

    def __init__(
        self,
        report_type: str,
        target_snapshot_id: str = "",
        matched_scenarios: list[dict[str, Any]] | None = None,
        outcome_analysis: dict[str, Any] | None = None,
        feature_weights: dict[str, float] | None = None,
        calculation_method: str = "WeightedFeatureComparison",
        evidence_ids: list[str] | None = None,
        historical_sources: list[str] | None = None,
        confidence_basis: str = "",
        limitations: list[str] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"MarketMemoryReport|{report_type}|{target_snapshot_id}|{utc_now().isoformat()}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.report_type = report_type
        self.target_snapshot_id = target_snapshot_id
        self.matched_scenarios: list[dict[str, Any]] = matched_scenarios or []
        self.outcome_analysis: dict[str, Any] | None = outcome_analysis
        self.feature_weights: dict[str, float] = dict(feature_weights) if feature_weights else {}
        self.calculation_method = calculation_method
        self.evidence_ids: list[str] = evidence_ids or []
        self.historical_sources: list[str] = historical_sources or []
        self.confidence_basis = confidence_basis
        self.limitations: list[str] = limitations or []
        self.audit_entries: list[dict[str, Any]] = []
        self.generated_at = utc_now()
        self.status = "Draft"

        self.lifecycle.transition(
            LifecycleStage.DRAFT,
            reason=f"MarketMemoryReport created: {report_type}",
        )

    def add_audit_entry(
        self,
        action: str,
        actor: str = "MarketMemory",
        details: str = "",
    ) -> None:
        """Add an audit entry to the report."""
        self.audit_entries.append(
            {
                "timestamp": utc_now().isoformat(),
                "actor": actor,
                "action": action,
                "details": details,
            }
        )

    def finalize(self) -> None:
        """Mark the report as final."""
        self.status = "Final"
        self.lifecycle.transition(
            LifecycleStage.FINAL,
            reason="MarketMemoryReport finalized",
        )

    def _to_hashable_dict(self) -> dict[str, Any]:
        return {
            "report_type": self.report_type,
            "target_snapshot_id": self.target_snapshot_id,
            "matched_scenarios": (
                sorted(
                    [m["scenario_id"] for m in self.matched_scenarios],
                )
                if self.matched_scenarios
                else []
            ),
            "outcome_analysis": str(self.outcome_analysis),
            "feature_weights": dict(sorted(self.feature_weights.items())),
            "calculation_method": self.calculation_method,
            "evidence_ids": sorted(self.evidence_ids),
            "historical_sources": sorted(self.historical_sources),
            "confidence_basis": self.confidence_basis,
            "limitations": sorted(self.limitations),
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "report_type": self.report_type,
                "target_snapshot_id": self.target_snapshot_id,
                "matched_scenarios": self.matched_scenarios,
                "outcome_analysis": self.outcome_analysis,
                "feature_weights": self.feature_weights,
                "calculation_method": self.calculation_method,
                "evidence_ids": self.evidence_ids,
                "historical_sources": self.historical_sources,
                "confidence_basis": self.confidence_basis,
                "limitations": self.limitations,
                "audit_entries": self.audit_entries,
                "generated_at": self.generated_at.isoformat(),
                "status": self.status,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> MarketMemoryReport:
        obj = super().from_dict(data)
        obj.report_type = data["report_type"]
        obj.target_snapshot_id = data.get("target_snapshot_id", "")
        obj.matched_scenarios = list(data.get("matched_scenarios", []))
        obj.outcome_analysis = data.get("outcome_analysis")
        obj.feature_weights = dict(data.get("feature_weights", {}))
        obj.calculation_method = data.get("calculation_method", "WeightedFeatureComparison")
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.historical_sources = list(data.get("historical_sources", []))
        obj.confidence_basis = data.get("confidence_basis", "")
        obj.limitations = list(data.get("limitations", []))
        obj.audit_entries = list(data.get("audit_entries", []))
        obj.generated_at = parse_timestamp(data["generated_at"]) if data.get("generated_at") else utc_now()
        obj.status = data.get("status", "Draft")
        return obj
