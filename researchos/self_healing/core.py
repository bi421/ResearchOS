"""Core state machine for safe, deterministic self-healing workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Callable


class FailureStatus(str, Enum):
    DETECTED = "detected"
    DIAGNOSED = "diagnosed"
    REPAIR_PROPOSED = "repair_proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class RepairOutcome(str, Enum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class FailureRecord:
    failure_id: str
    source: str
    signature: str
    message: str
    status: FailureStatus = FailureStatus.DETECTED

    def __post_init__(self) -> None:
        for name in ("failure_id", "source", "signature", "message"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True)
class RepairAttempt:
    failure_id: str
    diagnosis: str
    repair_id: str
    outcome: RepairOutcome = RepairOutcome.NOT_RUN
    validation_evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("failure_id", "diagnosis", "repair_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")


class SelfHealingController:
    """Enforces detect -> diagnose -> repair -> validate -> promote ordering."""

    def __init__(self) -> None:
        self._failures: dict[str, FailureRecord] = {}
        self._repairs: dict[str, RepairAttempt] = {}

    @staticmethod
    def fingerprint(source: str, signature: str, message: str) -> str:
        payload = "\x1f".join((source, signature, message)).encode("utf-8")
        return sha256(payload).hexdigest()

    def detect(self, source: str, signature: str, message: str) -> FailureRecord:
        failure_id = self.fingerprint(source, signature, message)
        record = FailureRecord(failure_id, source, signature, message)
        self._failures[failure_id] = record
        return record

    def diagnose(self, failure_id: str, diagnosis: str, repair_id: str) -> RepairAttempt:
        failure = self._require_failure(failure_id)
        if failure.status is not FailureStatus.DETECTED:
            raise ValueError("failure must be in detected state before diagnosis")
        if not diagnosis.strip() or not repair_id.strip():
            raise ValueError("diagnosis and repair_id must not be empty")
        self._failures[failure_id] = FailureRecord(
            **{**failure.__dict__, "status": FailureStatus.REPAIR_PROPOSED}
        )
        attempt = RepairAttempt(failure_id, diagnosis, repair_id)
        self._repairs[repair_id] = attempt
        return attempt

    def validate(
        self,
        repair_id: str,
        checks: tuple[Callable[[], bool], ...],
        evidence: tuple[str, ...] = (),
    ) -> RepairAttempt:
        repair = self._require_repair(repair_id)
        if repair.outcome is not RepairOutcome.NOT_RUN:
            raise ValueError("repair validation can only run once")
        passed = all(check() for check in checks)
        outcome = RepairOutcome.PASSED if passed else RepairOutcome.FAILED
        attempt = RepairAttempt(repair.failure_id, repair.diagnosis, repair.repair_id, outcome, evidence)
        self._repairs[repair_id] = attempt
        status = FailureStatus.VALIDATED if passed else FailureStatus.REJECTED
        failure = self._require_failure(repair.failure_id)
        self._failures[repair.failure_id] = FailureRecord(
            **{**failure.__dict__, "status": status}
        )
        return attempt

    def promote(self, repair_id: str) -> RepairAttempt:
        repair = self._require_repair(repair_id)
        if repair.outcome is not RepairOutcome.PASSED:
            raise ValueError("only a validated repair may be promoted")
        failure = self._require_failure(repair.failure_id)
        if failure.status is not FailureStatus.VALIDATED:
            raise ValueError("failure is not validated")
        self._failures[repair.failure_id] = FailureRecord(
            **{**failure.__dict__, "status": FailureStatus.PROMOTED}
        )
        promoted = RepairAttempt(
            repair.failure_id, repair.diagnosis, repair.repair_id,
            RepairOutcome.PASSED, repair.validation_evidence
        )
        self._repairs[repair_id] = promoted
        return promoted

    def failure(self, failure_id: str) -> FailureRecord:
        return self._require_failure(failure_id)

    def repair(self, repair_id: str) -> RepairAttempt:
        return self._require_repair(repair_id)

    def _require_failure(self, failure_id: str) -> FailureRecord:
        try:
            return self._failures[failure_id]
        except KeyError as exc:
            raise KeyError(f"unknown failure: {failure_id}") from exc

    def _require_repair(self, repair_id: str) -> RepairAttempt:
        try:
            return self._repairs[repair_id]
        except KeyError as exc:
            raise KeyError(f"unknown repair: {repair_id}") from exc
