"""
Evidence Aggregation Layer - Phase 7.2

EvidenceCollection, EvidenceAggregator, and EvidenceValidator for the
decision engine, built on the canonical evidence contracts.

Based on Article XVII: Object Model - Decision Engine Layer.

Purpose:
    The EvidenceAggregator gathers evidence from all ResearchOS modules.
    It does NOT make decisions. It does NOT score. It does NOT rank.
    It ONLY collects structured evidence items into a collection.

Pipeline:
    DecisionContext -> EvidenceAggregator -> EvidenceCollection -> EvidenceScore -> ...

Canonical model:
    EvidenceSource and DecisionEvidenceItem are defined ONCE in
    researchos.decision_engine.contracts. This module must never redefine
    them. A canonical DecisionEvidenceItem carries:

        source          - EvidenceSource enum member
        source_id       - ID of the object that produced the evidence
        direction       - ProbabilityOutcome (Bullish | Bearish | Neutral)
        strength        - evidence strength (0.0-1.0)
        weight          - item-level weight factor (0.0-1.0)
        confidence      - confidence in this evidence item (0.0-1.0)
        description     - human-readable explanation
        supporting_ids  - IDs of supporting objects

    Collectors do not infer direction; every emitted item is NEUTRAL until
    a source module provides directional evidence.

Auditability:
    Item-level lifecycle/hashing belonged to the retired BaseObject-based
    DecisionEvidenceItem. Audit responsibility now lives on the EvidenceCollection,
    which is a BaseObject with deterministic identity, lifecycle tracking,
    and content hashing over all contained items.

Design Principles:
    - Deterministic: Same inputs -> same evidence items and collection hash
    - Auditable: Lifecycle, identity, and hash on every EvidenceCollection
    - Versioned: Collection versioning for reproducibility
    - Stateless: EvidenceAggregator has no state; all state is in inputs
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from researchos.core.base_object import BaseObject
from researchos.core.identity import deterministic_hash, generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.decision_engine.context import DecisionContext
from researchos.decision_engine.contracts import (
    DecisionEvidenceItem,
    EvidenceSource,
    ProbabilityOutcome,
)


class EvidenceCollection(BaseObject):
    def __init__(
        self,
        decision_context_id: str,
        items: Optional[List[DecisionEvidenceItem]] = None,
        collection_timestamp: Optional[datetime] = None,
        collection_version: str = "COLLECTION_V1",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"EvidenceCollection|{decision_context_id}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.decision_context_id = decision_context_id
        self.items: List[DecisionEvidenceItem] = items or []
        self.collection_timestamp = collection_timestamp or utc_now()
        self.collection_version = collection_version
        self._collection_hash: str = ""
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.CREATED, reason=f"EvidenceCollection created: {len(self.items)} items"
        )

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def collection_hash(self) -> str:
        if not self._collection_hash:
            self._update_hash()
        return self._collection_hash

    def _update_hash(self) -> None:
        self._collection_hash = deterministic_hash(self._to_hashable_dict())

    def add_item(self, item: DecisionEvidenceItem) -> None:
        self.items.append(item)
        self._update_hash()

    def add_items(self, items: List[DecisionEvidenceItem]) -> None:
        self.items.extend(items)
        self._update_hash()

    def get_source_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in self.items:
            src = item.source.value
            counts[src] = counts.get(src, 0) + 1
        return dict(sorted(counts.items()))

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "decision_context_id": self.decision_context_id,
            "items": [e.to_dict() for e in self.items],
            "collection_timestamp": self.collection_timestamp.isoformat(),
            "collection_version": self.collection_version,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "decision_context_id": self.decision_context_id,
                "items": [e.to_dict() for e in self.items],
                "collection_timestamp": self.collection_timestamp.isoformat(),
                "collection_version": self.collection_version,
                "total_items": self.total_items,
                "collection_hash": self._collection_hash,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceCollection":
        obj = super().from_dict(data)
        obj.decision_context_id = data["decision_context_id"]
        obj.items = [DecisionEvidenceItem.from_dict(e) for e in data.get("items", [])]
        obj.collection_timestamp = (
            parse_timestamp(data["collection_timestamp"])
            if data.get("collection_timestamp")
            else utc_now()
        )
        obj.collection_version = data.get("collection_version", "COLLECTION_V1")
        obj._collection_hash = data.get("collection_hash", "")
        return obj


class EvidenceAggregator:
    """Collects canonical DecisionEvidenceItem objects from a DecisionContext.

    Deterministic: the same context always yields the same items in the
    same order, and the same collection hash.
    """

    #: Per-reference evidence parameters:
    #: (strength, confidence, item_weight, description, source_type).
    _SCENARIO: Tuple[float, float, float, str, str] = (
        0.5,
        0.5,
        0.25,
        "Historical market scenario match",
        "historical_scenario",
    )
    _MEMORY_REPORT: Tuple[float, float, float, str, str] = (
        0.5,
        0.5,
        0.25,
        "Market memory report",
        "market_memory_report",
    )
    _EXPERIMENT: Tuple[float, float, float, str, str] = (
        0.6,
        0.6,
        0.20,
        "Experiment result",
        "experiment_result",
    )
    _VALIDATION: Tuple[float, float, float, str, str] = (
        0.8,
        0.8,
        0.15,
        "Validation result",
        "validation_result",
    )
    _MACRO_STATE: Tuple[float, float, float, str, str] = (
        0.7,
        0.7,
        0.25,
        "Macroeconomic state",
        "macro_state",
    )
    _MARKET_REGIME: Tuple[float, float, float, str, str] = (
        0.7,
        0.7,
        0.25,
        "Market regime",
        "market_regime",
    )
    _SIMULATION: Tuple[float, float, float, str, str] = (
        0.6,
        0.6,
        0.15,
        "Quant engine simulation",
        "simulation_result",
    )
    _RESEARCH: Tuple[float, float, float, str, str] = (
        0.5,
        0.5,
        0.15,
        "Research cycle evidence",
        "research_cycle",
    )

    def __init__(self, aggregator_version: str = "AGGREGATOR_V1"):
        self.aggregator_version = aggregator_version

    @staticmethod
    def _make_item(
        source: EvidenceSource,
        reference_id: str,
        params: Tuple[float, float, float, str, str],
    ) -> DecisionEvidenceItem:
        """Build a canonical DecisionEvidenceItem from per-reference parameters."""
        strength, confidence, weight, description, source_type = params
        return DecisionEvidenceItem(
            source=source,
            source_id=reference_id,
            direction=ProbabilityOutcome.NEUTRAL,
            strength=strength,
            weight=weight,
            confidence=confidence,
            description=f"{description} ({source_type})",
            supporting_ids=[reference_id],
        )

    def aggregate(self, context: DecisionContext) -> EvidenceCollection:
        items: List[DecisionEvidenceItem] = []
        items.extend(self._collect_market_memory(context))
        items.extend(self._collect_experiments(context))
        items.extend(self._collect_validation(context))
        items.extend(self._collect_macro(context))
        items.extend(self._collect_quant_engine(context))
        items.extend(self._collect_research(context))
        return EvidenceCollection(
            decision_context_id=context.id,
            items=items,
            collection_timestamp=context.decision_timestamp,
            collection_version=self.aggregator_version,
            ontology_tags=["decision_engine", "evidence_collection"],
        )

    def _collect_market_memory(self, context: DecisionContext) -> List[DecisionEvidenceItem]:
        items: List[DecisionEvidenceItem] = []
        for sid in context.historical_scenario_ids:
            items.append(self._make_item(EvidenceSource.MARKET_MEMORY, sid, self._SCENARIO))
        for mid in context.market_memory_report_ids:
            items.append(self._make_item(EvidenceSource.MARKET_MEMORY, mid, self._MEMORY_REPORT))
        return items

    def _collect_experiments(self, context: DecisionContext) -> List[DecisionEvidenceItem]:
        items: List[DecisionEvidenceItem] = []
        for eid in context.experiment_result_ids:
            items.append(self._make_item(EvidenceSource.EXPERIMENT, eid, self._EXPERIMENT))
        return items

    def _collect_validation(self, context: DecisionContext) -> List[DecisionEvidenceItem]:
        items: List[DecisionEvidenceItem] = []
        for vid in context.validation_ids:
            items.append(self._make_item(EvidenceSource.VALIDATION, vid, self._VALIDATION))
        return items

    def _collect_macro(self, context: DecisionContext) -> List[DecisionEvidenceItem]:
        items: List[DecisionEvidenceItem] = []
        if context.macro_state_id:
            items.append(
                self._make_item(
                    EvidenceSource.MACRO_INTELLIGENCE, context.macro_state_id, self._MACRO_STATE
                )
            )
        if context.market_regime_id:
            items.append(
                self._make_item(
                    EvidenceSource.MACRO_INTELLIGENCE, context.market_regime_id, self._MARKET_REGIME
                )
            )
        return items

    def _collect_quant_engine(self, context: DecisionContext) -> List[DecisionEvidenceItem]:
        items: List[DecisionEvidenceItem] = []
        for sid in context.simulation_result_ids:
            items.append(self._make_item(EvidenceSource.QUANT_ENGINE, sid, self._SIMULATION))
        return items

    def _collect_research(self, context: DecisionContext) -> List[DecisionEvidenceItem]:
        items: List[DecisionEvidenceItem] = []
        for rid in context.research_ids:
            items.append(self._make_item(EvidenceSource.RESEARCH_OBJECTS, rid, self._RESEARCH))
        return items


class EvidenceValidator:
    """Validates canonical DecisionEvidenceItem objects and collection integrity.

    Only fields defined on researchos.decision_engine.contracts.DecisionEvidenceItem
    are validated; legacy fields (reference_id, title, metadata, timestamp,
    version) are not part of the canonical contract.
    """

    def validate_item(self, item: DecisionEvidenceItem) -> List[str]:
        errors: List[str] = []
        if not isinstance(item.source, EvidenceSource):
            errors.append(
                f"DecisionEvidenceItem source must be an EvidenceSource, got {type(item.source)}"
            )
        if not item.source_id:
            errors.append("DecisionEvidenceItem source_id is empty")
        if not isinstance(item.direction, ProbabilityOutcome):
            errors.append(
                f"DecisionEvidenceItem direction must be a ProbabilityOutcome, got {type(item.direction)}"
            )
        for name, value in (
            ("strength", item.strength),
            ("confidence", item.confidence),
            ("weight", item.weight),
        ):
            if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                errors.append(f"DecisionEvidenceItem {name} must be in [0.0, 1.0], got {value}")
        return errors

    def validate_collection(self, collection: EvidenceCollection) -> List[str]:
        errors: List[str] = []
        if not collection.decision_context_id:
            errors.append("EvidenceCollection decision_context_id is empty")
        seen_source_ids: Dict[str, int] = {}
        for i, item in enumerate(collection.items):
            item_errors = self.validate_item(item)
            errors.extend(f"Item[{i}]: {e}" for e in item_errors)
            if item.source_id:
                if item.source_id in seen_source_ids:
                    errors.append(
                        f"Duplicate source_id at items {seen_source_ids[item.source_id]} and {i}"
                    )
                seen_source_ids[item.source_id] = i
        return errors

    def is_valid_item(self, item: DecisionEvidenceItem) -> bool:
        return len(self.validate_item(item)) == 0

    def is_valid_collection(self, collection: EvidenceCollection) -> bool:
        return len(self.validate_collection(collection)) == 0
