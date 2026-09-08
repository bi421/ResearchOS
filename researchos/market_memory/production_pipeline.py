"""Production Market Memory execution path.

The existing research pipeline remains useful for exploratory analysis. This
wrapper adds a hard evidence-publication gate so production execution cannot
return a publishable evidence set when prerequisites fail.
"""

from __future__ import annotations

from dataclasses import replace

from researchos.market_memory.event_schema import EvidenceStatus, MarketMemoryReport
from researchos.market_memory.pipeline_v1 import run_market_memory_pipeline


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
    """Run Market Memory and require production evidence prerequisites."""
    if minimum_events < 1:
        raise ValueError("minimum_events must be >= 1")

    report = run_market_memory_pipeline(
        data_path=data_path,
        asset=asset,
        timeframe=timeframe,
        fast_period=fast_period,
        slow_period=slow_period,
        seed=seed,
    )

    source = "synthetic" if any(
        token in data_path.lower() for token in ("synthetic", "demo", "mock", "fixture")
    ) else "real_file"

    if source == "synthetic":
        return replace(
            report,
            evidence_records=[],
            overall_status=EvidenceStatus.REJECTED.value,
            notes=(
                "PRODUCTION GATE FAILED: synthetic source is not eligible for evidence. "
                f"{report.notes}"
            ),
        )

    if len(report.evidence_records) == 0 or report.total_events < minimum_events:
        return replace(
            report,
            evidence_records=[],
            overall_status=EvidenceStatus.REJECTED.value,
            notes=(
                "PRODUCTION GATE FAILED: evidence prerequisites not met "
                f"(events={report.total_events}, minimum={minimum_events}). {report.notes}"
            ),
        )

    return report


__all__ = ["run_production_market_memory_pipeline"]
