"""
Lifecycle management for ResearchOS objects.

Implements the lifecycle tracking for all objects.
Based on Article XVII: Object Model — every object has a lifecycle.

Each object progresses through well-defined stages, and all transitions
are recorded for auditability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from researchos.core.timestamp import parse_timestamp, utc_now


class LifecycleStage(str, Enum):
    """Standard lifecycle stages for ResearchOS objects."""

    CREATED = "Created"
    VALIDATED = "Validated"
    ACTIVE = "Active"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    FINALIZED = "Finalized"
    SUPerseded = "Superseded"
    INVALIDATED = "Invalidated"
    RESOLVED = "Resolved"
    RETIRED = "Retired"
    ARCHIVED = "Archived"
    DRAFT = "Draft"
    FINAL = "Final"
    INITIATED = "Initiated"
    VERIFIED = "Verified"
    DETECTED = "Detected"
    TRACKED = "Tracked"
    MITIGATED = "Mitigated"
    ASSESSED = "Assessed"
    COMPLETED = "Completed"
    ANALYZED = "Analyzed"
    STARTED = "Started"
    UPDATED = "Updated"
    CALIBRATED = "Calibrated"
    RESOLVED_ESCALATED = "Resolved/Escalated"


@dataclass
class LifecycleTransition:
    """A single lifecycle transition event."""

    stage: LifecycleStage
    timestamp: datetime
    reason: str | None = None

    def to_dict(self) -> dict[str, any]:
        return {
            "stage": self.stage.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
        }


class Lifecycle:
    """
    Tracks the lifecycle of a ResearchOS object.

    Every object starts in the CREATED stage and progresses through
    a series of well-defined stages. All transitions are recorded
    for auditability and traceability.
    """

    def __init__(self, initial_stage: LifecycleStage = LifecycleStage.CREATED):
        self.transitions: list[LifecycleTransition] = [
            LifecycleTransition(
                stage=initial_stage,
                timestamp=utc_now(),
                reason="Object created",
            )
        ]

    @property
    def current_stage(self) -> LifecycleStage:
        """Get the current lifecycle stage."""
        return self.transitions[-1].stage

    def transition(
        self,
        stage: LifecycleStage,
        reason: str | None = None,
    ) -> None:
        """
        Transition to a new lifecycle stage.

        Args:
            stage: The new stage to transition to.
            reason: Optional reason for the transition.

        Raises:
            RuntimeError: If the object is in a FINALIZED or ARCHIVED
                terminal state and cannot be mutated.
        """
        if self.current_stage in (LifecycleStage.FINALIZED, LifecycleStage.ARCHIVED):
            raise RuntimeError(f"Cannot transition from terminal stage {self.current_stage.value}")
        self.transitions.append(
            LifecycleTransition(
                stage=stage,
                timestamp=utc_now(),
                reason=reason,
            )
        )

    def is_terminal(self) -> bool:
        """Check if the object is in a terminal state."""
        return self.current_stage in {
            LifecycleStage.ARCHIVED,
            LifecycleStage.RETIRED,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Lifecycle:
        obj = cls.__new__(cls)
        obj.transitions = []
        for t in data.get("transitions", []):
            obj.transitions.append(
                LifecycleTransition(
                    stage=LifecycleStage(t["stage"]),
                    timestamp=parse_timestamp(t["timestamp"]),
                    reason=t.get("reason"),
                )
            )
        return obj

    def to_dict(self) -> dict[str, any]:
        return {
            "current_stage": self.current_stage.value,
            "transitions": [t.to_dict() for t in self.transitions],
        }
