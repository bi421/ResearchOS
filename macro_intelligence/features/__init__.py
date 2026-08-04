"""
ResearchOS Macro Intelligence Layer - Feature Engineering Package
"""

from macro_intelligence.features.enums import (
    FeatureCategory,
    FeatureType,
    FeatureState,
    CalculationMethod,
    ValidationRule,
    FeatureVersionCompatibility,
)

from macro_intelligence.features.definitions import (
    FeatureDefinition,
    FeatureValue,
    FeatureVector,
)

from macro_intelligence.features.pipeline import (
    FeatureExtractor,
    FeatureValidator,
    FeatureNormalizer,
    FeaturePipeline,
    FeatureCalculationResult,
)

from macro_intelligence.features.registry import (
    FeatureRegistry,
    FeatureMetadata,
)

__all__ = [
    # Enums
    "FeatureCategory",
    "FeatureType",
    "FeatureState",
    "CalculationMethod",
    "ValidationRule",
    "FeatureVersionCompatibility",
    # Definitions
    "FeatureDefinition",
    "FeatureValue",
    "FeatureVector",
    "FeatureCalculationResult",
    # Pipeline
    "FeatureExtractor",
    "FeatureValidator",
    "FeatureNormalizer",
    "FeaturePipeline",
    # Registry
    "FeatureRegistry",
    "FeatureMetadata",
]
