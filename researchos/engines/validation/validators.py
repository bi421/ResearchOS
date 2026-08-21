"""Validator classes for ResearchOS objects.

Based on Article XII: Validation Engine.
Based on Article XVII: Object Model — Validation Layer.

Validators check objects against deterministic validation rules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Type

from researchos.core.base_object import BaseObject
from researchos.engines.validation.rules import (
    validate_evidence,
    validate_hypothesis,
    validate_observation,
    validate_scenario,
)


class ObjectValidator:
    """Base validator for all ResearchOS objects."""

    def validate(self, obj: BaseObject) -> Tuple[bool, List[str]]:
        data = obj.to_dict()
        return self._validate_dict(data)

    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        raise NotImplementedError("Subclasses must implement _validate_dict")


class ObservationValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return validate_observation(data)


class EvidenceValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return validate_evidence(data)


class HypothesisValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return validate_hypothesis(data)


class ScenarioValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return validate_scenario(data)


class ConfidenceValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        value = data.get("value", 0.0)
        if not (0.0 <= value <= 1.0):
            errors.append("Value must be between 0.0 and 1.0")
        calibrated = data.get("calibrated_value", 0.0)
        if not (0.0 <= calibrated <= 1.0):
            errors.append("Calibrated value must be between 0.0 and 1.0")
        lower = data.get("lower_bound", 0.0)
        upper = data.get("upper_bound", 1.0)
        if lower > upper:
            errors.append("Lower bound must be <= upper bound")
        return (len(errors) == 0, errors)


class ContradictionValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        ctype = data.get("type", "")
        if ctype not in ("Internal", "Cross-Market", "Macro", "Timeframe", "Research"):
            errors.append("Type must be Internal, Cross-Market, Macro, Timeframe, or Research")
        severity = data.get("severity", 0.0)
        if not (0.0 <= severity <= 1.0):
            errors.append("Severity must be between 0.0 and 1.0")
        resolution = data.get("resolution", "")
        if resolution not in ("Resolved", "Unresolved", "Escalated"):
            errors.append("Resolution must be Resolved, Unresolved, or Escalated")
        return (len(errors) == 0, errors)


class ValidationValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        status = data.get("overall_status", "")
        if status not in ("In Progress", "Accurate", "Partially Accurate", "Inaccurate"):
            errors.append("Status must be In Progress, Accurate, Partially Accurate, or Inaccurate")
        quality = data.get("quality_score", 0.0)
        if not (0.0 <= quality <= 1.0):
            errors.append("Quality score must be between 0.0 and 1.0")
        return (len(errors) == 0, errors)


class FailureAnalysisValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        failures = data.get("failures", [])
        if not failures:
            errors.append("At least one failure required for analysis")
        return (len(errors) == 0, errors)


class BiasValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        frequency = data.get("frequency", 0.0)
        if not (0.0 <= frequency <= 1.0):
            errors.append("Frequency must be between 0.0 and 1.0")
        severity = data.get("severity", 0.0)
        if not (0.0 <= severity <= 1.0):
            errors.append("Severity must be between 0.0 and 1.0")
        return (len(errors) == 0, errors)


class LearningRecordValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        score = data.get("score", 0.0)
        if not (0.0 <= score <= 1.0):
            errors.append("Score must be between 0.0 and 1.0")
        trajectory = data.get("trajectory", "")
        if trajectory not in ("Accelerating", "Steady", "Decelerating", "Plateauing"):
            errors.append("Trajectory must be Accelerating, Steady, Decelerating, or Plateauing")
        return (len(errors) == 0, errors)


class CognitiveAssessmentValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        for field in (
            "knowledge_score",
            "reasoning_score",
            "discipline_score",
            "reflection_score",
            "learning_progress",
            "overall_score",
        ):
            val = data.get(field, 0.0)
            if not (0.0 <= val <= 1.0):
                errors.append(f"{field} must be between 0.0 and 1.0")
        return (len(errors) == 0, errors)


class ResearchCycleValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        stages = data.get("stages", [])
        if not stages:
            errors.append("At least one stage required")
        return (len(errors) == 0, errors)


class ReasoningChainValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        steps = data.get("steps", [])
        if not steps:
            errors.append("At least one step required")
        confidence = data.get("confidence", 0.0)
        if not (0.0 <= confidence <= 1.0):
            errors.append("Confidence must be between 0.0 and 1.0")
        return (len(errors) == 0, errors)


class AuditEntryValidator(ObjectValidator):
    def _validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not data.get("actor"):
            errors.append("Actor is required")
        if not data.get("action"):
            errors.append("Action is required")
        if not data.get("object_id") or not data.get("object_type"):
            errors.append("Object ID and type are required")
        return (len(errors) == 0, errors)


VALIDATOR_REGISTRY: Dict[str, Type[ObjectValidator]] = {
    "Observation": ObservationValidator,
    "Evidence": EvidenceValidator,
    "Hypothesis": HypothesisValidator,
    "Scenario": ScenarioValidator,
    "Confidence": ConfidenceValidator,
    "Contradiction": ContradictionValidator,
    "Validation": ValidationValidator,
    "FailureAnalysis": FailureAnalysisValidator,
    "Bias": BiasValidator,
    "LearningRecord": LearningRecordValidator,
    "CognitiveAssessment": CognitiveAssessmentValidator,
    "ResearchCycle": ResearchCycleValidator,
    "ReasoningChain": ReasoningChainValidator,
    "AuditEntry": AuditEntryValidator,
}


def get_validator(obj_type: str) -> ObjectValidator:
    validator_class = VALIDATOR_REGISTRY.get(obj_type)
    if validator_class is None:
        raise ValueError(f"No validator registered for type: {obj_type}")
    return validator_class()
