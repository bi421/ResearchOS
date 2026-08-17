"""
Pipeline Repository Layer (Q15).

Persists the immutable ``PipelineReport`` objects produced by the
orchestration layer (Q14) using deterministic, stdlib-only JSON storage.

Public API:
    PipelineRepository     JSON-backed deterministic pipeline store
    PipelineRecord         immutable wrapper (report + storage metadata)
    PipelineRepositoryError       base error
    PipelineNotFoundError         missing pipeline id
    InvalidPipelineRecordError    malformed report/record/payload
"""

from .contracts import (
    PIPELINE_REPOSITORY_VERSION,
    InvalidPipelineRecordError,
    PipelineNotFoundError,
    PipelineRecord,
    PipelineRepositoryError,
)
from .repository import (
    DEFAULT_PATH,
    PipelineRepository,
)

__all__ = [
    "DEFAULT_PATH",
    "PIPELINE_REPOSITORY_VERSION",
    "InvalidPipelineRecordError",
    "PipelineNotFoundError",
    "PipelineRecord",
    "PipelineRepository",
    "PipelineRepositoryError",
]
