"""
Probability & Statistics Engine — contracts, enums, and dataclass models.

Research-only statistical computation. No ML. No trading logic.
All distributions and estimators are deterministic given a fixed seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class DistributionType(str, Enum):
    NORMAL = "normal"
    STUDENT_T = "student_t"
    LOG_NORMAL = "log_normal"
    EMPIRICAL = "empirical"
    KDE = "kde"


class TestStatistic(str, Enum):
    Z = "z"
    T = "t"
    CHI2 = "chi2"
    F = "f"


@dataclass(frozen=True)
class DistributionFit:
    """Parameters of a fitted distribution."""

    distribution: DistributionType
    parameters: Dict[str, float] = field(default_factory=dict)
    log_likelihood: float = 0.0
    sample_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "distribution": self.distribution.value,
            "parameters": dict(sorted(self.parameters.items())),
            "log_likelihood": self.log_likelihood,
            "sample_size": self.sample_size,
        }


@dataclass(frozen=True)
class ConfidenceInterval:
    """A confidence interval for a statistic."""

    lower: float
    upper: float
    confidence_level: float
    method: str

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "confidence_level": self.confidence_level,
            "method": self.method,
        }


@dataclass(frozen=True)
class HypothesisTestResult:
    """Result of a hypothesis test."""

    statistic: float
    p_value: float
    null_hypothesis: str
    alternative_hypothesis: str
    significance_level: float
    test_name: str

    @property
    def is_significant(self) -> bool:
        return self.p_value < self.significance_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": self.statistic,
            "p_value": self.p_value,
            "null_hypothesis": self.null_hypothesis,
            "alternative_hypothesis": self.alternative_hypothesis,
            "significance_level": self.significance_level,
            "test_name": self.test_name,
            "is_significant": self.is_significant,
        }


@dataclass(frozen=True)
class MonteCarloResult:
    """Result of a Monte Carlo simulation."""

    samples: List[float] = field(default_factory=list)
    mean: float = 0.0
    std: float = 0.0
    percentiles: Dict[float, float] = field(default_factory=dict)
    seed: int = 0
    num_samples: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": self.mean,
            "std": self.std,
            "percentiles": dict(sorted(self.percentiles.items())),
            "seed": self.seed,
            "num_samples": self.num_samples,
        }

