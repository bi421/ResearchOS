"""Pipeline coordination for ResearchOS — connecting object lifecycle stages."""

from researchos.pipeline.pipeline import ResearchPipeline
from researchos.pipeline.references import ReferenceValidator

__all__ = [
    "ResearchPipeline",
    "ReferenceValidator",
]
