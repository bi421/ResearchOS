"""
ResearchOS Macro Intelligence Layer - Feature Engineering Package
"""

from researchos.macro.features.definitions import (
    FeatureDefinition,
    FeatureValue,
    FeatureVector,
)
from researchos.macro.features.enums import (
    CalculationMethod,
    FeatureCategory,
    FeatureState,
    FeatureType,
    FeatureVersionCompatibility,
    ValidationRule,
)
from researchos.macro.features.pipeline import (
    FeatureCalculationResult,
    FeatureExtractor,
    FeatureNormalizer,
    FeaturePipeline,
    FeatureValidator,
)
from researchos.macro.features.registry import (
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
