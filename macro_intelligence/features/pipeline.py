"""
ResearchOS Macro Intelligence Layer - Feature Pipeline
Version: feat/pipeline/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List, Dict
from macro_intelligence.features.enums import FeatureCategory
from macro_intelligence.features.definitions import (
    FeatureDefinition,
    FeatureValue,
    FeatureVector,
)
from macro_intelligence.time.normalizer import TimeNormalizer


@dataclass(frozen=True)
class FeatureCalculationResult:
    """
    Result of a feature calculation.
    """
    
    feature_id: str
    timestamp: datetime
    value: Optional[float]
    quality_score: float
    calculation_time_ms: float
    evidence_ids: List[str]
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "feature_id": self.feature_id,
            "timestamp": TimeNormalizer.get_deterministic_timestamp(self.timestamp),
            "value": self.value,
            "quality_score": self.quality_score,
            "calculation_time_ms": self.calculation_time_ms,
            "evidence_ids": sorted(self.evidence_ids),
            "errors": self.errors,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureCalculationResult:
        """Deserialize from dictionary."""
        return cls(
            feature_id=data["feature_id"],
            timestamp=TimeNormalizer.parse_deterministic_timestamp(data["timestamp"]),
            value=data.get("value"),
            quality_score=data.get("quality_score", 1.0),
            calculation_time_ms=data.get("calculation_time_ms", 0.0),
            evidence_ids=data.get("evidence_ids", []),
            errors=data.get("errors", []),
        )


class FeatureExtractor:
    """
    Extracts features from evidence.
    
    MIL-FEAT-001: Features are deterministic functions of evidence.
    """
    
    def __init__(self):
        self.extractors: Dict[str, FeatureCategory] = {}
    
    def register_extractor(
        self,
        feature_id: str,
        category: FeatureCategory,
    ) -> None:
        """Register a feature extractor."""
        self.extractors[feature_id] = category
    
    def extract(
        self,
        definition: FeatureDefinition,
        evidence: Dict[str, Any],
        timestamp: datetime,
    ) -> FeatureCalculationResult:
        """
        Extract a feature from evidence.
        
        Returns:
            FeatureCalculationResult
        """
        # Implementation would go here
        # For now, return a placeholder result
        return FeatureCalculationResult(
            feature_id=definition.feature_id,
            timestamp=timestamp,
            value=None,
            quality_score=0.0,
            calculation_time_ms=0.0,
            evidence_ids=list(evidence.keys()),
            errors=["Feature extraction not yet implemented"],
        )


class FeatureValidator:
    """
    Validates feature values.
    """
    
    def validate(
        self,
        feature: FeatureValue,
        definition: FeatureDefinition,
    ) -> tuple[bool, List[str]]:
        """
        Validate a feature value.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate basic feature properties
        is_valid, base_errors = feature.validate()
        errors.extend(base_errors)
        
        # Validate against expected range
        if feature.value is not None and definition.expected_range:
            low, high = definition.expected_range
            if not (low <= feature.value <= high):
                errors.append(
                    f"Value {feature.value} outside expected range [{low}, {high}]"
                )
        
        # Validate no NaN or Inf
        if feature.value is not None:
            import math
            if math.isnan(feature.value) or math.isinf(feature.value):
                errors.append(f"Value {feature.value} is NaN or Inf")
        
        return (len(errors) == 0, errors)


class FeatureNormalizer:
    """
    Normalizes feature values.
    """
    
    def normalize(
        self,
        feature: FeatureValue,
        method: str = "zscore",
        history: List[float] = None,
    ) -> FeatureValue:
        """
        Normalize a feature value.
        
        Args:
            feature: Feature to normalize
            method: Normalization method (zscore, minmax, etc.)
            history: Historical values for normalization
        
        Returns:
            Normalized feature
        """
        # Implementation would go here
        return feature


class FeaturePipeline:
    """
    Complete feature engineering pipeline.
    
    Flow:
    Evidence -> Feature Extraction -> Feature Validation -> 
    Feature Normalization -> Feature Store -> Feature Vector
    """
    
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.validator = FeatureValidator()
        self.normalizer = FeatureNormalizer()
    
    def run(
        self,
        definitions: List[FeatureDefinition],
        evidence: Dict[str, Any],
        timestamp: datetime,
    ) -> FeatureVector:
        """
        Run the complete feature pipeline.
        
        Returns:
            FeatureVector with all calculated features
        """
        vector_id = f"VEC_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        vector = FeatureVector(
            vector_id=vector_id,
            timestamp=timestamp,
        )
        
        # Process each feature definition
        for definition in definitions:
            # Extract feature
            result = self.extractor.extract(definition, evidence, timestamp)
            
            # Create feature value
            feature = FeatureValue(
                feature_id=definition.feature_id,
                timestamp=timestamp,
                value=result.value,
                quality_score=result.quality_score,
                evidence_ids=result.evidence_ids,
                calculation_version=definition.calculation_version,
            )
            
            # Validate feature
            is_valid, errors = self.validator.validate(feature, definition)
            if not is_valid:
                feature = FeatureValue(
                    **feature.to_dict(),
                    is_valid=False,
                )
            
            # Add to vector
            vector = vector.add_feature(feature)
        
        return vector
    
    def get_dependency_graph(
        self,
        definitions: List[FeatureDefinition],
    ) -> Dict[str, List[str]]:
        """
        Get dependency graph for feature definitions.
        
        Returns:
            Dict mapping feature_id to list of dependencies
        """
        graph = {}
        for definition in definitions:
            dependencies = list(definition.required_evidence)
            dependencies.extend(definition.prerequisite_features)
            graph[definition.feature_id] = dependencies
        return graph
    
    def get_topological_order(
        self,
        definitions: List[FeatureDefinition],
    ) -> List[str]:
        """
        Get topological order for feature calculation.
        
        Returns:
            List of feature_ids in calculation order
        """
        graph = self.get_dependency_graph(definitions)
        
        # Simple topological sort
        ordered = []
        visited = set()
        
        def visit(feature_id: str):
            if feature_id in visited:
                return
            visited.add(feature_id)
            
            # Visit dependencies first
            for dep in graph.get(feature_id, []):
                visit(dep)
            
            ordered.append(feature_id)
        
        for feature_id in graph:
            visit(feature_id)
        
        return ordered
