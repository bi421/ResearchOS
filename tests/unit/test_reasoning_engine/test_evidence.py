"""
Tests for the Reasoning Engine evidence-validation wrapper (Phase 4.5.2).

Verifies:
    - EvidenceRecord carries evidence, validated flag, and error tuple.
    - ``validated`` is True only when no errors exist.
    - validation_errors is an immutable tuple.
    - EvidenceRecord is a frozen, hashable dataclass.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from researchos.reasoning_engine.contracts import EvidenceType, ReasoningEvidence
from researchos.reasoning_engine.evidence import EvidenceRecord


def _make_evidence(
    reliability_score: float = 0.9,
    content_hash: str = "abc123456",
    source: str = "historical_dataset",
    id: str = "dataset_xauusd_001",
    evidence_type: EvidenceType = EvidenceType.DATASET,
) -> ReasoningEvidence:
    return ReasoningEvidence(
        id=id,
        source=source,
        evidence_type=evidence_type,
        content_hash=content_hash,
        reliability_score=reliability_score,
    )


class TestEvidenceRecordConstruction:
    """Tests for EvidenceRecord basic construction and invariant."""

    def test_is_frozen_dataclass(self):
        assert is_dataclass(EvidenceRecord)

    def test_validated_true_when_no_errors(self):
        """validated=True only when there are no errors."""
        record = EvidenceRecord(evidence=_make_evidence(), validation_errors=())
        assert record.validated is True
        assert record.validation_errors == ()

    def test_validated_false_when_errors_present(self):
        """A single error flips validated to False."""
        record = EvidenceRecord(
            evidence=_make_evidence(),
            validation_errors=("reliability_score below threshold",),
        )
        assert record.validated is False

    def test_validation_errors_always_tuple(self):
        """Errors passed as a list are canonicalised to an immutable tuple."""
        record = EvidenceRecord(
            evidence=_make_evidence(),
            validation_errors=["a", "b"],
        )
        assert isinstance(record.validation_errors, tuple)
        assert record.validation_errors == ("a", "b")

    def test_validated_derived_overrides_argument(self):
        """Passing a mismatched ``validated`` cannot violate the invariant."""
        record = EvidenceRecord(
            evidence=_make_evidence(),
            validated=True,
            validation_errors=("boom",),
        )
        # Invariant wins: errors present => validated must be False.
        assert record.validated is False

    def test_to_dict_round_trips_record(self):
        record = EvidenceRecord(
            evidence=_make_evidence(),
            validation_errors=("one", "two"),
        )
        data = record.to_dict()
        assert data["validated"] is False
        assert data["validation_errors"] == ["one", "two"]
        assert data["evidence"]["id"] == "dataset_xauusd_001"

    def test_record_is_hashable(self):
        record = EvidenceRecord(evidence=_make_evidence(), validation_errors=())
        assert hash(record)  # does not raise


class TestEvidenceRecordImmutability:
    """EvidenceRecord is frozen."""

    def test_field_mutation_rejected(self):
        record = EvidenceRecord(evidence=_make_evidence(), validation_errors=())
        with pytest.raises(FrozenInstanceError):
            record.validated = False  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            record.validation_errors = ("x",)  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            record.evidence = _make_evidence()  # type: ignore[misc]

    def test_errors_tuple_does_not_mutate_through_evidence(self):
        """The wrapped evidence is the original immutable ReasoningEvidence."""
        ev = _make_evidence()
        record = EvidenceRecord(evidence=ev, validation_errors=())
        assert record.evidence is ev
