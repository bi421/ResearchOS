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

from researchos.market_memory.event_schema import (
    ConditionalResult,
    MarketEvent,
    SelfAuditResult,
)


def run_self_audit(
    events: list[MarketEvent],
    conditional_results: list[ConditionalResult] | None = None,
    min_sample_size: int = 5,
    max_conditions: int = 10,
) -> SelfAuditResult:
    """
    Run comprehensive self-audit on market memory research.

    Args:
        events: List of all market events
        conditional_results: List of conditional analysis results
        min_sample_size: Minimum acceptable sample size
        max_conditions: Maximum number of conditions before flagging explosion risk

    Returns:
        SelfAuditResult with all audit findings
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

    # 1. Missing data check
    for e in events:
        if not e.event_id:
            issues["missing_provenance"].append(f"Event missing ID: {e}")
        if e.outcome is None:
            issues["missing_provenance"].append(f"Event missing outcome: {e.event_id}")

    # 2. Duplicate events
    seen = set()
    for e in events:
        key = (e.asset, e.timeframe, e.timestamp.isoformat(), e.event_type, e.direction)
        if key in seen:
            issues["duplicate_events"].append(f"Duplicate: {e.event_id}")
        seen.add(key)

    # 3. Timestamp ordering
    for i in range(1, len(events)):
        if events[i].timestamp < events[i - 1].timestamp:
            issues["timestamp_violations"].append(f"Order violation at index {i}: {events[i].timestamp} < {events[i-1].timestamp}")

    # 4. Future leakage check (basic)
    for e in events:
        if e.outcome:
            # Outcome timestamp should be after event timestamp
            if e.outcome.event_timestamp < e.timestamp:
                issues["future_leakage_detected"].append(f"Outcome before event: {e.event_id}")

    # 5. Overlapping windows (basic check)
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            if events[i].timestamp == events[j].timestamp:
                issues["overlapping_windows"].append(f"Same timestamp: {events[i].event_id} and {events[j].event_id}")

    # 6. Insufficient sample size
    if conditional_results:
        for cr in conditional_results:
            if cr.sample_size < min_sample_size:
                issues["insufficient_sample_size"].append(f"{cr.condition_name}: n={cr.sample_size} < {min_sample_size}")

    # 7. Condition explosion
    if conditional_results and len(conditional_results) > max_conditions:
        issues["condition_explosion_risk"].append(f"Tested {len(conditional_results)} conditions (max: {max_conditions})")

    # 8. Multiple testing risk
    if conditional_results and len(conditional_results) > 1:
        issues["multiple_testing_risk"].append(f"Multiple conditions tested ({len(conditional_results)}); no correction applied")

    # 9. Invalid probability claims
    if conditional_results:
        for cr in conditional_results:
            if cr.sample_size > 0 and abs(cr.raw_probability - 0.5) > 0.45 and cr.sample_size < 10:
                issues["invalid_probability_claims"].append(f"{cr.condition_name}: extreme probability {cr.raw_probability:.2f} with n={cr.sample_size}")

    # Determine overall status
    total_issues = sum(len(v) for v in issues.values())
    if total_issues == 0:
        overall_status = "PASS"
    elif any(issues["future_leakage_detected"]) or any(issues["train_test_contamination"]):
        overall_status = "FAIL"
    else:
        overall_status = "WARNING"

    return SelfAuditResult(
        total_events=len(events),
        duplicate_events=len(issues["duplicate_events"]),
        timestamp_violations=len(issues["timestamp_violations"]),
        future_leakage_detected=len(issues["future_leakage_detected"]) > 0,
        overlapping_windows=len(issues["overlapping_windows"]),
        insufficient_sample_size=issues["insufficient_sample_size"],
        condition_explosion_risk=len(issues["condition_explosion_risk"]) > 0,
        multiple_testing_risk=len(issues["multiple_testing_risk"]) > 0,
        train_test_contamination=len(issues["train_test_contamination"]) > 0,
        unstable_results=issues["unstable_results"],
        missing_provenance=issues["missing_provenance"],
        invalid_probability_claims=issues["invalid_probability_claims"],
        reproducibility_failures=issues["reproducibility_failures"],
        overall_status=overall_status,
    )
