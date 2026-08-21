"""
ResearchOS Macro Intelligence Layer - Regime Contracts
Version: regime/contracts/v1
Status: FROZEN

MIL-REG-001: Regime objects are immutable.
MIL-REG-002: Every regime preserves provenance.
MIL-REG-003: Same evidence produces identical regime object.
MIL-REG-004: Contracts are backward compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional

from researchos.macro.provenance.chain import ProvenanceChain
from researchos.macro.time.normalizer import TimeNormalizer


@dataclass(frozen=True)
class RegimeConfidence:
    """
    Immutable confidence measurement for regime classification.

    MIL-REG-001: Regime objects are immutable.
    """

    level: float  # 0.0 to 1.0
    evidence_count: int
    data_quality: float  # 0.0 to 1.0
    model_version: str
    calculated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "level": self.level,
            "evidence_count": self.evidence_count,
            "data_quality": self.data_quality,
            "model_version": self.model_version,
            "calculated_at": TimeNormalizer.get_deterministic_timestamp(self.calculated_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeConfidence:
        """Deserialize from dictionary."""
        return cls(
            level=data["level"],
            evidence_count=data["evidence_count"],
            data_quality=data["data_quality"],
            model_version=data["model_version"],
            calculated_at=TimeNormalizer.parse_deterministic_timestamp(data["calculated_at"]),
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RegimeConfidence:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "level": self.level,
            "evidence_count": self.evidence_count,
            "data_quality": self.data_quality,
            "model_version": self.model_version,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RegimeEvidence:
    """
    Immutable evidence supporting regime classification.

    MIL-REG-002: Every regime preserves provenance.
    """

    evidence_id: str
    source: str
    timestamp: datetime
    value: float
    contribution: float  # How much this evidence contributes to regime
    weight: float  # Weight assigned to this evidence

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "value": self.value,
            "contribution": self.contribution,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeEvidence:
        """Deserialize from dictionary."""
        return cls(
            evidence_id=data["evidence_id"],
            source=data["source"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            value=data["value"],
            contribution=data["contribution"],
            weight=data["weight"],
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RegimeEvidence:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "value": self.value,
            "contribution": self.contribution,
            "weight": self.weight,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RegimeAssessment:
    """
    Immutable assessment of a regime state.

    MIL-REG-001: Regime objects are immutable.
    MIL-REG-003: Same evidence produces identical regime object.
    """

    assessment_id: str
    timestamp: datetime
    inflation_state: str
    growth_state: str
    monetary_state: str
    liquidity_state: str
    employment_state: str
    risk_state: str
    confidence: RegimeConfidence
    evidence: List[RegimeEvidence] = field(default_factory=list)
    severity: str = "normal"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "assessment_id": self.assessment_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "inflation_state": self.inflation_state,
            "growth_state": self.growth_state,
            "monetary_state": self.monetary_state,
            "liquidity_state": self.liquidity_state,
            "employment_state": self.employment_state,
            "risk_state": self.risk_state,
            "confidence": self.confidence.to_dict(),
            "evidence_count": len(self.evidence),
            "severity": self.severity,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeAssessment:
        """Deserialize from dictionary."""
        confidence = RegimeConfidence.from_dict(data["confidence"])
        evidence = [RegimeEvidence.from_dict(e) for e in data.get("evidence", [])]
        return cls(
            assessment_id=data["assessment_id"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            inflation_state=data["inflation_state"],
            growth_state=data["growth_state"],
            monetary_state=data["monetary_state"],
            liquidity_state=data["liquidity_state"],
            employment_state=data["employment_state"],
            risk_state=data["risk_state"],
            confidence=confidence,
            evidence=evidence,
            severity=data.get("severity", "normal"),
            notes=data.get("notes", ""),
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RegimeAssessment:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "assessment_id": self.assessment_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "inflation_state": self.inflation_state,
            "growth_state": self.growth_state,
            "monetary_state": self.monetary_state,
            "liquidity_state": self.liquidity_state,
            "employment_state": self.employment_state,
            "risk_state": self.risk_state,
            "severity": self.severity,
            "confidence_level": self.confidence.level,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RegimeSnapshot:
    """
    Immutable snapshot of regime state at a point in time.

    MIL-REG-001: Regime objects are immutable.
    MIL-REG-002: Every regime preserves provenance.
    """

    snapshot_id: str
    timestamp: datetime
    assessment: RegimeAssessment
    version: str = "regime/contracts/v1"
    provenance: Optional[ProvenanceChain] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "assessment": self.assessment.to_dict(),
            "version": self.version,
            "has_provenance": self.provenance is not None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeSnapshot:
        """Deserialize from dictionary."""
        assessment = RegimeAssessment.from_dict(data["assessment"])
        provenance = None
        if data.get("has_provenance") and data.get("provenance"):
            provenance = ProvenanceChain.from_dict(data["provenance"])
        return cls(
            snapshot_id=data["snapshot_id"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            assessment=assessment,
            version=data.get("version", "regime/contracts/v1"),
            provenance=provenance,
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RegimeSnapshot:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "snapshot_id": self.snapshot_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "assessment_hash": self.assessment.compute_hash(),
            "version": self.version,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MacroRegime:
    """
    Immutable macro regime definition.

    MIL-REG-001: Regime objects are immutable.
    MIL-REG-003: Same evidence produces identical regime object.
    """

    regime_id: str
    name: str
    description: str
    timestamp: datetime
    inflation_state: str
    growth_state: str
    monetary_state: str
    liquidity_state: str
    employment_state: str
    risk_state: str
    severity: str
    confidence: RegimeConfidence
    evidence: List[RegimeEvidence] = field(default_factory=list)
    version: str = "regime/contracts/v1"
    provenance: Optional[ProvenanceChain] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "regime_id": self.regime_id,
            "name": self.name,
            "description": self.description,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "inflation_state": self.inflation_state,
            "growth_state": self.growth_state,
            "monetary_state": self.monetary_state,
            "liquidity_state": self.liquidity_state,
            "employment_state": self.employment_state,
            "risk_state": self.risk_state,
            "severity": self.severity,
            "confidence": self.confidence.to_dict(),
            "evidence_count": len(self.evidence),
            "version": self.version,
            "has_provenance": self.provenance is not None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroRegime:
        """Deserialize from dictionary."""
        confidence = RegimeConfidence.from_dict(data["confidence"])
        evidence = [RegimeEvidence.from_dict(e) for e in data.get("evidence", [])]
        provenance = None
        if data.get("has_provenance") and data.get("provenance"):
            provenance = ProvenanceChain.from_dict(data["provenance"])
        return cls(
            regime_id=data["regime_id"],
            name=data["name"],
            description=data["description"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            inflation_state=data["inflation_state"],
            growth_state=data["growth_state"],
            monetary_state=data["monetary_state"],
            liquidity_state=data["liquidity_state"],
            employment_state=data["employment_state"],
            risk_state=data["risk_state"],
            severity=data.get("severity", "normal"),
            confidence=confidence,
            evidence=evidence,
            version=data.get("version", "regime/contracts/v1"),
            provenance=provenance,
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> MacroRegime:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "regime_id": self.regime_id,
            "name": self.name,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "inflation_state": self.inflation_state,
            "growth_state": self.growth_state,
            "monetary_state": self.monetary_state,
            "liquidity_state": self.liquidity_state,
            "employment_state": self.employment_state,
            "risk_state": self.risk_state,
            "severity": self.severity,
            "confidence_level": self.confidence.level,
            "version": self.version,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Type aliases for clarity
InflationRegime = str
GrowthRegime = str
MonetaryRegime = str
LiquidityRegime = str
EmploymentRegime = str
RiskRegime = str
