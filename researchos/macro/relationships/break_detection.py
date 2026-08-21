"""
ResearchOS Macro Intelligence Layer - Structural Break Detection

Detects changes in correlation structure over time.
Pure, deterministic, stateless.
"""

from __future__ import annotations

from researchos.macro.relationships.correlation import pearson_correlation
from researchos.macro.relationships.models import (
    ALGORITHM_VERSION,
    BreakType,
    StructuralBreak,
)


def detect_structural_breaks(
    series_a: list[float],
    series_b: list[float],
    break_threshold: float = 0.3,
    min_segment_size: int = 10,
) -> list[StructuralBreak]:
    """
    Detect structural breaks in the relationship between two series.

    Scans for points where the correlation changes significantly
    between pre- and post-break segments.

    Args:
        series_a: Values for series A
        series_b: Values for series B
        break_threshold: Minimum absolute change in correlation to flag a break
        min_segment_size: Minimum observations per segment

    Returns:
        List of StructuralBreak detected
    """
    n = len(series_a)
    if n < min_segment_size * 2:
        return []

    breaks = []
    overall_corr = pearson_correlation(series_a, series_b)
    if overall_corr is None:
        return []

    # Scan potential break points
    for breakpoint in range(min_segment_size, n - min_segment_size):
        pre_a = series_a[:breakpoint]
        pre_b = series_b[:breakpoint]
        post_a = series_a[breakpoint:]
        post_b = series_b[breakpoint:]

        corr_before = pearson_correlation(pre_a, pre_b)
        corr_after = pearson_correlation(post_a, post_b)

        if corr_before is None or corr_after is None:
            continue

        corr_change = abs(corr_after - corr_before)

        if corr_change >= break_threshold:
            # Determine break type
            break_type = _classify_break(corr_before, corr_after)

            # Compute confidence based on segment sizes and correlation change
            confidence = min(1.0, corr_change / break_threshold * 0.5 + 0.3)

            breaks.append(
                StructuralBreak(
                    series_a="",
                    series_b="",
                    break_point=str(breakpoint),
                    break_type=break_type,
                    correlation_before=corr_before,
                    correlation_after=corr_after,
                    confidence=round(confidence, 4),
                    algorithm_version=ALGORITHM_VERSION,
                )
            )

    # Deduplicate: keep only the most significant break in each cluster
    breaks = _deduplicate_breaks(breaks, min_gap=min_segment_size)

    return breaks


def _classify_break(corr_before: float, corr_after: float) -> str:
    """Classify the type of structural break."""
    # Direction change: sign flips between the two segments.
    if corr_before * corr_after < 0:
        return BreakType.DIRECTION_CHANGE.value

    # Strength change: magnitude of correlation differs between segments.
    return BreakType.STRENGTH_CHANGE.value


def _deduplicate_breaks(breaks: list[StructuralBreak], min_gap: int) -> list[StructuralBreak]:
    """Keep only the most significant break in each cluster."""
    if not breaks:
        return []

    result = []
    i = 0
    while i < len(breaks):
        cluster = [breaks[i]]
        j = i + 1
        while j < len(breaks) and int(breaks[j].break_point) - int(breaks[i].break_point) < min_gap:
            cluster.append(breaks[j])
            j += 1

        # Keep the break with highest confidence
        best = max(cluster, key=lambda b: b.confidence)
        result.append(best)
        i = j

    return result


def compare_correlation_windows(
    series_a: list[float],
    series_b: list[float],
    window1_end: int,
    window2_start: int,
) -> tuple[float | None, float | None, str | None]:
    """
    Compare correlation in two windows.

    Returns:
        (correlation_before, correlation_after, break_type_or_None)
    """
    n = len(series_a)
    if window1_end >= n or window2_start >= n or window1_end <= 0 or window2_start <= 0:
        return None, None, None

    pre_a = series_a[:window1_end]
    pre_b = series_b[:window1_end]
    post_a = series_a[window2_start:]
    post_b = series_b[window2_start:]

    corr_before = pearson_correlation(pre_a, pre_b)
    corr_after = pearson_correlation(post_a, post_b)

    if corr_before is None or corr_after is None:
        return corr_before, corr_after, None

    if corr_before * corr_after < 0:
        break_type = BreakType.DIRECTION_CHANGE.value
    else:
        break_type = BreakType.STRENGTH_CHANGE.value

    return corr_before, corr_after, break_type
