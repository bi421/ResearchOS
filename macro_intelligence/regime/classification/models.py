"""
ResearchOS Macro Intelligence Layer - Classification Models

Data models for the regime classification engine.
All models are frozen (immutable) dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from macro_intelligence.regime.classification.taxonomy import (
    MacroRegime,
)


@dataclass(frozen=True)
class ClassificationRule:
    """
    A single classification rule.
    
    Frozen dataclass: immutable, hashable, deterministic.
    """
    
    # Identity
    rule_id: str
    rule_version: str
    
    # Rule content
    conditions: dict[str, str]
    result_regime: str
    description: str
    provenance: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "conditions": dict(sorted(self.conditions.items())),
            "result_regime": self.result_regime,
            "description": self.description,
            "provenance": self.provenance,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClassificationRule:
        return cls(
            rule_id=data["rule_id"],
            rule_version=data["rule_version"],
            conditions=data["conditions"],
            result_regime=data["result_regime"],
            description=data["description"],
            provenance=data.get("provenance", ""),
        )
    
    def matches(self, assessment_signals: dict[str, str]) -> bool:
        """Check if this rule matches the given assessment signals."""
        for key, expected_value in self.conditions.items():
            actual_value = assessment_signals.get(key)
            if actual_value != expected_value:
                return False
        return True
    
    def compute_hash(self) -> str:
        """Deterministic hash for the rule."""
        import hashlib
        import json
        hash_data = {
            "rule_id": self.rule_id,
            "conditions": dict(sorted(self.conditions.items())),
            "result_regime": self.result_regime,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class ClassificationEvidence:
    """
    Evidence supporting a classification decision.
    """
    
    # Rule that matched
    matching_rule_id: str
    matching_rule_version: str
    
    # Supporting signals from detectors
    signal_evidence: dict[str, str]
    
    # Derived explanation
    explanation: str = ""
    
    # Provenance
    detector_provenance: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "matching_rule_id": self.matching_rule_id,
            "matching_rule_version": self.matching_rule_version,
            "signal_evidence": dict(sorted(self.signal_evidence.items())),
            "explanation": self.explanation,
            "detector_provenance": dict(sorted(self.detector_provenance.items())),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClassificationEvidence:
        return cls(
            matching_rule_id=data["matching_rule_id"],
            matching_rule_version=data["matching_rule_version"],
            signal_evidence=data.get("signal_evidence", {}),
            explanation=data.get("explanation", ""),
            detector_provenance=data.get("detector_provenance", {}),
        )
    
    def compute_hash(self) -> str:
        """Deterministic hash for classification evidence."""
        import hashlib
        import json
        hash_data = {
            "matching_rule_id": self.matching_rule_id,
            "signal_evidence": dict(sorted(self.signal_evidence.items())),
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class RegimeClassification:
    """
    Final classification result from the regime classification engine.
    
    Frozen dataclass: immutable, hashable, deterministic.
    """
    
    # Identity
    classification_id: str
    algorithm_version: str
    
    # Classification results
    primary_regime: MacroRegime
    confidence: float
    evidence: ClassificationEvidence
    classification_time: datetime
    
    # Optional fields with defaults
    secondary_regimes: dict[str, str] = field(default_factory=dict)
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    
    # Metadata
    rule_applied: str = ""
    explanation: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "classification_id": self.classification_id,
            "algorithm_version": self.algorithm_version,
            "primary_regime": self.primary_regime.value,
            "secondary_regimes": dict(sorted(self.secondary_regimes.items())),
            "confidence": self.confidence,
            "confidence_breakdown": dict(sorted(self.confidence_breakdown.items())),
            "evidence": self.evidence.to_dict(),
            "classification_time": self.classification_time.isoformat(),
            "rule_applied": self.rule_applied,
            "explanation": self.explanation,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeClassification:
        return cls(
            classification_id=data["classification_id"],
            algorithm_version=data["algorithm_version"],
            primary_regime=MacroRegime(data["primary_regime"]),
            secondary_regimes=data.get("secondary_regimes", {}),
            confidence=data["confidence"],
            confidence_breakdown=data.get("confidence_breakdown", {}),
            evidence=ClassificationEvidence.from_dict(data["evidence"]),
            classification_time=datetime.fromisoformat(data["classification_time"]),
            rule_applied=data.get("rule_applied", ""),
            explanation=data.get("explanation", ""),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> RegimeClassification:
        """Deserialize from JSON."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compute_hash(self) -> str:
        """Deterministic hash for the classification."""
        import hashlib
        import json
        hash_data = {
            "classification_id": self.classification_id,
            "algorithm_version": self.algorithm_version,
            "primary_regime": self.primary_regime.value,
            "secondary_regimes": dict(sorted(self.secondary_regimes.items())),
            "confidence": self.confidence,
            "evidence": self.evidence.to_dict(),
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
