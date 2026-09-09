"""Strict Market Memory execution with canonical dataset provenance binding.

This module keeps the existing statistical pipeline unchanged while enforcing
strict dataset identity at the evidence publication boundary.
"""

from __future__ import annotations

import hashlib
from typing import Any

from researchos.data_engine.candle import Candle
from researchos.data_engine.dataset import HistoricalDataset
from researchos.market_memory.evidence import create_evidence_record
from researchos.market_memory.event_schema import EvidenceRecord, MarketMemoryReport
from researchos.market_memory.pipeline_v1 import run_market_memory_pipeline
from researchos.research_identity import DatasetIdentity


def _file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_dataset_identity(
    df: Any,
    *,
    data_path: str,
    asset: str,
    timeframe: str,
) -> DatasetIdentity:
    """Build canonical record/content and metadata hashes from validated D1 data."""
    candles: list[Candle] = []
    for row in df.iter_rows(named=True):
        candles.append(
            Candle(
                symbol=asset,
                timeframe=timeframe,
                timestamp=row["timestamp"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0) or 0.0),
                spread=(float(row["spread"]) if row.get("spread") is not None else None),
                tick_volume=(float(row["tick_volume"]) if row.get("tick_volume") is not None else None),
                real_volume=(float(row["real_volume"]) if row.get("real_volume") is not None else None),
            )
        )

    dataset = HistoricalDataset(
        symbol=asset,
        timeframe=timeframe,
        data_type="candle",
        records=candles,
        source="MT5",
        quality="Validated",
        version="1.0.0",
    )
    dataset.mark_ready()
    dataset.mark_validated()

    # The dataset_id remains tied to the exact source artifact used by the
    # legacy Market Memory event provenance, while the two canonical hashes
    # come from normalized typed records rather than raw CSV bytes.
    dataset_id = f"{asset}_{timeframe}_{_file_sha256(data_path)}"
    return DatasetIdentity(
        dataset_id=dataset_id,
        dataset_content_hash=dataset.dataset_content_hash,
        dataset_hash=dataset.dataset_hash,
    )


def _strict_record(record: EvidenceRecord, identity: DatasetIdentity) -> EvidenceRecord:
    """Re-emit an existing finding through the strict evidence constructor."""
    uncertainty = dict(record.uncertainty)
    uncertainty.pop("provenance", None)
    return create_evidence_record(
        finding_name=record.finding_name,
        dataset_id=record.dataset_id,
        dataset_version=identity.dataset_hash,
        event_definition=record.event_definition,
        condition_definition=record.condition_definition,
        sample_size=record.sample_size,
        time_range=record.time_range,
        computation_method=record.computation_method,
        code_module=record.code_module,
        statistical_method=record.statistical_method,
        result=dict(record.result),
        uncertainty=uncertainty,
        validation_method=record.validation_method,
        random_seed=record.random_seed,
        status=record.status,
        dataset_identity=identity,
        dataset_content_hash=identity.dataset_content_hash,
        dataset_hash=identity.dataset_hash,
    )


def run_strict_market_memory_pipeline(
    data_path: str,
    *,
    asset: str = "XAUUSD",
    timeframe: str = "D1",
    fast_period: int = 20,
    slow_period: int = 100,
    seed: int = 42,
    minimum_events: int = 100,
) -> MarketMemoryReport:
    """Run Market Memory and return evidence strictly bound to dataset identity."""
    from researchos.market_memory.event_extractor import load_xauusd_d1

    df = load_xauusd_d1(data_path)
    identity = _build_dataset_identity(
        df,
        data_path=data_path,
        asset=asset,
        timeframe=timeframe,
    )
    report = run_market_memory_pipeline(
        data_path=data_path,
        asset=asset,
        timeframe=timeframe,
        fast_period=fast_period,
        slow_period=slow_period,
        seed=seed,
        enforce_production_gate=True,
        minimum_events=minimum_events,
    )
    if not report.evidence_records:
        return report

    strict_records = [_strict_record(record, identity) for record in report.evidence_records]
    return MarketMemoryReport(
        report_id=report.report_id,
        asset=report.asset,
        timeframe=report.timeframe,
        event_type=report.event_type,
        generated_at=report.generated_at,
        total_events=report.total_events,
        date_range=report.date_range,
        outcomes=report.outcomes,
        conditional_results=report.conditional_results,
        validation_results=report.validation_results,
        evidence_records=strict_records,
        self_audit=report.self_audit,
        overall_status=report.overall_status,
        notes=report.notes + f" Strict dataset identity bound: {identity.to_dict()}",
    )


__all__ = ["run_strict_market_memory_pipeline"]
