"""Deterministic self-healing engineering primitives.

This package is temporary development infrastructure for ResearchOS. It detects
failures, records diagnosis/repair attempts, and requires validation before a
repair can be promoted.
"""

from .core import FailureRecord, FailureStatus, RepairAttempt, RepairOutcome, SelfHealingController

__all__ = [
    "FailureRecord",
    "FailureStatus",
    "RepairAttempt",
    "RepairOutcome",
    "SelfHealingController",
]
