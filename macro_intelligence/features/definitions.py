"""
ResearchOS Macro Intelligence Layer - Feature Definitions
Version: feat/def/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from macro_intelligence.features.enums import (
    CalculationMethod,
    FeatureCategory,
    FeatureType,
    ValidationRule,
)
from macro_intelligence.time.normalizer import UTC, TimeNormalizer


@dataclass(frozen=True)
class FeatureDefinition:
    """
    Immutable feature definition.

    MIL-FEAT-001: Features are deterministic functions of evidence.
    MIL-FEAT-003: Every feature has complete provenance.

    Defines:
    - Feature name and category
    - Calculation method and parameters
    - Validation rules
    - Version information
    """

    # Identity
    feature_id: str
    feature_name: str
    category: FeatureCategory
    feature_type: FeatureType

    # Calculation
    method: CalculationMethod
    parameters: dict = field(default_factory=dict)

    # Dependencies
    required_evidence: list[str] = field(default_factory=list)
    prerequisite_features: list[str] = field(default_factory=list)

    # Validation
    validation_rules: list[ValidationRule] = field(default_factory=list)
    expected_range: tuple[float, float] | None = None

    # Version
    version: str = "feat/def/v1"
    calculation_version: str = "calc/v1"

    # Metadata
    description: str = ""
    unit: str = ""
    metadata: dict = field(default_factory=dict)

    # Generated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "category": self.category.value,
            "feature_type": self.feature_type.value,
            "method": self.method.value,
            "parameters": self.parameters,
            "required_evidence": sorted(self.required_evidence),
            "prerequisite_features": sorted(self.prerequisite_features),
            "validation_rules": [r.value for r in self.validation_rules],
            "expected_range": self.expected_range,
            "version": self.version,
            "calculation_version": self.calculation_version,
            "description": self.description,
            "unit": self.unit,
            "metadata": self.metadata,
            "created_at": TimeNormalizer.get_deterministic_timestamp(self.created_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureDefinition:
        """Deserialize from dictionary."""
        return cls(
            feature_id=data["feature_id"],
            feature_name=data["feature_name"],
            category=FeatureCategory(data["category"]),
            feature_type=FeatureType(data["feature_type"]),
            method=CalculationMethod(data["method"]),
            parameters=data.get("parameters", {}),
            required_evidence=data.get("required_evidence", []),
            prerequisite_features=data.get("prerequisite_features", []),
            validation_rules=[ValidationRule(r) for r in data.get("validation_rules", [])],
            expected_range=data.get("expected_range"),
            version=data.get("version", "feat/def/v1"),
            calculation_version=data.get("calculation_version", "calc/v1"),
            description=data.get("description", ""),
            unit=data.get("unit", ""),
            metadata=data.get("metadata", {}),
            created_at=TimeNormalizer.parse_deterministic_timestamp(
                data.get("created_at", TimeNormalizer.get_deterministic_timestamp(datetime.now(UTC)))
            ),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> FeatureDefinition:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Compute deterministic hash.

        MIL-FEAT-001: Features are deterministic functions of evidence.
        """
        import hashlib

        # Exclude runtime metadata from hash
        hash_data = {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "category": self.category.value,
            "feature_type": self.feature_type.value,
            "method": self.method.value,
            "parameters": self.parameters,
            "required_evidence": sorted(self.required_evidence),
            "prerequisite_features": sorted(self.prerequisite_features),
            "calculation_version": self.calculation_version,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the feature definition.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Validate feature_id format
        if not self.feature_id.startswith("FEAT_"):
            errors.append("feature_id must start with 'FEAT_'")

        # Validate feature_name is not empty
        if not self.feature_name:
            errors.append("feature_name cannot be empty")

        # Validate dependencies don't reference self
        if self.feature_id in self.prerequisite_features:
            errors.append("Feature cannot depend on itself")

        # Validate expected range
        if self.expected_range:
            low, high = self.expected_range
            if low >= high:
                errors.append("expected_range low must be < high")

        return (len(errors) == 0, errors)

    def requires_history(self) -> bool:
        """Check if feature calculation requires historical data."""
        return self.method.requires_history()

    def is_bivariate(self) -> bool:
        """Check if feature is bivariate."""
        return self.feature_type.is_bivariate()


@dataclass(frozen=True)
class FeatureValue:
    """
    Immutable feature value with provenance.

    MIL-FEAT-002: Feature vectors are immutable.
    MIL-FEAT-003: Every feature has complete provenance.
    """

    # Identity
    feature_id: str
    timestamp: datetime

    # Value
    value: float | None

    # Quality
    quality_score: float = 1.0
    is_valid: bool = True

    # Provenance
    evidence_ids: list[str] = field(default_factory=list)
    calculation_version: str = "calc/v1"

    # Generated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: str = "feat/val/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "feature_id": self.feature_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "value": self.value,
            "quality_score": self.quality_score,
            "is_valid": self.is_valid,
            "evidence_ids": sorted(self.evidence_ids),
            "calculation_version": self.calculation_version,
            "created_at": TimeNormalizer.get_deterministic_timestamp(self.created_at),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureValue:
        """Deserialize from dictionary."""
        return cls(
            feature_id=data["feature_id"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            value=data.get("value"),
            quality_score=data.get("quality_score", 1.0),
            is_valid=data.get("is_valid", True),
            evidence_ids=data.get("evidence_ids", []),
            calculation_version=data.get("calculation_version", "calc/v1"),
            created_at=TimeNormalizer.parse_deterministic_timestamp(
                data.get("created_at", TimeNormalizer.get_deterministic_timestamp(datetime.now(UTC)))
            ),
            version=data.get("version", "feat/val/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> FeatureValue:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "feature_id": self.feature_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "value": self.value,
            "quality_score": self.quality_score,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the feature value."""
        errors = []

        # Validate feature_id format
        if not self.feature_id.startswith("FEAT_"):
            errors.append("feature_id must start with 'FEAT_'")

        # Validate quality score
        if not (0.0 <= self.quality_score <= 1.0):
            errors.append("quality_score must be between 0.0 and 1.0")

        # Validate value if present
        if self.value is not None:
            import math

            if math.isnan(self.value) or math.isinf(self.value):
                errors.append("value cannot be NaN or Inf")

        return (len(errors) == 0, errors)


@dataclass(frozen=True)
class FeatureVector:
    """
    Immutable feature vector for a specific timestamp.

    MIL-FEAT-002: Feature vectors are immutable.
    MIL-FEAT-005: Feature vectors are reproducible.
    """

    # Identity
    vector_id: str
    timestamp: datetime

    # Features
    features: dict[str, FeatureValue] = field(default_factory=dict)

    # Metadata
    version: str = "feat/vec/v1"
    calculation_version: str = "calc/v1"

    # Generated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "vector_id": self.vector_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "feature_count": len(self.features),
            "version": self.version,
            "calculation_version": self.calculation_version,
            "created_at": TimeNormalizer.get_deterministic_timestamp(self.created_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureVector:
        """Deserialize from dictionary."""
        return cls(
            vector_id=data["vector_id"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            features=data.get("features", {}),
            version=data.get("version", "feat/vec/v1"),
            calculation_version=data.get("calculation_version", "calc/v1"),
            created_at=TimeNormalizer.parse_deterministic_timestamp(
                data.get("created_at", TimeNormalizer.get_deterministic_timestamp(datetime.now(UTC)))
            ),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> FeatureVector:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "vector_id": self.vector_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "feature_count": len(self.features),
            "calculation_version": self.calculation_version,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def add_feature(self, feature: FeatureValue) -> FeatureVector:
        """
        Add a feature to the vector.

        Returns:
            New FeatureVector with feature added
        """
        new_features = dict(self.features)
        new_features[feature.feature_id] = feature
        return FeatureVector(
            vector_id=self.vector_id,
            timestamp=self.timestamp,
            features=new_features,
            version=self.version,
            calculation_version=self.calculation_version,
            created_at=self.created_at,
        )

    def get_feature(self, feature_id: str) -> FeatureValue | None:
        """Get a feature by ID."""
        return self.features.get(feature_id)

    def get_feature_values(self) -> dict[str, float | None]:
        """Get all feature values as dict."""
        return {fid: fvalue.value for fid, fvalue in self.features.items()}

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the feature vector."""
        errors = []

        # Validate vector_id format
        if not self.vector_id.startswith("VEC_"):
            errors.append("vector_id must start with 'VEC_'")

        # Validate each feature
        for feature_id, feature in self.features.items():
            is_valid, feature_errors = feature.validate()
            if not is_valid:
                errors.extend([f"{feature_id}: {e}" for e in feature_errors])

        return (len(errors) == 0, errors)
