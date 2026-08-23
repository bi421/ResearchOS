"""
ResearchOS Macro Intelligence Layer - Feature Registry
Version: feat/registry/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from macro_intelligence.features.definitions import FeatureDefinition
from macro_intelligence.features.enums import FeatureCategory
from macro_intelligence.time.normalizer import TimeNormalizer


@dataclass(frozen=True)
class FeatureMetadata:
    """
    Metadata for a feature in the registry.
    """

    feature_id: str
    category: FeatureCategory
    description: str
    unit: str
    version: str
    calculation_version: str
    created_at: datetime
    last_calculated: datetime | None = None
    calculation_count: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "feature_id": self.feature_id,
            "category": self.category.value,
            "description": self.description,
            "unit": self.unit,
            "version": self.version,
            "calculation_version": self.calculation_version,
            "created_at": TimeNormalizer.get_deterministic_timestamp(self.created_at),
            "last_calculated": TimeNormalizer.get_deterministic_timestamp(self.last_calculated) if self.last_calculated else None,
            "calculation_count": self.calculation_count,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureMetadata:
        """Deserialize from dictionary."""
        return cls(
            feature_id=data["feature_id"],
            category=FeatureCategory(data["category"]),
            description=data.get("description", ""),
            unit=data.get("unit", ""),
            version=data.get("version", "feat/registry/v1"),
            calculation_version=data.get("calculation_version", "calc/v1"),
            created_at=TimeNormalizer.parse_deterministic_timestamp(data["created_at"]),
            last_calculated=TimeNormalizer.parse_deterministic_timestamp(data["last_calculated"]) if data.get("last_calculated") else None,
            calculation_count=data.get("calculation_count", 0),
            errors=data.get("errors", []),
        )


class FeatureRegistry:
    """
    Registry for feature definitions and metadata.

    Supports:
    - Feature discovery
    - Versioning
    - Dependency graph
    - Metadata
    - Categories
    - Calculation version
    """

    def __init__(self):
        self.features: dict[str, FeatureDefinition] = {}
        self.metadata: dict[str, FeatureMetadata] = {}
        self.versions: dict[str, str] = {}

    def register(
        self,
        definition: FeatureDefinition,
        description: str = "",
        unit: str = "",
    ) -> None:
        """
        Register a feature definition.

        Args:
            definition: Feature definition to register
            description: Human-readable description
            unit: Unit of measurement
        """
        self.features[definition.feature_id] = definition

        # Create metadata
        metadata = FeatureMetadata(
            feature_id=definition.feature_id,
            category=definition.category,
            description=description or definition.description,
            unit=unit or definition.unit,
            version=definition.version,
            calculation_version=definition.calculation_version,
            created_at=definition.created_at,
        )
        self.metadata[definition.feature_id] = metadata

        # Track version
        self.versions[definition.feature_id] = definition.version

    def get(self, feature_id: str) -> FeatureDefinition | None:
        """
        Get a feature definition by ID.

        Returns:
            FeatureDefinition or None
        """
        return self.features.get(feature_id)

    def get_metadata(self, feature_id: str) -> FeatureMetadata | None:
        """
        Get metadata for a feature.

        Returns:
            FeatureMetadata or None
        """
        return self.metadata.get(feature_id)

    def get_by_category(
        self,
        category: FeatureCategory,
    ) -> list[FeatureDefinition]:
        """
        Get all features in a category.

        Returns:
            List of FeatureDefinitions
        """
        return [feat for feat in self.features.values() if feat.category == category]

    def get_all(self) -> list[FeatureDefinition]:
        """
        Get all registered features.

        Returns:
            List of all FeatureDefinitions
        """
        return list(self.features.values())

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """
        Get complete dependency graph.

        Returns:
            Dict mapping feature_id to list of dependencies
        """
        graph = {}
        for feature_id, definition in self.features.items():
            dependencies = list(definition.required_evidence)
            dependencies.extend(definition.prerequisite_features)
            graph[feature_id] = dependencies
        return graph

    def get_topological_order(self) -> list[str]:
        """
        Get topological order for feature calculation.

        Returns:
            List of feature_ids in calculation order
        """
        graph = self.get_dependency_graph()

        # Kahn's algorithm for topological sort
        in_degree = {fid: 0 for fid in graph}
        for fid, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[fid] = in_degree.get(fid, 0)

        # Recalculate in-degrees
        in_degree = {fid: 0 for fid in graph}
        for fid, deps in graph.items():
            for dep in deps:
                if dep in graph:
                    in_degree[fid] = in_degree.get(fid, 0) + 1

        # Start with nodes having no dependencies
        queue = [fid for fid, deg in in_degree.items() if deg == 0]
        ordered = []

        while queue:
            fid = queue.pop(0)
            ordered.append(fid)

            # Reduce in-degree for dependents
            for other_fid, deps in graph.items():
                if fid in deps:
                    in_degree[other_fid] -= 1
                    if in_degree[other_fid] == 0:
                        queue.append(other_fid)

        return ordered

    def get_version(self, feature_id: str) -> str | None:
        """
        Get version for a feature.

        Returns:
            Version string or None
        """
        return self.versions.get(feature_id)

    def get_calculation_version(self, feature_id: str) -> str | None:
        """
        Get calculation version for a feature.

        Returns:
            Calculation version string or None
        """
        feature = self.features.get(feature_id)
        return feature.calculation_version if feature else None

    def increment_calculation_count(self, feature_id: str) -> None:
        """
        Increment calculation count for a feature.

        Args:
            feature_id: Feature ID
        """
        if feature_id in self.metadata:
            metadata = self.metadata[feature_id]
            # Create new metadata with incremented count
            new_metadata = FeatureMetadata(
                feature_id=metadata.feature_id,
                category=metadata.category,
                description=metadata.description,
                unit=metadata.unit,
                version=metadata.version,
                calculation_version=metadata.calculation_version,
                created_at=metadata.created_at,
                last_calculated=metadata.last_calculated,
                calculation_count=metadata.calculation_count + 1,
                errors=metadata.errors,
            )
            self.metadata[feature_id] = new_metadata

    def add_error(self, feature_id: str, error: str) -> None:
        """
        Add an error to a feature's metadata.

        Args:
            feature_id: Feature ID
            error: Error message
        """
        if feature_id in self.metadata:
            metadata = self.metadata[feature_id]
            new_errors = list(metadata.errors)
            new_errors.append(error)

            new_metadata = FeatureMetadata(
                feature_id=metadata.feature_id,
                category=metadata.category,
                description=metadata.description,
                unit=metadata.unit,
                version=metadata.version,
                calculation_version=metadata.calculation_version,
                created_at=metadata.created_at,
                last_calculated=metadata.last_calculated,
                calculation_count=metadata.calculation_count,
                errors=new_errors,
            )
            self.metadata[feature_id] = new_metadata

    def get_statistics(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with registry statistics
        """
        return {
            "total_features": len(self.features),
            "total_versions": len(set(self.versions.values())),
            "features_by_category": {cat.value: len(self.get_by_category(cat)) for cat in FeatureCategory},
            "total_calculations": sum(m.calculation_count for m in self.metadata.values()),
            "features_with_errors": sum(1 for m in self.metadata.values() if m.errors),
        }
