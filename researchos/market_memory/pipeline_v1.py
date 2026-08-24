"""
Market Memory Pipeline — end-to-end market memory research pipeline.

Pipeline stages:
  1. Load data
  2. Extract events
  3. Compute outcomes
  4. Conditional analysis
  5. Bootstrap uncertainty
  6. Temporal validation
  7. Self-audit
  8. Evidence generation
  9. Report generation
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from researchos.market_memory.bootstrap import bootstrap_mean_ci
from researchos.market_memory.conditioning import (
    ConditionSpec,
    MultipleTestingAudit,
    compute_conditional_statistics,
    filter_events,
)
from researchos.market_memory.evidence import create_evidence_record
from researchos.market_memory.event_extractor import extract_sma_crossover_events
from researchos.market_memory.event_schema import (
    ConditionalResult,
    EvidenceRecord,
    EvidenceStatus,
    EventType,
    MarketEvent,
    MarketMemoryReport,
    SelfAuditResult,
    ValidationResult,
)
from researchos.market_memory.outcome_engine import compute_forward_outcomes
from researchos.market_memory.self_audit import run_self_audit
from researchos.market_memory.temporal_validation import (
    chronological_split,
    expanding_window_splits,
)


def _compute_dataset_hash(file_path: str) -> str:
    """Compute SHA256 hash of dataset file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_market_memory_pipeline(
    data_path: str = "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv",
    asset: str = "XAUUSD",
    timeframe: str = "D1",
    fast_period: int = 20,
    slow_period: int = 100,
    seed: int = 42,
    conditions: list[ConditionSpec] | None = None,
) -> MarketMemoryReport:
    """
    Run the complete market memory pipeline.

    Args:
        data_path: Path to CSV data file
        asset: Asset symbol
        timeframe: Timeframe
        fast_period: Fast SMA period
        slow_period: Slow SMA period
        seed: Random seed
        conditions: List of condition specifications to test

    Returns:
        MarketMemoryReport with all results
    """
    # 1. Load data
    from researchos.market_memory.event_extractor import load_xauusd_d1

    df = load_xauusd_d1(data_path)
    dataset_hash = _compute_dataset_hash(data_path)
    dataset_id = f"{asset}_{timeframe}_{dataset_hash}"

    # 2. Extract events
    events = extract_sma_crossover_events(
        df,
        fast_period=fast_period,
        slow_period=slow_period,
        dataset_source=dataset_id,
        seed=seed,
    )

    # 3. Compute outcomes
    price_df = df.select(["timestamp", "open", "high", "low", "close"])
    events = compute_forward_outcomes(events, price_df)

    # 4. Conditional analysis
    if conditions is None:
        conditions = [
            ConditionSpec(
                name="all_crossovers",
                conditions={},
                description="All SMA crossovers",
            ),
            ConditionSpec(
                name="bullish_crossover",
                conditions={"direction": "bullish"},
                description="Bullish SMA crossovers only",
            ),
            ConditionSpec(
                name="bearish_crossover",
                conditions={"direction": "bearish"},
                description="Bearish SMA crossovers only",
            ),
            ConditionSpec(
                name="low_volatility",
                conditions={"volatility_state": "Low"},
                description="Crossovers in low volatility regime",
            ),
            ConditionSpec(
                name="high_volatility",
                conditions={"volatility_state": "High"},
                description="Crossovers in high volatility regime",
            ),
        ]

    conditional_results = []
    for spec in conditions:
        result = compute_conditional_statistics(
            events, spec, outcome_field="return_1d", bootstrap_seed=seed
        )
        conditional_results.append(result)

    # 5. Bootstrap for key conditions
    bootstrap_results = {}
    for cr in conditional_results:
        if cr.sample_size >= 5:
            matched = filter_events(events, cr.condition_spec)
            returns_1d = [
                e.outcome.return_1d
                for e in matched
                if e.outcome and e.outcome.return_1d is not None
            ]
            if returns_1d:
                bootstrap_results[cr.condition_name] = bootstrap_mean_ci(
                    returns_1d, seed=seed
                )

    # 6. Temporal validation
    train_events, val_events, test_events = chronological_split(events)
    temporal_integrity = chronological_split(events)  # Just to get the check

    validation_results = []
    for cr in conditional_results:
        train_matched = filter_events(train_events, cr.condition_spec)
        test_matched = filter_events(test_events, cr.condition_spec)

        train_returns = [
            e.outcome.return_1d
            for e in train_matched
            if e.outcome and e.outcome.return_1d is not None
        ]
        test_returns = [
            e.outcome.return_1d
            for e in test_matched
            if e.outcome and e.outcome.return_1d is not None
        ]

        train_mean = sum(train_returns) / len(train_returns) if train_returns else 0.0
        test_mean = sum(test_returns) / len(test_returns) if test_returns else 0.0

        validation_results.append(
            ValidationResult(
                condition_name=cr.condition_name,
                train_period=(
                    train_events[0].timestamp.isoformat() if train_events else "",
                    train_events[-1].timestamp.isoformat() if train_events else "",
                ),
                validation_period=(
                    val_events[0].timestamp.isoformat() if val_events else "",
                    val_events[-1].timestamp.isoformat() if val_events else "",
                ),
                test_period=(
                    test_events[0].timestamp.isoformat() if test_events else "",
                    test_events[-1].timestamp.isoformat() if test_events else "",
                ),
                train_events=len(train_matched),
                validation_events=len(val_events),
                test_events=len(test_matched),
                train_statistic=train_mean,
                validation_statistic=0.0,
                test_statistic=test_mean,
                is_stable=abs(train_mean - test_mean) < 0.05 if train_returns and test_returns else False,
                validation_method="chronological_split",
            )
        )

    # 7. Self-audit
    audit = run_self_audit(events, conditional_results)

    # 8. Evidence records
    evidence_records = []
    for cr in conditional_results:
        ev = create_evidence_record(
            finding_name=f"SMA Crossover {cr.condition_name}",
            dataset_id=dataset_id,
            dataset_version=dataset_hash,
            event_definition=f"SMA{fast_period}/{slow_period} crossover on {asset} {timeframe}",
            condition_definition=cr.condition_spec.to_dict()["conditions"],
            sample_size=cr.sample_size,
            time_range=(
                events[0].timestamp.isoformat() if events else "",
                events[-1].timestamp.isoformat() if events else "",
            ),
            computation_method="forward_return_analysis",
            code_module="researchos.market_memory.pipeline",
            statistical_method="empirical_probability_with_bootstrap_ci",
            result={
                "raw_probability": cr.raw_probability,
                "mean_return": cr.mean_return,
                "std_return": cr.std_return,
            },
            uncertainty=(
                {"confidence_interval": cr.confidence_interval}
                if cr.confidence_interval
                else {}
            ),
            validation_method="chronological_train_test_split",
            random_seed=seed,
            status=cr.status,
        )
        evidence_records.append(ev)

    # 9. Multiple testing audit
    multiple_testing = MultipleTestingAudit(
        total_hypotheses_tested=len(conditions),
        conditions_tested=[c.name for c in conditions],
        selection_process="Pre-specified based on domain knowledge (regime, direction, volatility)",
        correction_applied="None (explanatory only; do not use for inference without correction)",
        limitations="Multiple conditions increase false positive risk; Bonferroni or FDR correction required for inference",
    )

    # 10. Overall status
    if audit.overall_status == "FAIL":
        overall_status = EvidenceStatus.REJECTED.value
    elif audit.overall_status == "WARNING":
        overall_status = EvidenceStatus.INCONCLUSIVE.value
    elif all(cr.status == EvidenceStatus.VALIDATED.value for cr in conditional_results):
        overall_status = EvidenceStatus.VALIDATED.value
    else:
        overall_status = EvidenceStatus.UNVALIDATED.value

    # 11. Build report
    report = MarketMemoryReport(
        report_id=f"MMR|{asset}|{timeframe}|SMA{fast_period}_{slow_period}|{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        asset=asset,
        timeframe=timeframe,
        event_type=EventType.SMA_CROSSOVER.value,
        total_events=len(events),
        date_range=(
            events[0].timestamp.isoformat() if events else "",
            events[-1].timestamp.isoformat() if events else "",
        ),
        outcomes={
            "total_events": len(events),
            "bullish_count": sum(1 for e in events if e.direction == "bullish"),
            "bearish_count": sum(1 for e in events if e.direction == "bearish"),
            "avg_return_1d": (
                sum(e.outcome.return_1d for e in events if e.outcome and e.outcome.return_1d is not None)
                / len([e for e in events if e.outcome and e.outcome.return_1d is not None])
                if any(e.outcome and e.outcome.return_1d is not None for e in events)
                else 0.0
            ),
        },
        conditional_results=conditional_results,
        validation_results=validation_results,
        evidence_records=evidence_records,
        self_audit=audit,
        overall_status=overall_status,
        notes=f"Dataset hash: {dataset_hash}. Multiple testing audit: {multiple_testing.to_dict()}",
    )

    return report
