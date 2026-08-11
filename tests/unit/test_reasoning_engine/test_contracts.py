"""
Tests for the Reasoning Engine contracts layer (Phase 4.5.1).

Verifies:
    1.  Valid EvidenceItem creation
    2.  Invalid reliability_score rejected
    3.  Empty id rejected
    4.  Empty source rejected
    5.  Valid Fact creation
    6.  Empty Fact statement rejected
    7.  Valid Hypothesis creation
    8.  Invalid confidence rejected
    9.  Dataclasses are frozen / immutable

Based on Article X: Reasoning Engine -- Contracts guarantees.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from researchos.reasoning_engine.contracts import (
    EvidenceItem,
    EvidenceType,
    Fact,
    Hypothesis,
    InvalidEvidenceTypeError,
    InvalidIdentifierError,
    InvalidReliabilityScoreError,
    ReasoningContractError,
)


# ============================================================================= #
# EvidenceItem
# ============================================================================= #


class TestEvidenceItem:
    """Tests for the EvidenceItem contract."""

    def _valid_data(self) -> dict:
        return dict(
            id="ev_001",
            source="FRED",
            evidence_type=EvidenceType.OBSERVATION,
            content_hash="sha256:abc123",
            reliability_score=0.85,
        )

    def test_valid_creation(self):
        """1. Valid EvidenceItem creation."""
        ev = EvidenceItem(**self._valid_data())
        assert ev.id == "ev_001"
        assert ev.source == "FRED"
        assert ev.evidence_type == EvidenceType.OBSERVATION
        assert ev.content_hash == "sha256:abc123"
        assert ev.reliability_score == 0.85

    def test_evidence_type_string_coercion(self):
        """A plain string for evidence_type is coerced into an EvidenceType."""
        ev = EvidenceItem(
            id="ev_002",
            source="FRED",
            evidence_type="dataset",
            content_hash="sha256:def456",
            reliability_score=1.0,
        )
        assert ev.evidence_type is EvidenceType.DATASET

    def _with_override(self, **overrides: object) -> dict:
        """Return a copy of the valid data with selected fields overridden."""
        return {**self._valid_data(), **overrides}

    def test_invalid_reliability_score_rejected(self):
        """2. Invalid reliability_score rejected."""
        for bad in (-0.01, 1.01, 1.5, -1.0):
            with pytest.raises(InvalidReliabilityScoreError):
                EvidenceItem(**self._with_override(reliability_score=bad))

    def test_reliability_score_boundary_values_accepted(self):
        """Boundary scores 0.0 and 1.0 are valid."""
        for boundary in (0.0, 1.0):
            ev = EvidenceItem(
                **self._with_override(reliability_score=boundary)
            )
            assert ev.reliability_score == boundary

    def test_empty_id_rejected(self):
        """3. Empty id rejected."""
        with pytest.raises(InvalidIdentifierError):
            EvidenceItem(**self._with_override(id=""))

    def test_whitespace_id_rejected(self):
        with pytest.raises(InvalidIdentifierError):
            EvidenceItem(**self._with_override(id="   "))

    def test_empty_source_rejected(self):
        """4. Empty source rejected."""
        with pytest.raises(InvalidIdentifierError):
            EvidenceItem(**self._with_override(source=""))

    def test_empty_content_hash_rejected(self):
        """Empty content_hash rejected."""
        with pytest.raises(InvalidIdentifierError):
            EvidenceItem(**self._with_override(content_hash=""))

    def test_invalid_evidence_type_rejected(self):
        with pytest.raises(InvalidEvidenceTypeError):
            EvidenceItem(**self._with_override(evidence_type="bogus"))

    def test_non_numeric_score_rejected(self):
        with pytest.raises(InvalidReliabilityScoreError):
            EvidenceItem(**self._with_override(reliability_score="high"))  # type: ignore[arg-type]

    def test_to_from_roundtrip(self):
        """to_dict / from_dict round-trips losslessly."""
        original = EvidenceItem(**self._valid_data())
        restored = EvidenceItem.from_dict(original.to_dict())
        assert restored == original


# ============================================================================= #
# Fact
# ============================================================================= #


class TestFact:
    """Tests for the Fact contract."""

    def _valid_data(self) -> dict:
        return dict(
            statement="CPI YoY declined to 2.8 percent in July 2024.",
            evidence_ids=("ev_001", "ev_002"),
        )

    def test_valid_creation(self):
        """5. Valid Fact creation."""
        fact = Fact(**self._valid_data())
        assert fact.statement == "CPI YoY declined to 2.8 percent in July 2024."
        assert fact.evidence_ids == ("ev_001", "ev_002")

    def test_evidence_ids_canonicalised_to_tuple(self):
        """A list of evidence ids is stored as an immutable tuple."""
        fact = Fact(statement="A test fact.", evidence_ids=["ev_001", "ev_002"])
        assert isinstance(fact.evidence_ids, tuple)
        assert fact.evidence_ids == ("ev_001", "ev_002")

    def test_empty_statement_rejected(self):
        """6. Empty Fact statement rejected."""
        with pytest.raises(InvalidIdentifierError):
            Fact(statement="", evidence_ids=("ev_001",))

    def test_whitespace_statement_rejected(self):
        with pytest.raises(InvalidIdentifierError):
            Fact(statement="   ", evidence_ids=("ev_001",))

    def test_to_from_roundtrip(self):
        original = Fact(**self._valid_data())
        restored = Fact.from_dict(original.to_dict())
        assert restored == original


# ============================================================================= #
# Hypothesis
# ============================================================================= #


class TestHypothesis:
    """Tests for the Hypothesis contract."""

    def _valid_data(self) -> dict:
        return dict(
            statement="Inflation will continue to moderate through 2025.",
            supporting_facts=("fact_001",),
            confidence=0.72,
        )

    def _with_override(self, **overrides: object) -> dict:
        """Return a copy of the valid data with selected fields overridden."""
        return {**self._valid_data(), **overrides}

    def test_valid_creation(self):
        """7. Valid Hypothesis creation."""
        hyp = Hypothesis(**self._valid_data())
        assert hyp.statement == "Inflation will continue to moderate through 2025."
        assert hyp.supporting_facts == ("fact_001",)
        assert hyp.confidence == 0.72

    def test_invalid_confidence_rejected(self):
        """8. Invalid confidence rejected."""
        for bad in (-0.01, 1.01, 2.0, -1.0):
            with pytest.raises(InvalidReliabilityScoreError):
                Hypothesis(**self._with_override(confidence=bad))

    def test_confidence_boundary_values_accepted(self):
        for boundary in (0.0, 1.0):
            hyp = Hypothesis(**self._with_override(confidence=boundary))
            assert hyp.confidence == boundary

    def test_empty_statement_rejected(self):
        with pytest.raises(InvalidIdentifierError):
            Hypothesis(statement="", supporting_facts=("fact_001",), confidence=0.5)

    def test_supporting_facts_canonicalised_to_tuple(self):
        hyp = Hypothesis(
            statement="A test hypothesis.",
            supporting_facts=["fact_001", "fact_002"],
            confidence=0.5,
        )
        assert isinstance(hyp.supporting_facts, tuple)
        assert hyp.supporting_facts == ("fact_001", "fact_002")

    def test_to_from_roundtrip(self):
        original = Hypothesis(**self._valid_data())
        restored = Hypothesis.from_dict(original.to_dict())
        assert restored == original


# ============================================================================= #
# Immutability / frozen-dataclass guarantee
# ============================================================================= #


class TestImmutability:
    """9. Dataclasses are frozen / immutable."""

    @pytest.mark.parametrize(
        "cls",
        [EvidenceItem, Fact, Hypothesis],
        ids=["EvidenceItem", "Fact", "Hypothesis"],
    )
    def test_is_frozen_dataclass(self, cls):
        assert is_dataclass(cls)

    def test_error_hierarchy_is_contract_error(self):
        assert issubclass(InvalidIdentifierError, ReasoningContractError)
        assert issubclass(InvalidReliabilityScoreError, ReasoningContractError)
        assert issubclass(InvalidEvidenceTypeError, ReasoningContractError)

    def test_evidence_item_frozen(self):
        ev = EvidenceItem(
            id="ev",
            source="s",
            evidence_type=EvidenceType.OBSERVATION,
            content_hash="h",
            reliability_score=0.5,
        )
        with pytest.raises(FrozenInstanceError):
            ev.id = "changed"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            ev.reliability_score = 0.1  # type: ignore[misc]

    def test_fact_frozen(self):
        fact = Fact(statement="s", evidence_ids=("e",))
        with pytest.raises(FrozenInstanceError):
            fact.statement = "changed"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            fact.evidence_ids = ("e9",)  # type: ignore[misc]

    def test_hypothesis_frozen(self):
        hyp = Hypothesis(statement="s", supporting_facts=("f",), confidence=0.5)
        with pytest.raises(FrozenInstanceError):
            hyp.statement = "changed"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            hyp.confidence = 0.1  # type: ignore[misc]
