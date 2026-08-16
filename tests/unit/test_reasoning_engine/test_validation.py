"""
Tests for the Reasoning Engine EvidenceValidator (Phase 4.5.2).

Verifies:
    - valid evidence accepted
    - low reliability rejected
    - short hash rejected
    - empty source rejected
    - multiple errors collected
    - deterministic output

Based on Article X: Reasoning Engine -- validation guarantees.
"""

from __future__ import annotations

import pytest

from researchos.reasoning_engine.contracts import (
    EvidenceItem,
    EvidenceType,
    InvalidIdentifierError,
)
from researchos.reasoning_engine.evidence import EvidenceRecord
from researchos.reasoning_engine.validation import EvidenceValidator


def _make_evidence(
    reliability_score: float = 0.9,
    content_hash: str = "abc123456",
    source: str = "historical_dataset",
    id: str = "dataset_xauusd_001",
    evidence_type: EvidenceType = EvidenceType.DATASET,
) -> EvidenceItem:
    return EvidenceItem(
        id=id,
        source=source,
        evidence_type=evidence_type,
        content_hash=content_hash,
        reliability_score=reliability_score,
    )


@pytest.fixture
def validator() -> EvidenceValidator:
    return EvidenceValidator()


class TestValidEvidence:
    """A well-formed EvidenceItem is accepted."""

    def test_valid_evidence_accepted(self, validator: EvidenceValidator):
        """Valid evidence accepted."""
        record = validator.validate(_make_evidence())
        assert isinstance(record, EvidenceRecord)
        assert record.validated is True
        assert record.validation_errors == ()


class TestLowReliability:
    """Rule 1: reliability_score must be >= 0.5."""

    def test_low_reliability_rejected(self, validator: EvidenceValidator):
        """Low reliability rejected."""
        record = validator.validate(_make_evidence(reliability_score=0.2))
        assert record.validated is False
        assert "reliability_score below threshold" in record.validation_errors

    def test_boundary_reliability_accepted(self, validator: EvidenceValidator):
        """A reliability of exactly 0.5 is the threshold and is accepted."""
        record = validator.validate(_make_evidence(reliability_score=0.5))
        assert record.validated is True
        assert record.validation_errors == ()


class TestShortHash:
    """Rule 2: content_hash length must be >= 8 characters."""

    def test_short_hash_rejected(self, validator: EvidenceValidator):
        """Short hash rejected."""
        record = validator.validate(_make_evidence(content_hash="abc1234"))
        assert record.validated is False
        assert "content_hash too short" in record.validation_errors

    def test_boundary_hash_accepted(self, validator: EvidenceValidator):
        record = validator.validate(_make_evidence(content_hash="12345678"))
        assert record.validated is True


class TestEmptySource:
    """Rule 3: source must contain meaningful text.

    The EvidenceItem contract already rejects empty sources at construction,
    so an empty source can never reach the validator.  We assert that boundary
    here and confirm the validator never reports a source error for valid input.
    """

    def test_empty_source_rejected(self):
        """Empty source rejected (enforced by the EvidenceItem contract)."""
        with pytest.raises(InvalidIdentifierError):
            EvidenceItem(
                id="ev_001",
                source="",
                evidence_type=EvidenceType.OBSERVATION,
                content_hash="abc123456",
                reliability_score=0.9,
            )

    def test_whitespace_source_rejected(self):
        with pytest.raises(InvalidIdentifierError):
            EvidenceItem(
                id="ev_001",
                source="   ",
                evidence_type=EvidenceType.OBSERVATION,
                content_hash="abc123456",
                reliability_score=0.9,
            )

    def test_validator_reports_no_source_error_for_valid_input(
        self, validator: EvidenceValidator
    ):
        record = validator.validate(_make_evidence(source="historical_dataset"))
        assert "source must contain meaningful text" not in record.validation_errors


class TestMultipleErrors:
    """All failing rules are collected, never short-circuited."""

    def test_multiple_errors_collected(self, validator: EvidenceValidator):
        """Multiple errors collected."""
        record = validator.validate(
            _make_evidence(reliability_score=0.2, content_hash="abc1234")
        )
        assert record.validated is False
        # Both achievable rules fire.
        assert "reliability_score below threshold" in record.validation_errors
        assert "content_hash too short" in record.validation_errors
        assert len(record.validation_errors) == 2


class TestDeterministicOutput:
    """The same EvidenceItem always yields an identical EvidenceRecord."""

    def test_deterministic_output(self, validator: EvidenceValidator):
        """Deterministic output."""
        evidence = _make_evidence()
        record_a = validator.validate(evidence)
        record_b = validator.validate(evidence)
        assert record_a == record_b
        assert hash(record_a) == hash(record_b)
        assert record_a.validation_errors == record_b.validation_errors

    def test_deterministic_output_invalid(self, validator: EvidenceValidator):
        evidence = _make_evidence(reliability_score=0.2, content_hash="abc1234")
        record_a = validator.validate(evidence)
        record_b = validator.validate(evidence)
        assert record_a == record_b
        assert record_a.validation_errors == record_b.validation_errors

    def test_different_inputs_different_records(self, validator: EvidenceValidator):
        record_good = validator.validate(_make_evidence())
        record_bad = validator.validate(_make_evidence(reliability_score=0.2))
        assert record_good != record_bad
        assert record_good.validated is True
        assert record_bad.validated is False
