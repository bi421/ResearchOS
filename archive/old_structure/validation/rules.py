"""
Validation rules for ResearchOS objects.

Based on Article XII: Validation Engine.
Based on Article XVII: Object Model — Validation Layer.

All validation rules are deterministic and version-controlled.
"""

from __future__ import annotations

from typing import Any

# Validation rule definitions
VALIDATION_RULES: dict[str, dict[str, Any]] = {
    "observation": {
        "completeness": "Value must not be None",
        "timeliness": "Timestamp must be in the past",
        "integrity": "Value must be int, float, str, or bool",
    },
    "evidence": {
        "quality_range": "Quality must be between 0.0 and 1.0",
        "confidence_range": "Confidence must be between 0.0 and 1.0",
        "weight_range": "Weight must be between 0.0 and 1.0",
        "tier_valid": "Tier must be Primary, Secondary, or Tertiary",
        "direction_valid": "Direction must be Supporting, Contradicting, or Neutral",
    },
    "hypothesis": {
        "type_valid": "Type must be Primary, Alternative, Null, or Tail",
        "rank_score_range": "Rank score must be between 0.0 and 1.0",
        "confidence_range": "Confidence must be between 0.0 and 1.0",
        "status_valid": "Status must be Active, Invalidated, or Retired",
    },
    "scenario": {
        "type_valid": "Type must be Base, Bull, Bear, or Tail",
        "probability_range": "Probability must be between 0.0 and 1.0",
        "status_valid": "Status must be Active, Valid, Invalidated, or Resolved",
    },
    "confidence": {
        "value_range": "Value must be between 0.0 and 1.0",
        "calibrated_range": "Calibrated value must be between 0.0 and 1.0",
        "interval_valid": "Lower bound must be <= upper bound",
    },
    "contradiction": {
        "type_valid": "Type must be Internal, Cross-Market, Macro, Timeframe, or Research",
        "severity_range": "Severity must be between 0.0 and 1.0",
        "resolution_valid": "Resolution must be Resolved, Unresolved, or Escalated",
    },
    "validation": {
        "status_valid": "Status must be In Progress, Accurate, Partially Accurate, or Inaccurate",
        "quality_range": "Quality score must be between 0.0 and 1.0",
    },
    "failure_analysis": {
        "failures_required": "At least one failure required for analysis",
    },
    "bias": {
        "type_valid": "Type must be a valid bias type",
        "frequency_range": "Frequency must be between 0.0 and 1.0",
        "severity_range": "Severity must be between 0.0 and 1.0",
    },
    "learning_record": {
        "dimension_valid": "Dimension must be a valid learning dimension",
        "score_range": "Score must be between 0.0 and 1.0",
        "trajectory_valid": "Trajectory must be Accelerating, Steady, Decelerating, or Plateauing",
    },
    "cognitive_assessment": {
        "score_range": "All scores must be between 0.0 and 1.0",
    },
    "research_cycle": {
        "stages_required": "At least one stage required",
    },
    "reasoning_chain": {
        "steps_required": "At least one step required",
        "confidence_range": "Confidence must be between 0.0 and 1.0",
    },
    "audit_entry": {
        "actor_required": "Actor is required",
        "action_required": "Action is required",
        "object_required": "Object ID and type are required",
    },
}


def validate_observation(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate an observation against the observation validation rules.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors: list[str] = []

    # Completeness check
    if data.get("value") is None:
        errors.append("Value must not be None")

    # Timeliness check
    from researchos.core.timestamp import parse_timestamp, utc_now

    timestamp = data.get("timestamp")
    if timestamp:
        try:
            ts = parse_timestamp(timestamp) if isinstance(timestamp, str) else timestamp
            if ts > utc_now():
                errors.append("Timestamp must be in the past")
        except (ValueError, TypeError):
            errors.append("Timestamp must be a valid ISO 8601 string")

    # Integrity check
    value = data.get("value")
    if value is not None and not isinstance(value, (int, float, str, bool)):
        errors.append("Value must be int, float, str, or bool")

    return (len(errors) == 0, errors)


def validate_evidence(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate an evidence object."""
    errors: list[str] = []

    quality = data.get("quality", 0.0)
    if not (0.0 <= quality <= 1.0):
        errors.append("Quality must be between 0.0 and 1.0")

    confidence = data.get("confidence", 0.0)
    if not (0.0 <= confidence <= 1.0):
        errors.append("Confidence must be between 0.0 and 1.0")

    weight = data.get("weight", 0.0)
    if not (0.0 <= weight <= 1.0):
        errors.append("Weight must be between 0.0 and 1.0")

    tier = data.get("tier", "")
    if tier not in ("Primary", "Secondary", "Tertiary"):
        errors.append("Tier must be Primary, Secondary, or Tertiary")

    direction = data.get("direction", "")
    if direction not in ("Supporting", "Contradicting", "Neutral"):
        errors.append("Direction must be Supporting, Contradicting, or Neutral")

    return (len(errors) == 0, errors)


def validate_hypothesis(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a hypothesis object."""
    errors: list[str] = []

    htype = data.get("type", "")
    if htype not in ("Primary", "Alternative", "Null", "Tail"):
        errors.append("Type must be Primary, Alternative, Null, or Tail")

    rank_score = data.get("rank_score", 0.0)
    if not (0.0 <= rank_score <= 1.0):
        errors.append("Rank score must be between 0.0 and 1.0")

    confidence = data.get("confidence", 0.0)
    if not (0.0 <= confidence <= 1.0):
        errors.append("Confidence must be between 0.0 and 1.0")

    status = data.get("status", "")
    if status not in ("Active", "Invalidated", "Retired"):
        errors.append("Status must be Active, Invalidated, or Retired")

    return (len(errors) == 0, errors)


def validate_scenario(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a scenario object."""
    errors: list[str] = []

    stype = data.get("type", "")
    if stype not in ("Base", "Bull", "Bear", "Tail"):
        errors.append("Type must be Base, Bull, Bear, or Tail")

    probability = data.get("probability", 0.0)
    if not (0.0 <= probability <= 1.0):
        errors.append("Probability must be between 0.0 and 1.0")

    status = data.get("status", "")
    if status not in ("Active", "Valid", "Invalidated", "Resolved"):
        errors.append("Status must be Active, Valid, Invalidated, or Resolved")

    return (len(errors) == 0, errors)
