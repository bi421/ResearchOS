from __future__ import annotations

import pytest

from researchos.self_healing import FailureStatus, RepairOutcome, SelfHealingController


def test_self_healing_happy_path() -> None:
    controller = SelfHealingController()
    failure = controller.detect("ci", "pytest-failure", "assertion failed")
    repair = controller.diagnose(failure.failure_id, "incorrect invariant", "repair-001")

    validated = controller.validate(
        repair.repair_id,
        (lambda: True, lambda: 2 + 2 == 4),
        evidence=("unit-tests", "ci-green"),
    )
    promoted = controller.promote(repair.repair_id)

    assert validated.outcome is RepairOutcome.PASSED
    assert promoted.outcome is RepairOutcome.PASSED
    assert controller.failure(failure.failure_id).status is FailureStatus.PROMOTED


def test_failed_validation_cannot_be_promoted() -> None:
    controller = SelfHealingController()
    failure = controller.detect("ci", "test-failure", "boom")
    repair = controller.diagnose(failure.failure_id, "bad assumption", "repair-002")
    validated = controller.validate(repair.repair_id, (lambda: False,))

    assert validated.outcome is RepairOutcome.FAILED
    assert controller.failure(failure.failure_id).status is FailureStatus.REJECTED
    with pytest.raises(ValueError, match="only a validated repair may be promoted"):
        controller.promote(repair.repair_id)


def test_deterministic_failure_fingerprint() -> None:
    first = SelfHealingController.fingerprint("ci", "pytest", "failure")
    second = SelfHealingController.fingerprint("ci", "pytest", "failure")
    different = SelfHealingController.fingerprint("ci", "pytest", "other")

    assert first == second
    assert first != different


def test_invalid_state_transitions_are_rejected() -> None:
    controller = SelfHealingController()
    failure = controller.detect("ci", "x", "y")
    repair = controller.diagnose(failure.failure_id, "cause", "repair-003")

    with pytest.raises(ValueError, match="repair validation can only run once"):
        controller.validate(repair.repair_id, (lambda: True,))
        controller.validate(repair.repair_id, (lambda: True,))


def test_empty_failure_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="source must not be empty"):
        SelfHealingController().detect("", "sig", "msg")
