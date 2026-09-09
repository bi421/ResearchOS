"""Frozen outcome contract for the first real XAUUSD M1 study."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class M1OutcomeContract:
    """Explicit, direction-aware forward-label definition."""

    horizon_days: int = 1
    threshold_return: float = 0.0
    price_field: str = "close"
    direction_aware: bool = True

    def __post_init__(self) -> None:
        if self.horizon_days < 1:
            raise ValueError("horizon_days must be >= 1")
        if self.threshold_return < 0:
            raise ValueError("threshold_return must be non-negative")
        if self.price_field != "close":
            raise ValueError("The frozen M1 contract uses close prices")
        if not self.direction_aware:
            raise ValueError("The frozen M1 contract requires direction-aware labels")

    @property
    def label_name(self) -> str:
        return f"hit_threshold_{self.horizon_days}d"
