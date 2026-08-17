"""
Machine Learning Feature Contracts
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class FeatureSet:
    name: str
    features: Dict[str, List[float]]
