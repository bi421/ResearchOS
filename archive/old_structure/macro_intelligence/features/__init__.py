"""
ResearchOS Macro Intelligence Layer - Feature Engineering Package
"""

from macro_intelligence.features.definitions import (
    FeatureDefinition,
    FeatureValue,
    FeatureVector,
)
from macro_intelligence.features.enums import (
    CalculationMethod,
    FeatureCategory,
    FeatureState,
    FeatureType,
    FeatureVersionCompatibility,
    ValidationRule,
)
from macro_intelligence.features.pipeline import (
    FeatureCalculationResult,
    FeatureExtractor,
    FeatureNormalizer,
    FeaturePipeline,
    FeatureValidator,
)
from macro_intelligence.features.registry import (
    FeatureMetadata,
    FeatureRegistry,
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
