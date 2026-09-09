"""Explicit contract for real-XAUUSD M1 forward outcomes."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class M1OutcomeContract:
    """Immutable label definition used by the real M1 research pipeline.

    ``horizon_days`` is a calendar-time target, while the realized endpoint is
    selected from the first available market observation at or after that
    target. The Outcome Engine records that actual endpoint for auditability.
    """

    horizon_days: int = 1
    threshold_return: float = 0.0
    price_field: str = "close"
    direction_aware: bool = True

    def __post_init__(self) -> None:
        if self.horizon_days < 1:
            raise ValueError("horizon_days must be positive")
        if self.threshold_return < 0.0:
            raise ValueError("threshold_return must be non-negative")
        if self.price_field != "close":
            raise ValueError("M1OutcomeContract currently requires close prices")
        if not self.direction_aware:
            raise ValueError("M1 outcomes must use direction-aware semantics")

    @property
    def label_name(self) -> str:
        return f"hit_threshold_{self.horizon_days}d"
