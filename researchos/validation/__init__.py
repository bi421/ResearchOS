"""Validation engine for ResearchOS — evaluates research against reality."""

from researchos.validation.rules import (
    VALIDATION_RULES,
    validate_evidence,
    validate_hypothesis,
    validate_observation,
    validate_scenario,
)
from researchos.validation.validators import (
    EvidenceValidator,
    ObjectValidator,
    ObservationValidator,
)

__all__ = [
    "ObservationValidator",
    "EvidenceValidator",
    "ObjectValidator",
    "VALIDATION_RULES",
    "validate_observation",
    "validate_evidence",
    "validate_hypothesis",
    "validate_scenario",
]
