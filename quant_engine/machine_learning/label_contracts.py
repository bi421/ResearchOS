"""
Label Generation Contracts.

Frozen dataclasses used across the Label Generation Engine.

This module is deliberately independent from FeatureBuilder, model training,
dataset construction, and the decision engine.  It only defines the data
shapes shared by the label generators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LabelResult:
    """A single supervised-learning label series.

    Attributes:
        name: Identifier for the label series (e.g. ``"future_return"``).
        values: Label values aligned with the input close-price series.
        metadata: Free-form metadata describing how the labels were produced.
        horizon: The forward horizon used to build the labels
            (``max_horizon`` for triple barrier).
        timestamps: Optional per-observation timestamps aligned with
            ``values``.
    """

    name: str
    values: List[Optional[float]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    horizon: Optional[int] = None
    timestamps: Optional[List[Any]] = None


__all__ = ["LabelResult"]
