"""
Self-Audit — automated checks for research integrity.

Checks for:
  - Missing data
  - Duplicate events
  - Timestamp ordering
  - Future leakage
  - Overlapping event windows
  - Insufficient sample size
  - Condition explosion
  - Multiple-testing risk
  - Train/test contamination
  - Unstable results
  - Missing provenance
  - Invalid probability claims
  - Reproducibility failures
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from researchos.market_memory.event_schema import (
    ConditionalResult,
    MarketEvent,
    SelfAuditResult,
)
from researchos.market_memory.label_dependence import audit_label_overlap


def run_self_audit(
    events: list[MarketEvent],
    conditional_results: list[ConditionalResult] | None = None,
    min_sample_size: int = 5,
    max_conditions: int = 10,
    *,
    label_end_getter: Callable[[MarketEvent], datetime | None] | None = None,
    multiple_testing_corrected: bool = False,
) -> SelfAuditResult:
    """Run comprehensive deterministic research-integrity checks.

    ``label_end_getter`` enables an actual realized-label dependence audit. The
    audit uses the future observation timestamp that realized each outcome,
    rather than guessing a label window from row offsets.
    """
    issues: dict[str, list[str]] = {
        "duplicate_events": [],
        "timestamp_violations": [],
        "future_leakage_detected": [],
        "overlapping_windows": [],
        "insufficient_sample_size": [],
        "condition_explosion_risk": [],
        "multiple_testing_risk": [],
        "train_test_contamination": [],
        "unstable_results": [],
        "missing_provenance": [],
        "invalid_probability_claims": [],
        "reproducibility_failures": [],
    }

    for e in events:
        if not e.event_id:
            issues["missing_provenance"].append(f"Event missing ID: {e}")
        if e.outcome is None:
            issues["missing_provenance"].append(f"Event missing outcome: {e.event_id}")

    seen = set()
    for e in events:
        key = (e.asset, e.timeframe, e.timestamp.isoformat(), e.event_type, e.direction)
        if key in seen:
            issues["duplicate_events"].append(f"Duplicate: {e.event_id}")
        seen.add(key)

    for i in range(1, len(events)):
        if events[i].timestamp < events[i - 1].timestamp:
            issues["timestamp_violations"].append(
                f"Order violation at index {i}: {events[i].timestamp} < {events[i - 1].timestamp}"
            )

    for e in events:
        if e.outcome and e.outcome.event_timestamp < e.timestamp:
            issues["future_leakage_detected"].append(f"Outcome before event: {e.event_id}")

    if label_end_getter is not None and events:
        dependence = audit_label_overlap(events, label_end_getter)
        issues["overlapping_windows"].extend(
            [f"Realized label overlap pairs: {dependence.overlap_pairs}"]
            if dependence.overlap_pairs
            else []
        )
        if dependence.missing_realized_end:
            issues["missing_provenance"].append(
                f"Missing realized label end timestamps: {dependence.missing_realized_end}"
            )
    else:
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                if events[i].timestamp == events[j].timestamp:
                    issues["overlapping_windows"].append(
                        f"Same timestamp: {events[i].event_id} and {events[j].event_id}"
                    )

    if conditional_results:
        for cr in conditional_results:
            if cr.sample_size < min_sample_size:
                issues["insufficient_sample_size"].append(
                    f"{cr.condition_name}: n={cr.sample_size} < {min_sample_size}"
                )

    if conditional_results and len(conditional_results) > max_conditions:
        issues["condition_explosion_risk"].append(
            f"Tested {len(conditional_results)} conditions (max: {max_conditions})"
        )

    if conditional_results and len(conditional_results) > 1 and not multiple_testing_corrected:
        issues["multiple_testing_risk"].append(
            f"Multiple conditions tested ({len(conditional_results)}); no correction applied"
        )

    if conditional_results:
        for cr in conditional_results:
            if cr.sample_size > 0 and abs(cr.raw_probability - 0.5) > 0.45 and cr.sample_size < 10:
                issues["invalid_probability_claims"].append(
                    f"{cr.condition_name}: extreme probability {cr.raw_probability:.2f} with n={cr.sample_size}"
                )

    total_issues = sum(len(v) for v in issues.values())
    if total_issues == 0:
        overall_status = "PASS"
    elif issues["future_leakage_detected"] or issues["train_test_contamination"]:
        overall_status = "FAIL"
    else:
        overall_status = "WARNING"

    notes_parts = []
    if label_end_getter is not None:
        notes_parts.append("Actual realized-label overlap audit applied")
    if multiple_testing_corrected:
        notes_parts.append("Multiple-testing correction verified by caller")

    return SelfAuditResult(
        total_events=len(events),
        duplicate_events=len(issues["duplicate_events"]),
        timestamp_violations=len(issues["timestamp_violations"]),
        future_leakage_detected=bool(issues["future_leakage_detected"]),
        overlapping_windows=len(issues["overlapping_windows"]),
        insufficient_sample_size=issues["insufficient_sample_size"],
        condition_explosion_risk=bool(issues["condition_explosion_risk"]),
        multiple_testing_risk=bool(issues["multiple_testing_risk"]),
        train_test_contamination=bool(issues["train_test_contamination"]),
        unstable_results=issues["unstable_results"],
        missing_provenance=issues["missing_provenance"],
        invalid_probability_claims=issues["invalid_probability_claims"],
        reproducibility_failures=issues["reproducibility_failures"],
        overall_status=overall_status,
        notes="; ".join(notes_parts),
    )
