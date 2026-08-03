"""
Contracts, enums, and data classes for the Quant Research Experiment Framework.

Based on Article XVII: Object Model — Experiment Layer.
Based on Article III: Principles — Determinism, Repeatability, Auditability.

Defines the shared vocabulary used across all experiment objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ExperimentStatus(str, Enum):
    """Lifecycle status of an Experiment."""

    DRAFT = "Draft"
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    VALIDATED = "Validated"
    ARCHIVED = "Archived"


class ExperimentType(str, Enum):
    """The type of experiment to run."""

    BACKTEST = "Backtest"
    WALK_FORWARD = "WalkForward"
    STRESS_TEST = "StressTest"
    MONTE_CARLO = "MonteCarlo"
    SENSITIVITY = "Sensitivity"
    A_B = "A/B"
    CUSTOM = "Custom"


class HypothesisStatus(str, Enum):
    """Status of a QuantHypothesis through the testing lifecycle."""

    FORMULATED = "Formulated"
    READY = "Ready"
    TESTING = "Testing"
    TESTED = "Tested"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    INCONCLUSIVE = "Inconclusive"


class ValidationStatus(str, Enum):
    """Outcome of an experiment validation."""

    PENDING = "Pending"
    PASSED = "Passed"
    FAILED = "Failed"
    INCONCLUSIVE = "Inconclusive"


@dataclass
class DatasetConfig:
    """
    Configuration for binding a dataset to an experiment.

    All parameters are captured so the experiment is fully repeatable.
    Future C++ Quant Engine can load datasets from this config.

    Attributes:
        source: Dataset identifier or path.
        start_date: ISO 8601 start date for the data window.
        end_date: ISO 8601 end date for the data window.
        symbols: List of asset symbols or identifiers.
        resolution: Data resolution (e.g., "1m", "1h", "1d").
        filters: Optional filters to apply (e.g., market hours only).
        parameters: Additional dataset-specific parameters.
    """

    source: str
    start_date: str = ""
    end_date: str = ""
    symbols: List[str] = field(default_factory=list)
    resolution: str = "1d"
    filters: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return {
            "source": self.source,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "symbols": sorted(self.symbols),
            "resolution": self.resolution,
            "filters": sorted(self.filters),
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetConfig":
        """Deserialize from a dictionary."""
        return cls(
            source=data["source"],
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            symbols=list(data.get("symbols", [])),
            resolution=data.get("resolution", "1d"),
            filters=list(data.get("filters", [])),
            parameters=dict(data.get("parameters", {})),
        )


@dataclass
class SimulationConfig:
    """
    Configuration for the simulation engine.

    All parameters are captured so the simulation is fully repeatable.
    Future C++ Quant Engine will accept this exact config.

    Attributes:
        seed: Deterministic random seed for reproducibility.
        initial_capital: Starting capital for the simulation.
        commission: Commission model (e.g., "fixed:0.01" or "pct:0.001").
        slippage: Slippage model (e.g., "fixed:0.001" or "pct:0.0005").
        max_positions: Maximum number of concurrent positions.
        parameters: Additional simulation-specific parameters.
    """

    seed: int = 42
    initial_capital: float = 100_000.0
    commission: str = "fixed:0.0"
    slippage: str = "fixed:0.0"
    max_positions: int = 10
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return {
            "seed": self.seed,
            "initial_capital": self.initial_capital,
            "commission": self.commission,
            "slippage": self.slippage,
            "max_positions": self.max_positions,
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationConfig":
        """Deserialize from a dictionary."""
        return cls(
            seed=int(data.get("seed", 42)),
            initial_capital=float(data.get("initial_capital", 100_000.0)),
            commission=str(data.get("commission", "fixed:0.0")),
            slippage=str(data.get("slippage", "fixed:0.0")),
            max_positions=int(data.get("max_positions", 10)),
            parameters=dict(data.get("parameters", {})),
        )


@dataclass
class MetricDefinition:
    """
    Definition of a single metric tracked in an experiment.

    Attributes:
        name: Metric name (e.g., "sharpe_ratio", "max_drawdown").
        description: Human-readable description.
        higher_is_better: Whether higher values indicate better performance.
        target: Optional target value for validation.
        tolerance: Acceptable deviation from target (for validation).
    """

    name: str
    description: str = ""
    higher_is_better: bool = True
    target: Optional[float] = None
    tolerance: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "higher_is_better": self.higher_is_better,
            "target": self.target,
            "tolerance": self.tolerance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricDefinition":
        """Deserialize from a dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            higher_is_better=bool(data.get("higher_is_better", True)),
            target=data.get("target"),
            tolerance=data.get("tolerance"),
        )

