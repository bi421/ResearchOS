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
    ExperimentLearningRecord
            ↓
    Evidence / Knowledge boundary
"""

from researchos.experiments.certified_runner import EvidenceAwareExperimentRunner
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
from researchos.experiments.learning import ExperimentLearningRecord, LearningRecord
from researchos.experiments.reports import ExperimentReport
from researchos.experiments.result import ExperimentResult, ExperimentRun
from researchos.experiments.runner import AbstractExperimentRunner, BaseExperimentRunner, get_runner
from researchos.experiments.validation import ExperimentValidation

__all__ = [
    "ExperimentStatus",
    "ExperimentType",
    "HypothesisStatus",
    "ValidationStatus",
    "DatasetConfig",
    "SimulationConfig",
    "MetricDefinition",
    "QuantHypothesis",
    "Experiment",
    "ExperimentRun",
    "ExperimentResult",
    "BaseExperimentRunner",
    "EvidenceAwareExperimentRunner",
    "AbstractExperimentRunner",
    "get_runner",
    "ExperimentValidation",
    "ExperimentLearningRecord",
    "LearningRecord",
    "ExperimentReport",
]
