"""Production Market Memory execution path."""

from __future__ import annotations

from researchos.market_memory.event_schema import MarketMemoryReport
from researchos.market_memory.strict_pipeline import run_strict_market_memory_pipeline


def run_production_market_memory_pipeline(
    data_path: str,
    *,
    asset: str = "XAUUSD",
    timeframe: str = "D1",
    fast_period: int = 20,
    slow_period: int = 100,
    seed: int = 42,
    minimum_events: int = 100,
) -> MarketMemoryReport:
    """Run Market Memory with strict dataset provenance and fail-closed gating."""
    return run_strict_market_memory_pipeline(
        data_path=data_path,
        asset=asset,
        timeframe=timeframe,
        fast_period=fast_period,
        slow_period=slow_period,
        seed=seed,
        minimum_events=minimum_events,
    )


__all__ = ["run_production_market_memory_pipeline"]
