"""
Research Evaluation Engine (Q16).

Evaluates historical research runs stored by PipelineRepository,
providing deterministic reproducibility, stability, and evidence scores.
"""

from .contracts import (
    EVALUATION_VERSION,
    EvaluationError,
    EvaluationReport,
    EvaluationScore,
    InvalidEvaluationError,
    PipelineEvaluationError,
)
from .engine import ResearchEvaluator

__all__ = [
    "EVALUATION_VERSION",
    "EvaluationError",
    "EvaluationReport",
    "EvaluationScore",
    "InvalidEvaluationError",
    "PipelineEvaluationError",
    "ResearchEvaluator",
]
