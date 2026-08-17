"""
Quant Research Experiment Framework — test hypotheses against historical data.

Purpose:
    Allow TRADER-OS to test hypotheses against historical data with full
    determinism, auditability, and repeatability guarantees.

Workflow:
    Research Question
            ↓
    QuantHypothesis
            ↓
    Experiment
            ↓
    ExperimentRun
            ↓
    ExperimentResult
            ↓
    ExperimentValidation
            ↓
    LearningRecord

Design Principles:
    - Deterministic: Same inputs → same outputs (seeded RNG, content-addressed IDs)
    - Auditable: Full lifecycle tracking, all state transitions recorded
    - Repeatable: Complete parameter capture enables exact re-execution
    - Serializable: All objects support to_dict/from_dict for storage and transport
    - C++ Ready: Computation interfaces are abstract; future C++ Quant Engine
      can replace the backend without changing experiment objects.

Based on Article XVII: Object Model — Experiment Layer.
"""

from researchos.experiments.contracts import (
    DatasetConfig,
    ExperimentStatus,
    ExperimentType,
    HypothesisStatus,
    MetricDefinition,
    SimulationConfig,
    ValidationStatus,
)
from researchos.experiments.experiment import Experiment
from researchos.experiments.hypothesis import QuantHypothesis
from researchos.experiments.learning import LearningRecord
from researchos.experiments.reports import ExperimentReport
from researchos.experiments.result import ExperimentResult, ExperimentRun
from researchos.experiments.runner import AbstractExperimentRunner, BaseExperimentRunner, get_runner
from researchos.experiments.validation import ExperimentValidation

__all__ = [
    # Enums / Configs
    "ExperimentStatus",
    "ExperimentType",
    "HypothesisStatus",
    "ValidationStatus",
    "DatasetConfig",
    "SimulationConfig",
    "MetricDefinition",
    # Core objects
    "QuantHypothesis",
    "Experiment",
    "ExperimentRun",
    "ExperimentResult",
    "BaseExperimentRunner",
    "AbstractExperimentRunner",
    "get_runner",
    "ExperimentValidation",
    "LearningRecord",
    "ExperimentReport",
]
