"""
Machine Learning Feature Contracts
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureSet:
    name: str
    features: dict[str, list[float]]
