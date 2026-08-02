"""
Evidence Aggregation Layer - Phase 7.2

Canonical EvidenceSource, EvidenceItem, EvidenceCollection, EvidenceAggregator,
and EvidenceValidator for the entire system.

Based on Article XVII: Object Model - Decision Engine Layer.

Purpose:
    The EvidenceAggregator gathers evidence from all ResearchOS modules.
    It does NOT make decisions. It does NOT score. It does NOT rank.
    It ONLY collects structured evidence items into a collection.

Pipeline:
    DecisionContext -> EvidenceAggregator -> EvidenceCollection -> EvidenceScore -> ...

Design Principles:
    - Deterministic: Same inputs -> same evidence items
    - Auditable: Full lifecycle tracking on every EvidenceItem
    - Versioned: Collection versioning for reproducibility
    - Stateless: EvidenceAggregator has no state; all state is in inputs
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.decision_engine.context import DecisionContext
from researchos.decision_engine.contracts import ProbabilityDirection


class EvidenceSource(str, Enum):
    MARKET_MEMORY = "MarketMemory"
    EXPERIMENT = "Experiment"
    VALIDATION = "Validation"
    MACRO = "Macro"
    QUANT_ENGINE = "QuantEngine"
    RESEARCH = "Research"
    MANUAL = "Manual"


class EvidenceItem(BaseObject):
    def __init__(
        self,
        source: EvidenceSource,
        reference_id: str,
        title: str,
        description: str = "",
        timestamp: Optional[datetime] = None,
        confidence: float = 0.5,
        weight: float = 1.0,
        direction: ProbabilityDirection = ProbabilityDirection.NEUTRAL,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "EVIDENCE_V1",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"EvidenceItem|{source.value}|{reference_id}|{title[:100]}"
            id = generate_id(seed)
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.source = source
        self.reference_id = reference_id
        self.title = title
        self.description = description
        self.timestamp = timestamp or utc_now()
        self.confidence = confidence
        self.weight = weight
        self.direction = direction
        self.metadata: Dict[str, Any] = metadata or {}
        self.version = version
        self._item_hash: str = ""
        self._update_hash()
        self.lifecycle.transition(LifecycleStage.CREATED, reason=f"EvidenceItem created: {source.value} | {title[:60]}")

    @property
    def item_hash(self) -> str:
        if not self._item_hash:
            self._update_hash()
        return self._item_hash

    def _update_hash(self) -> None:
        self._item_hash = deterministic_hash(self._to_hashable_dict())

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value, "reference_id": self.reference_id,
            "title": self.title, "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence, "weight": self.weight,
            "direction": self.direction.value,
            "metadata": dict(sorted(self.metadata.items())) if self.metadata else {},
            "version": self.version,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "source": self.source.value, "reference_id": self.reference_id,
            "title": self.title, "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence, "weight": self.weight,
            "direction": self.direction.value,
            "metadata": self.metadata, "version": self.version,
            "item_hash": self._item_hash,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceItem":
        obj = super().from_dict(data)
        obj.source = EvidenceSource(data["source"])
        obj.reference_id = data["reference_id"]
        obj.title = data["title"]
        obj.description = data.get("description", "")
        obj.timestamp = parse_timestamp(data["timestamp"]) if data.get("timestamp") else utc_now()
        obj.confidence = float(data.get("confidence", 0.5))
        obj.weight = float(data.get("weight", 1.0))
        obj.direction = ProbabilityDirection(data.get("direction", "Neutral"))
        obj.metadata = dict(data.get("metadata", {}))
        obj.version = data.get("version", "EVIDENCE_V1")
        obj._item_hash = data.get("item_hash", "")
        return obj


class EvidenceCollection(BaseObject):
    def __init__(
        self,
        decision_context_id: str,
        items: Optional[List[EvidenceItem]] = None,
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
        self.items: List[EvidenceItem] = items or []
        self.collection_timestamp = collection_timestamp or utc_now()
        self.collection_version = collection_version
        self._collection_hash: str = ""
        self._update_hash()
        self.lifecycle.transition(LifecycleStage.CREATED, reason=f"EvidenceCollection created: {len(self.items)} items")

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

    def add_item(self, item: EvidenceItem) -> None:
        self.items.append(item)
        self._update_hash()

    def add_items(self, items: List[EvidenceItem]) -> None:
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
        base.update({
            "decision_context_id": self.decision_context_id,
            "items": [e.to_dict() for e in self.items],
            "collection_timestamp": self.collection_timestamp.isoformat(),
            "collection_version": self.collection_version,
            "total_items": self.total_items,
            "collection_hash": self._collection_hash,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceCollection":
        obj = super().from_dict(data)
        obj.decision_context_id = data["decision_context_id"]
        obj.items = [EvidenceItem.from_dict(e) for e in data.get("items", [])]
        obj.collection_timestamp = parse_timestamp(data["collection_timestamp"]) if data.get("collection_timestamp") else utc_now()
        obj.collection_version = data.get("collection_version", "COLLECTION_V1")
        obj._collection_hash = data.get("collection_hash", "")
        return obj


class EvidenceAggregator:
    def __init__(self, aggregator_version: str = "AGGREGATOR_V1"):
        self.aggregator_version = aggregator_version

    def aggregate(self, context: DecisionContext) -> EvidenceCollection:
        items: List[EvidenceItem] = []
        items.extend(self._collect_market_memory(context))
        items.extend(self._collect_experiments(context))
        items.extend(self._collect_validation(context))
        items.extend(self._collect_macro(context))
        items.extend(self._collect_quant_engine(context))
        items.extend(self._collect_research(context))
        return EvidenceCollection(
            decision_context_id=context.id, items=items,
            collection_version=self.aggregator_version,
            ontology_tags=["decision_engine", "evidence_collection"],
        )

    def _collect_market_memory(self, context: DecisionContext) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for sid in context.historical_scenario_ids:
            items.append(EvidenceItem(source=EvidenceSource.MARKET_MEMORY, reference_id=sid, title=f"Historical scenario: {sid[:16]}", description="Historical market scenario match", timestamp=context.decision_timestamp, confidence=0.5, weight=0.25, metadata={"scenario_id": sid, "source_type": "historical_scenario"}, version=self.aggregator_version))
        for mid in context.market_memory_report_ids:
            items.append(EvidenceItem(source=EvidenceSource.MARKET_MEMORY, reference_id=mid, title=f"Market memory: {mid[:16]}", description="Market memory report", timestamp=context.decision_timestamp, confidence=0.5, weight=0.25, metadata={"report_id": mid, "source_type": "market_memory_report"}, version=self.aggregator_version))
        return items

    def _collect_experiments(self, context: DecisionContext) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for eid in context.experiment_result_ids:
            items.append(EvidenceItem(source=EvidenceSource.EXPERIMENT, reference_id=eid, title=f"Experiment: {eid[:16]}", description="Experiment result", timestamp=context.decision_timestamp, confidence=0.6, weight=0.20, metadata={"experiment_id": eid, "source_type": "experiment_result"}, version=self.aggregator_version))
        return items

    def _collect_validation(self, context: DecisionContext) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for vid in context.validation_ids:
            items.append(EvidenceItem(source=EvidenceSource.VALIDATION, reference_id=vid, title=f"Validation: {vid[:16]}", description="Validation result", timestamp=context.decision_timestamp, confidence=0.8, weight=0.15, metadata={"validation_id": vid, "source_type": "validation_result"}, version=self.aggregator_version))
        return items

    def _collect_macro(self, context: DecisionContext) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        if context.macro_state_id:
            items.append(EvidenceItem(source=EvidenceSource.MACRO, reference_id=context.macro_state_id, title=f"Macro state: {context.macro_state_id[:16]}", description="Macroeconomic state", timestamp=context.decision_timestamp, confidence=0.7, weight=0.25, metadata={"macro_state_id": context.macro_state_id, "source_type": "macro_state"}, version=self.aggregator_version))
        if context.market_regime_id:
            items.append(EvidenceItem(source=EvidenceSource.MACRO, reference_id=context.market_regime_id, title=f"Regime: {context.market_regime_id[:16]}", description="Market regime", timestamp=context.decision_timestamp, confidence=0.7, weight=0.25, metadata={"regime_id": context.market_regime_id, "source_type": "market_regime"}, version=self.aggregator_version))
        return items

    def _collect_quant_engine(self, context: DecisionContext) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for sid in context.simulation_result_ids:
            items.append(EvidenceItem(source=EvidenceSource.QUANT_ENGINE, reference_id=sid, title=f"Simulation: {sid[:16]}", description="Quant engine simulation", timestamp=context.decision_timestamp, confidence=0.6, weight=0.15, metadata={"simulation_id": sid, "source_type": "simulation_result"}, version=self.aggregator_version))
        return items

    def _collect_research(self, context: DecisionContext) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for rid in context.research_ids:
            items.append(EvidenceItem(source=EvidenceSource.RESEARCH, reference_id=rid, title=f"Research: {rid[:16]}", description="Research cycle evidence", timestamp=context.decision_timestamp, confidence=0.5, weight=0.15, metadata={"research_id": rid, "source_type": "research_cycle"}, version=self.aggregator_version))
        return items


class EvidenceValidator:
    def validate_item(self, item: EvidenceItem) -> List[str]:
        errors: List[str] = []
        if not item.source:
            errors.append("EvidenceItem source is empty")
        if not item.reference_id:
            errors.append("EvidenceItem reference_id is empty")
        if not item.title:
            errors.append("EvidenceItem title is empty")
        if not (0.0 <= item.confidence <= 1.0):
            errors.append(f"EvidenceItem confidence must be in [0.0, 1.0], got {item.confidence}")
        if not (0.0 <= item.weight <= 1.0):
            errors.append(f"EvidenceItem weight must be in [0.0, 1.0], got {item.weight}")
        if not isinstance(item.direction, ProbabilityDirection):
            errors.append(f"EvidenceItem direction must be a ProbabilityDirection, got {type(item.direction)}")
        return errors

    def validate_collection(self, collection: EvidenceCollection) -> List[str]:
        errors: List[str] = []
        if not collection.decision_context_id:
            errors.append("EvidenceCollection decision_context_id is empty")
        seen_ref_ids: Dict[str, int] = {}
        for i, item in enumerate(collection.items):
            item_errors = self.validate_item(item)
            errors.extend(f"Item[{i}]: {e}" for e in item_errors)
            if item.reference_id:
                if item.reference_id in seen_ref_ids:
                    errors.append(f"Duplicate reference_id at items {seen_ref_ids[item.reference_id]} and {i}")
                seen_ref_ids[item.reference_id] = i
        return errors

    def is_valid_item(self, item: EvidenceItem) -> bool:
        return len(self.validate_item(item)) == 0

    def is_valid_collection(self, collection: EvidenceCollection) -> bool:
        return len(self.validate_collection(collection)) == 0
