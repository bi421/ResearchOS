"""ResearchAttributionEngine — service for tracing, verifying, and reporting on reasoning attribution.

This engine provides the high-level API for the Attribution Layer.
It wraps a RepositoryInterface and provides deterministic methods for:

- Tracing the full reasoning chain from any conclusion back to observations
- Computing attribution confidence based on chain completeness
- Linking conclusions to similar past market patterns via MarketMemory
- Verifying attribution integrity (all referenced objects exist)
- Generating attribution reports for a research cycle

Every method produces deterministic results that integrate with the
existing audit chain and serialization framework.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from researchos.core.base_object import BaseObject
from researchos.objects.attribution import (
    ATTRIBUTION_COMPLETE_THRESHOLD,
    ATTRIBUTION_PARTIAL_THRESHOLD,
    Attribution,
    AttributionGraph,
)
from researchos.objects.evidence import Evidence, EvidenceRegistry
from researchos.objects.hypothesis import Hypothesis, HypothesisSet
from researchos.objects.interpretation import Interpretation, Narrative
from researchos.objects.observation import Observation
from researchos.objects.process import AuditEntry
from researchos.objects.scenario import Scenario, ScenarioSet
from researchos.objects.confidence import Confidence
from researchos.objects.contradiction import Contradiction
from researchos.objects.research import Research, ResearchReport
from researchos.objects.validation import Validation
from researchos.objects.knowledge import Knowledge, Pattern, Lesson
from researchos.objects.market_memory import (
    MarketEvent,
    MarketStructure,
    LiquidityEvent,
    MarketOutcome,
)
from researchos.repository.interface import RepositoryInterface


# Type-based traversal rules: mapping conclusion types to their parent/input fields
TRAVERSAL_RULES: Dict[str, List[str]] = {
    "Hypothesis": ["research_id", "evidence_ids", "narrative_id"],
    "Scenario": ["hypothesis_id", "supporting_evidence", "dependencies"],
    "Interpretation": ["evidence_ids", "supporting_evidence", "contradicting_evidence"],
    "Narrative": ["interpretations", "research_id"],
    "Confidence": ["target_id"],
    "Contradiction": ["research_id"],
    "ResearchReport": ["research_id"],
    "Validation": ["research_id", "research_report_id"],
    "Knowledge": ["source_references"],
    "Pattern": ["supporting_evidence", "contradicting_evidence"],
    "Lesson": ["supporting_evidence"],
}

# Conclusion types that can have their own Attribution record
ATTRIBUTABLE_TYPES = {
    "Hypothesis",
    "Scenario",
    "Narrative",
    "ResearchReport",
    "Validation",
    "Contradiction",
    "Confidence",
    "Knowledge",
    "Pattern",
    "Lesson",
}


class ResearchAttributionEngine:
    """Service for tracing, verifying, and reporting on reasoning attribution.

    Usage:
        engine = ResearchAttributionEngine(repository)
        attribution = engine.create_attribution(hypothesis_id, "Hypothesis")
        report = engine.get_attribution_report(research_id)
    """

    def __init__(self, repository: RepositoryInterface):
        self.repo = repository

    # ------------------------------------------------------------------
    # Attribution creation
    # ------------------------------------------------------------------

    def create_attribution(
        self,
        conclusion_id: str,
        conclusion_type: str,
        ontology_tags: Optional[List[str]] = None,
    ) -> Attribution:
        """Create a complete attribution record for a conclusion.

        Traces the full reasoning chain from the conclusion back to
        evidence and observations. Computes confidence and status
        automatically.

        Args:
            conclusion_id: ID of the conclusion object.
            conclusion_type: Type of the conclusion.
            ontology_tags: Optional ontology tags.

        Returns:
            A fully populated Attribution object.

        Raises:
            ValueError: If the conclusion object is not found or the type
                        is not attributable.
        """
        if conclusion_type not in ATTRIBUTABLE_TYPES:
            raise ValueError(
                f"Cannot create attribution for type '{conclusion_type}'. "
                f"Attributable types: {sorted(ATTRIBUTABLE_TYPES)}"
            )

        obj = self.repo.get(conclusion_id)
        if obj is None:
            raise ValueError(f"Conclusion object not found: {conclusion_id}")

        # Trace the chain
        reasoning_path, reasoning_object_ids = self._trace_chain(conclusion_id, conclusion_type)

        # Collect evidence and observations
        evidence_ids = self._collect_evidence_ids(reasoning_object_ids)
        observation_ids = self._collect_observation_ids(evidence_ids, reasoning_object_ids)

        # Build human-readable trace
        trace = self._build_trace(reasoning_path)

        # Compute confidence from chain completeness
        confidence = self._compute_chain_confidence(
            conclusion_id, reasoning_object_ids, evidence_ids, observation_ids
        )

        # Determine status
        status = self._determine_status(confidence, reasoning_object_ids)

        attribution = Attribution(
            conclusion_id=conclusion_id,
            conclusion_type=conclusion_type,
            reasoning_path=reasoning_path,
            reasoning_object_ids=reasoning_object_ids,
            evidence_ids=evidence_ids,
            observation_ids=observation_ids,
            confidence=confidence,
            attribution_trace=trace,
            status=status,
            ontology_tags=ontology_tags,
        )

        self.repo.save(attribution)
        self._audit("ATTRIBUTION_CREATED", attribution.id, f"Attribution for {conclusion_type} {conclusion_id[:8]}...")

        return attribution

    # ------------------------------------------------------------------
    # Chain tracing
    # ------------------------------------------------------------------

    def trace_conclusion(self, conclusion_id: str, conclusion_type: str) -> Dict[str, Any]:
        """Trace the full reasoning chain for a conclusion without creating an Attribution.

        Args:
            conclusion_id: ID of the conclusion object.
            conclusion_type: Type of the conclusion.

        Returns:
            Dict with keys: conclusion_id, conclusion_type, reasoning_path,
            reasoning_object_ids, evidence_ids, observation_ids, trace.
        """
        reasoning_path, reasoning_object_ids = self._trace_chain(conclusion_id, conclusion_type)
        evidence_ids = self._collect_evidence_ids(reasoning_object_ids)
        observation_ids = self._collect_observation_ids(evidence_ids, reasoning_object_ids)
        trace = self._build_trace(reasoning_path)

        return {
            "conclusion_id": conclusion_id,
            "conclusion_type": conclusion_type,
            "reasoning_path": reasoning_path,
            "reasoning_object_ids": reasoning_object_ids,
            "evidence_ids": evidence_ids,
            "observation_ids": observation_ids,
            "trace": trace,
        }

    def get_evidence_chain(self, conclusion_id: str) -> List[str]:
        """Get all evidence IDs upstream of a conclusion."""
        obj = self.repo.get(conclusion_id)
        if obj is None:
            return []
        obj_type = type(obj).__name__
        _, object_ids = self._trace_chain(conclusion_id, obj_type)
        return self._collect_evidence_ids(object_ids)

    def get_observation_chain(self, conclusion_id: str) -> List[str]:
        """Get all observation IDs upstream of a conclusion."""
        evidence_ids = self.get_evidence_chain(conclusion_id)
        obj = self.repo.get(conclusion_id)
        obj_type = type(obj).__name__ if obj else ""
        _, object_ids = self._trace_chain(conclusion_id, obj_type)
        return self._collect_observation_ids(evidence_ids, object_ids)

    # ------------------------------------------------------------------
    # Market memory linking
    # ------------------------------------------------------------------

    def link_market_memory(self, attribution_id: str, memory_ids: List[str]) -> Attribution:
        """Link MarketMemory objects to an existing attribution.

        Args:
            attribution_id: ID of the Attribution record.
            memory_ids: List of MarketMemory object IDs.

        Returns:
            The updated Attribution.

        Raises:
            ValueError: If the attribution is not found.
        """
        obj = self.repo.get(attribution_id)
        if obj is None or not isinstance(obj, Attribution):
            raise ValueError(f"Attribution not found: {attribution_id}")

        for mem_id in memory_ids:
            mem_obj = self.repo.get(mem_id)
            if mem_obj is None:
                raise ValueError(f"MarketMemory object not found: {mem_id}")
            obj.link_market_memory(mem_id)

        self.repo.save(obj)
        self._audit(
            "ATTRIBUTION_LINKED",
            attribution_id,
            f"Linked {len(memory_ids)} market memory references",
        )
        return obj

    def find_similar_patterns(
        self,
        attribution_id: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find similar past market patterns linked to this attribution.

        Scans the attribution's market_memory_ids and returns matching
        MarketOutcome objects for performance analysis.

        Args:
            attribution_id: ID of the Attribution record.
            max_results: Maximum number of similar patterns to return.

        Returns:
            List of dicts with market memory object details.
        """
        obj = self.repo.get(attribution_id)
        if obj is None or not isinstance(obj, Attribution):
            return []

        results: List[Dict[str, Any]] = []
        for mem_id in obj.market_memory_ids:
            mem_obj = self.repo.get(mem_id)
            if mem_obj is None:
                continue

            entry = {
                "memory_id": mem_id,
                "memory_type": type(mem_obj).__name__,
            }

            if isinstance(mem_obj, (MarketStructure, LiquidityEvent, MarketEvent)):
                entry["asset"] = getattr(mem_obj, "asset", "")
                entry["event_type"] = getattr(mem_obj, "event_type", "") or getattr(mem_obj, "structure_type", "")
                entry["direction"] = getattr(mem_obj, "direction", "")
                entry["price_level"] = getattr(mem_obj, "price_level", 0.0)

                outcomes = self._get_outcomes_for_event(mem_id)
                if outcomes:
                    entry["outcomes"] = [
                        {
                            "outcome_type": o.outcome_type,
                            "actual_move": o.actual_move,
                            "expected_move": o.expected_move,
                            "confidence": o.confidence,
                        }
                        for o in outcomes
                    ]

            results.append(entry)
            if len(results) >= max_results:
                break

        return results

    # ------------------------------------------------------------------
    # Graph management
    # ------------------------------------------------------------------

    def create_attribution_graph(
        self,
        research_id: str,
        attribution_ids: Optional[List[str]] = None,
    ) -> AttributionGraph:
        """Create an AttributionGraph for a research cycle.

        If attribution_ids is not provided, automatically creates
        attributions for all attributable objects in the cycle.

        Args:
            research_id: ID of the Research object.
            attribution_ids: Optional pre-existing attribution IDs.

        Returns:
            The AttributionGraph.
        """
        if attribution_ids is None:
            attribution_ids = []
            research = self.repo.get(research_id)
            if research is not None and isinstance(research, Research):
                # Walk all attributable sub-objects
                for field in ["hypothesis_set_id", "scenario_set_id",
                              "confidence_report_id", "contradiction_report_id",
                              "report_id"]:
                    obj_id = getattr(research, field, None)
                    if obj_id:
                        sub_obj = self.repo.get(obj_id)
                        if sub_obj is not None:
                            # Get child IDs from the container
                            child_ids = self._get_child_ids(sub_obj)
                            for cid in child_ids:
                                child = self.repo.get(cid)
                                if child is not None:
                                    ctype = type(child).__name__
                                    if ctype in ATTRIBUTABLE_TYPES:
                                        attr = self.create_attribution(cid, ctype)
                                        attribution_ids.append(attr.id)

        graph = AttributionGraph(
            research_id=research_id,
            ontology_tags=["attribution_graph"],
        )
        for aid in attribution_ids:
            attr = self.repo.get(aid)
            if attr is not None and isinstance(attr, Attribution):
                graph.add_attribution(attr)

        self.repo.save(graph)
        self._audit("GRAPH_CREATED", graph.id, f"Attribution graph for research {research_id[:8]}...")
        return graph

    def get_attribution_report(self, research_id: str) -> Dict[str, Any]:
        """Get a full attribution report for a research cycle.

        Args:
            research_id: ID of the Research object.

        Returns:
            Dict with summary statistics and all attributions.
        """
        research = self.repo.get(research_id)
        if research is None:
            return {"research_id": research_id, "error": "Research not found"}

        graphs: List[AttributionGraph] = []
        for obj in self.repo.get_all():
            if isinstance(obj, AttributionGraph) and obj.research_id == research_id:
                graphs.append(obj)

        all_attributions: List[Attribution] = []
        for g in graphs:
            all_attributions.extend(g.attributions)

        # Also find standalone attributions not in a graph
        for obj in self.repo.get_all():
            if isinstance(obj, Attribution) and obj.conclusion_id not in {
                a.conclusion_id for a in all_attributions
            }:
                # Check if it belongs to this research via chain
                chain = self._trace_chain(obj.conclusion_id, obj.conclusion_type)
                for oid in chain[1]:
                    ref = self.repo.get(oid)
                    if isinstance(ref, (Hypothesis, Scenario, Narrative)) and hasattr(ref, "research_id"):
                        if ref.research_id == research_id:
                            all_attributions.append(obj)
                            break

        total = len(all_attributions)
        complete = sum(1 for a in all_attributions if a.status == "Complete")
        partial = sum(1 for a in all_attributions if a.status == "Partial")
        broken = sum(1 for a in all_attributions if a.status == "Broken")
        avg_conf = sum(a.confidence for a in all_attributions) / max(total, 1)

        return {
            "research_id": research_id,
            "total_attributions": total,
            "complete": complete,
            "partial": partial,
            "broken": broken,
            "average_confidence": round(avg_conf, 4),
            "attributions": [
                {
                    "id": a.id,
                    "conclusion_id": a.conclusion_id,
                    "conclusion_type": a.conclusion_type,
                    "confidence": a.confidence,
                    "status": a.status,
                    "evidence_count": len(a.evidence_ids),
                    "observation_count": len(a.observation_ids),
                    "memory_links": len(a.market_memory_ids),
                    "trace": a.attribution_trace[:200],
                }
                for a in sorted(all_attributions, key=lambda x: x.confidence, reverse=True)
            ],
        }

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_attribution(self, attribution_id: str) -> Dict[str, Any]:
        """Verify that all references in an attribution exist.

        Args:
            attribution_id: ID of the Attribution record.

        Returns:
            Integrity report dict.
        """
        obj = self.repo.get(attribution_id)
        if obj is None or not isinstance(obj, Attribution):
            return {"attribution_id": attribution_id, "error": "Attribution not found"}

        available_ids = {o.id for o in self.repo.get_all()}
        report = obj.verify_integrity(available_ids)

        # Update status if needed
        if report["status"] != obj.status:
            obj.update_status(report["status"])
            self.repo.save(obj)

        return {
            "attribution_id": attribution_id,
            **report,
        }

    def verify_graph(self, graph_id: str) -> Dict[str, Any]:
        """Verify integrity of all attributions in a graph.

        Args:
            graph_id: ID of the AttributionGraph.

        Returns:
            Dict with per-attribution reports and summary.
        """
        graph = self.repo.get(graph_id)
        if graph is None or not isinstance(graph, AttributionGraph):
            return {"graph_id": graph_id, "error": "AttributionGraph not found"}

        available_ids = {o.id for o in self.repo.get_all()}
        reports = graph.verify_all(available_ids)

        return {
            "graph_id": graph_id,
            "total": len(reports),
            "all_complete": all(r["complete"] for r in reports),
            "reports": reports,
        }

    # ------------------------------------------------------------------
    # Confidence computation
    # ------------------------------------------------------------------

    def compute_attribution_confidence(
        self,
        conclusion_id: str,
        conclusion_type: str,
    ) -> float:
        """Compute attribution confidence for a conclusion without creating a record.

        Confidence is based on:
        1. Chain completeness (are all steps resolvable?)
        2. Evidence quality (do the linked evidence objects have high confidence?)
        3. Observation coverage (are there direct observations?)

        Args:
            conclusion_id: ID of the conclusion.
            conclusion_type: Type of the conclusion.

        Returns:
            Confidence score (0.0-1.0).
        """
        _, reasoning_object_ids = self._trace_chain(conclusion_id, conclusion_type)
        evidence_ids = self._collect_evidence_ids(reasoning_object_ids)
        observation_ids = self._collect_observation_ids(evidence_ids, reasoning_object_ids)
        return self._compute_chain_confidence(
            conclusion_id, reasoning_object_ids, evidence_ids, observation_ids
        )

    # ------------------------------------------------------------------
    # Internal: chain traversal
    # ------------------------------------------------------------------

    def _trace_chain(
        self,
        object_id: str,
        object_type: str,
        visited: Optional[set] = None,
        depth: int = 0,
    ) -> Tuple[List[str], List[str]]:
        """Recursively trace the reasoning chain upstream from an object.

        Args:
            object_id: Current object ID.
            object_type: Current object type.
            visited: Set of already-visited IDs (cycle prevention).
            depth: Current recursion depth.

        Returns:
            Tuple of (reasoning_path, reasoning_object_ids).
        """
        if visited is None:
            visited = set()

        path: List[str] = []
        ids: List[str] = []

        if object_id in visited or depth > 20:
            return path, ids

        visited.add(object_id)

        obj = self.repo.get(object_id)
        if obj is None:
            path.append(f"[MISSING] {object_type} {object_id[:8]}...")
            ids.append(object_id)
            return path, ids

        path.append(f"[{object_type}] {self._describe_object(obj)}")
        ids.append(object_id)

        # Get traversal rules for this type
        rules = TRAVERSAL_RULES.get(object_type, [])

        for field in rules:
            raw = getattr(obj, field, None)
            if raw is None:
                continue

            refs: List[str] = []
            if isinstance(raw, list):
                refs = raw
            elif isinstance(raw, str) and raw:
                refs = [raw]

            for ref_id in refs:
                if ref_id and ref_id not in visited:
                    ref_obj = self.repo.get(ref_id)
                    if ref_obj is not None:
                        ref_type = type(ref_obj).__name__
                        sub_path, sub_ids = self._trace_chain(ref_id, ref_type, visited, depth + 1)
                        path.extend(sub_path)
                        ids.extend(sub_ids)

        return path, ids

    def _describe_object(self, obj: BaseObject) -> str:
        """Generate a short description of an object for trace output."""
        type(obj).__name__

        if isinstance(obj, Observation):
            return f"{obj.source} = {obj.value} @ {obj.timestamp.isoformat() if hasattr(obj, 'timestamp') else ''}"
        elif isinstance(obj, Evidence):
            return f"{obj.direction}: {obj.interpretation[:60]}"
        elif isinstance(obj, Interpretation):
            return f"Rule={obj.rule_applied} → {obj.conclusion[:60]}"
        elif isinstance(obj, Narrative):
            return f"Thesis: {obj.thesis[:60]}"
        elif isinstance(obj, Hypothesis):
            return f"[{obj.type}] {obj.statement[:60]}"
        elif isinstance(obj, Scenario):
            return f"[{obj.type}] {obj.label}: {obj.thesis[:60]}"
        elif isinstance(obj, Confidence):
            return f"Target={obj.target_type}({obj.target_id[:8]}...) = {obj.value:.4f}"
        elif isinstance(obj, Contradiction):
            return f"[{obj.type}] {obj.description[:60]}"
        elif isinstance(obj, Research):
            return f"Q: {obj.question[:60]}"
        elif isinstance(obj, ResearchReport):
            return f"Report: {obj.title[:60] if obj.title else 'Untitled'}"
        elif isinstance(obj, Validation):
            return f"Status={obj.overall_status}, Quality={obj.quality_score}"
        elif isinstance(obj, Knowledge):
            return f"{obj.subject} {obj.predicate} {obj.object}"
        elif isinstance(obj, Pattern):
            return f"[{obj.type}] {obj.description[:60]}"
        elif isinstance(obj, Lesson):
            return f"[{obj.type}] {obj.description[:60]}"
        else:
            return f"{obj.id[:16]}..."

    def _collect_evidence_ids(self, object_ids: List[str]) -> List[str]:
        """Collect all unique evidence IDs from a list of object IDs."""
        evidence_set: set = set()
        for oid in object_ids:
            obj = self.repo.get(oid)
            if obj is None:
                continue
            if isinstance(obj, Evidence):
                evidence_set.add(obj.id)
            elif isinstance(obj, (Hypothesis, Interpretation, Narrative)):
                for field in ["evidence_ids", "supporting_evidence", "contradicting_evidence"]:
                    refs = getattr(obj, field, None) or []
                    if isinstance(refs, list):
                        evidence_set.update(refs)
        return sorted(evidence_set)

    def _collect_observation_ids(
        self,
        evidence_ids: List[str],
        object_ids: List[str],
    ) -> List[str]:
        """Collect all unique observation IDs from evidence and direct references."""
        obs_set: set = set()
        for eid in evidence_ids:
            ev = self.repo.get(eid)
            if isinstance(ev, Evidence) and ev.observation_id:
                obs_set.add(ev.observation_id)
        for oid in object_ids:
            obj = self.repo.get(oid)
            if isinstance(obj, Observation):
                obs_set.add(obj.id)
        return sorted(obs_set)

    def _compute_chain_confidence(
        self,
        conclusion_id: str,
        reasoning_object_ids: List[str],
        evidence_ids: List[str],
        observation_ids: List[str],
    ) -> float:
        """Compute confidence from chain completeness and evidence quality.

        Factors:
        1. Resolution rate: How many objects in the chain were found (0.5 weight)
        2. Evidence quality: Average confidence of linked evidence (0.3 weight)
        3. Observation coverage: Direct observations found (0.2 weight)
        """
        if not reasoning_object_ids:
            return 0.0

        # Resolve rate: check each ID exists
        resolved = 0
        for oid in reasoning_object_ids:
            if self.repo.get(oid) is not None:
                resolved += 1
        resolve_rate = resolved / len(reasoning_object_ids)

        # Evidence quality
        ev_confidence_sum = 0.0
        ev_count = 0
        for eid in evidence_ids:
            ev = self.repo.get(eid)
            if isinstance(ev, Evidence):
                ev_confidence_sum += ev.confidence
                ev_count += 1
        ev_quality = (ev_confidence_sum / max(ev_count, 1)) if ev_count > 0 else 0.0

        # Observation coverage
        obs_coverage = min(1.0, len(observation_ids) / max(len(reasoning_object_ids), 1))

        confidence = (
            resolve_rate * 0.5 +
            ev_quality * 0.3 +
            obs_coverage * 0.2
        )

        return round(min(1.0, max(0.0, confidence)), 4)

    def _determine_status(
        self,
        confidence: float,
        reasoning_object_ids: List[str],
    ) -> str:
        """Determine attribution status from confidence and chain completeness."""
        if not reasoning_object_ids:
            return "Broken"
        if confidence >= ATTRIBUTION_COMPLETE_THRESHOLD:
            return "Complete"
        elif confidence >= ATTRIBUTION_PARTIAL_THRESHOLD:
            return "Partial"
        else:
            return "Broken"

    def _build_trace(self, reasoning_path: List[str]) -> str:
        """Build a human-readable trace from the reasoning path."""
        return "\n".join(f"  {i}. {step}" for i, step in enumerate(reasoning_path, 1))

    def _get_child_ids(self, obj: BaseObject) -> List[str]:
        """Get child object IDs from a container object."""
        if isinstance(obj, HypothesisSet):
            return obj.hypothesis_ids
        elif isinstance(obj, ScenarioSet):
            return obj.scenario_ids
        elif isinstance(obj, EvidenceRegistry):
            return obj.evidence_ids
        elif hasattr(obj, "confidence_ids"):
            return obj.confidence_ids
        elif hasattr(obj, "contradiction_ids"):
            return obj.contradiction_ids
        return []

    def _get_outcomes_for_event(self, event_id: str) -> List[MarketOutcome]:
        """Get all MarketOutcome records for a given event ID."""
        results = []
        for obj in self.repo.get_all():
            if isinstance(obj, MarketOutcome) and obj.event_id == event_id:
                results.append(obj)
        return results

    def _audit(self, action: str, object_id: str, reason: str) -> None:
        """Record an audit entry for an attribution action."""
        entry = AuditEntry(
            actor="attribution_engine",
            action=action,
            object_id=object_id,
            object_type="Attribution",
        )
        self.repo.save(entry)
