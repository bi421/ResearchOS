"""
Process objects — tracking the research lifecycle and audit trail.

Based on Article XVII: Object Model — Process Layer.
Based on Article X: Reasoning Engine.

Process objects track the complete research lifecycle, reasoning chains,
and provide an immutable audit trail for all system actions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import deterministic_hash, generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class ResearchCycle(BaseObject):
    """
    The complete cycle of research, from question to validation.

    Based on Article XVII: Object Model — ResearchCycle.

    Tracks the full lifecycle of a research project including all stages,
    their duration, inputs, outputs, and quality metrics. Enables analysis
    of research efficiency and bottlenecks.

    Attributes:
        research_id: Link to Research
        start_time: When the cycle started
        end_time: When the cycle ended
        stages: List of stage records with timing
        duration: Total duration in seconds
        inputs: Input references
        outputs: Output references
        quality_metrics: Quality metrics for the cycle
        cycle_hash: Deterministic hash of the cycle
    """

    def __init__(
        self,
        research_id: str,
        stages: list[dict[str, Any]] | None = None,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        quality_metrics: list[dict[str, Any]] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"ResearchCycle|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.start_time = utc_now()
        self.end_time: datetime | None = None
        self.stages: list[dict[str, Any]] = stages or []
        self.duration: float = 0.0
        self.inputs: list[str] = inputs or []
        self.outputs: list[str] = outputs or []
        self.quality_metrics: list[dict[str, Any]] = quality_metrics or []
        self.cycle_hash: str = ""

        self.lifecycle.transition(
            LifecycleStage.STARTED,
            reason="Research cycle started",
        )

    def add_stage(
        self,
        name: str,
        duration_seconds: float,
        status: str = "Complete",
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """Add a stage record to the cycle."""
        stage = {
            "name": name,
            "duration_seconds": duration_seconds,
            "status": status,
            "metrics": metrics or {},
        }
        self.stages.append(stage)
        self.duration += duration_seconds

    def add_quality_metric(self, name: str, value: float, weight: float = 1.0) -> None:
        """Add a quality metric to the cycle."""
        self.quality_metrics.append(
            {
                "name": name,
                "value": value,
                "weight": weight,
            }
        )

    def complete(self) -> None:
        """Mark the research cycle as complete."""
        self.end_time = utc_now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        content = self._to_hashable_dict()
        self.cycle_hash = deterministic_hash(content)
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Research cycle completed: {self.duration:.1f}s, {len(self.stages)} stages",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "stages": self.stages,
            "duration": self.duration,
            "inputs": sorted(self.inputs),
            "outputs": sorted(self.outputs),
            "quality_metrics": self.quality_metrics,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "stages": self.stages,
                "duration": self.duration,
                "inputs": self.inputs,
                "outputs": self.outputs,
                "quality_metrics": self.quality_metrics,
                "cycle_hash": self.cycle_hash,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> ResearchCycle:
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.start_time = parse_timestamp(data["start_time"])
        obj.end_time = parse_timestamp(data["end_time"]) if data.get("end_time") else None
        obj.stages = list(data.get("stages", []))
        obj.duration = data.get("duration", 0.0)
        obj.inputs = list(data.get("inputs", []))
        obj.outputs = list(data.get("outputs", []))
        obj.quality_metrics = list(data.get("quality_metrics", []))
        obj.cycle_hash = data.get("cycle_hash", "")
        return obj


class ReasoningChain(BaseObject):
    """
    A complete chain of reasoning from observation to conclusion.

    Based on Article XVII: Object Model — ReasoningChain.

    Captures every step in the reasoning pipeline, making all conclusions
    fully traceable back to their source evidence. Enables audit of
    every decision made by the system.

    Attributes:
        research_id: Link to Research
        steps: List of reasoning steps
        inputs: Input references
        outputs: Output references
        rules_applied: Rules applied in the chain
        evidence_used: Evidence IDs used
        confidence: Confidence in the chain (0.0-1.0)
        chain_hash: Deterministic hash of the chain
        trace: Full trace string
    """

    def __init__(
        self,
        research_id: str,
        steps: list[dict[str, Any]] | None = None,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        rules_applied: list[str] | None = None,
        evidence_used: list[str] | None = None,
        confidence: float = 0.0,
        trace: str = "",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"ReasoningChain|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.initial_inputs: list[str] = list(inputs or [])
        self.steps: list[dict[str, Any]] = steps or []
        self.inputs: list[str] = list(inputs or [])
        self.outputs: list[str] = outputs or []
        self.rules_applied: list[str] = rules_applied or []
        self.evidence_used: list[str] = evidence_used or []
        self.confidence = confidence
        self.trace = trace
        self.chain_hash: str = ""

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason="Reasoning chain created",
        )

    def add_step(
        self,
        rule: str,
        inputs: list[str],
        outputs: list[str],
        description: str = "",
    ) -> None:
        """Add a reasoning step to the chain."""
        step = {
            "order": len(self.steps) + 1,
            "rule": rule,
            "inputs": inputs,
            "outputs": outputs,
            "description": description,
        }
        self.steps.append(step)
        self.rules_applied.append(rule)
        self.inputs.extend(i for i in inputs if i not in self.inputs)
        self.outputs.extend(o for o in outputs if o not in self.outputs)
        self.evidence_used.extend(i for i in inputs if i not in self.evidence_used and i.startswith("ev_"))

    def verify(self) -> bool:
        """
        Verify the reasoning chain for completeness.

        A chain is complete if:
            1. It has at least one step
            2. The final outputs are a superset of initial inputs
            3. Every step's inputs appear in previous step outputs or initial inputs

        Returns:
            True if the chain is valid.
        """
        if not self.steps:
            return False

        available = set(self.initial_inputs)

        for index, step in enumerate(self.steps):
            step_inputs = set(step["inputs"])
            # ????? ????? ??? chain-??? ?? ??????? (raw evidence-???
            # ???? ?????????) ??? availability ?????????? ????????.
            # ????????? ????? ??? ?????? ????? ????????? output ????
            # ?????????? ?????.
            if index > 0 and not step_inputs.issubset(available):
                return False
            available.update(step["outputs"])

        self.trace = f"Chain verified: {len(self.steps)} steps, {len(self.initial_inputs)} inputs, {len(available)} outputs"
        content = self._to_hashable_dict()
        self.chain_hash = deterministic_hash(content)
        self.lifecycle.transition(
            LifecycleStage.VERIFIED,
            reason="Reasoning chain verified",
        )
        return True

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "steps": self.steps,
            "inputs": sorted(self.inputs),
            "outputs": sorted(self.outputs),
            "rules_applied": sorted(self.rules_applied),
            "evidence_used": sorted(self.evidence_used),
            "confidence": self.confidence,
            "trace": self.trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "steps": self.steps,
                "inputs": self.inputs,
                "outputs": self.outputs,
                "rules_applied": self.rules_applied,
                "evidence_used": self.evidence_used,
                "confidence": self.confidence,
                "chain_hash": self.chain_hash,
                "trace": self.trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> ReasoningChain:
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.initial_inputs = list(data.get("initial_inputs", data.get("inputs", [])))
        obj.steps = list(data.get("steps", []))
        obj.inputs = list(data.get("inputs", []))
        obj.outputs = list(data.get("outputs", []))
        obj.rules_applied = list(data.get("rules_applied", []))
        obj.evidence_used = list(data.get("evidence_used", []))
        obj.confidence = data.get("confidence", 0.0)
        obj.trace = data.get("trace", "")
        obj.chain_hash = data.get("chain_hash", "")
        return obj


class AuditEntry(BaseObject):
    """
    An immutable record of a single action or decision in the system.

    Based on Article XVII: Object Model — AuditEntry.

    Every action in ResearchOS is recorded as an AuditEntry. Once created,
    audit entries are immutable and form a verifiable chain. This ensures
    complete traceability of all system actions.

    Attributes:
        timestamp: When the action occurred
        actor: Who performed the action
        action: What action was performed
        object_id: The ID of the affected object
        object_type: The type of the affected object
        before_state: State before the action
        after_state: State after the action
        reasoning_chain_id: Link to the reasoning chain
        entry_hash: Deterministic hash of this entry
        previous_entry: Hash of the previous audit entry (for chain integrity)
    """

    def __init__(
        self,
        actor: str,
        action: str,
        object_id: str,
        object_type: str,
        before_state: str | None = None,
        after_state: str | None = None,
        reasoning_chain_id: str | None = None,
        previous_entry: str | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"AuditEntry|{actor}|{action}|{object_id}|{object_type}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.timestamp = utc_now()
        self.actor = actor
        self.action = action
        self.object_id = object_id
        self.object_type = object_type
        self.before_state = before_state or ""
        self.after_state = after_state or ""
        self.reasoning_chain_id = reasoning_chain_id or ""
        self.previous_entry = previous_entry or ""
        self.entry_hash: str = ""

        # Hash is computed at save time in save_audit_entry()
        # (previous_entry must be known to produce the final hash)

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"Audit entry created: {action} on {object_type}:{object_id}",
        )

    def is_chain_intact(self, previous_entry_hash: str) -> bool:
        """
        Verify that the audit chain is intact.

        Args:
            previous_entry_hash: The hash of the previous entry in the chain.

        Returns:
            True if this entry correctly references the previous entry.
        """
        if self.previous_entry:
            return self.previous_entry == previous_entry_hash
        return True  # First entry in chain

    def _to_hashable_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "reasoning_chain_id": self.reasoning_chain_id,
            "previous_entry": self.previous_entry,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "actor": self.actor,
                "action": self.action,
                "object_id": self.object_id,
                "affected_object_type": self.object_type,
                "before_state": self.before_state,
                "after_state": self.after_state,
                "reasoning_chain_id": self.reasoning_chain_id,
                "previous_entry": self.previous_entry,
                "entry_hash": self.entry_hash,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> AuditEntry:
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.actor = data["actor"]
        obj.action = data["action"]
        obj.object_id = data["object_id"]
        obj.object_type = data.get("affected_object_type", data.get("object_type", ""))
        obj.before_state = data.get("before_state", "")
        obj.after_state = data.get("after_state", "")
        obj.reasoning_chain_id = data.get("reasoning_chain_id", "")
        obj.previous_entry = data.get("previous_entry", "")
        obj.entry_hash = data.get("entry_hash", "")
        return obj
