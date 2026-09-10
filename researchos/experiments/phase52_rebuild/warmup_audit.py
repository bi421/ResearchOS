"""Audit whether historical context exists for leakage-safe feature warm-up.

Phase 5.2 currently requires 60 prior common daily observations to initialize
its frozen price feature set. Those observations are *context*, not research
samples. This module audits source calendar-day coverage before the research
period without changing the scientific dataset or filling missing data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WarmupCoverageAudit:
    """Deterministic audit of pre-research common-day warm-up coverage."""

    research_start_day: str
    warmup_rows_required: int
    earliest_xau_day: str | None
    earliest_dxy_day: str | None
    earliest_us10y_day: str | None
    earliest_vix_day: str | None
    common_days_before_research: int
    required_context_start_day: str | None
    context_available: bool
    status: str


def _validate_day(value: str) -> str:
    return date.fromisoformat(value).isoformat()


def audit_warmup_coverage(
    *,
    xau_days: set[str],
    dxy_days: set[str],
    us10y_days: set[str],
    vix_days: set[str],
    research_start_day: str,
    warmup_rows_required: int,
) -> WarmupCoverageAudit:
    """Determine whether enough pre-period four-way common days exist.

    No observations are modified, interpolated, or forward-filled. The audit
    only inspects calendar-day coverage and identifies the required context
    boundary.
    """
    start = _validate_day(research_start_day)
    if warmup_rows_required < 0:
        raise ValueError("warmup_rows_required must be non-negative")

    common_before = sorted(
        set(xau_days) & set(dxy_days) & set(us10y_days) & set(vix_days)
    )
    common_before = [day for day in common_before if day < start]
    available = len(common_before)
    context_available = available >= warmup_rows_required
    required_context_start = (
        common_before[-warmup_rows_required]
        if warmup_rows_required and context_available
        else None
    )
    return WarmupCoverageAudit(
        research_start_day=start,
        warmup_rows_required=warmup_rows_required,
        earliest_xau_day=min(xau_days) if xau_days else None,
        earliest_dxy_day=min(dxy_days) if dxy_days else None,
        earliest_us10y_day=min(us10y_days) if us10y_days else None,
        earliest_vix_day=min(vix_days) if vix_days else None,
        common_days_before_research=available,
        required_context_start_day=required_context_start,
        context_available=context_available,
        status="PASS" if context_available else "BLOCKED",
    )


__all__ = ["WarmupCoverageAudit", "audit_warmup_coverage"]
