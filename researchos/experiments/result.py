"""
ExperimentRun and ExperimentResult — the outputs of experiment execution.

Purpose:
    ExperimentRun captures a single execution of an Experiment with all
    parameters and context. ExperimentResult stores the actual metrics
    and outcomes produced by the run.

Based on Article XVII: Object Model — Experiment Layer.

Guarantees:
    - Deterministic: Same run inputs → same run hash and result hash
    - Auditable: Full lifecycle from Pending to Completed/Failed
    - Repeatable: All parameters and context captured for re-execution
"""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.experiments.contracts import (
    DatasetConfig,
    ExperimentStatus,
    SimulationConfig,
)


def _freeze_mapping(data: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Return a read-only mapping view of ``data`` (or empty mapping)."""
    return MappingProxyType(dict(data) if data else {})


class ExperimentRun(BaseObject):
    """
    A single execution of an Experiment.

    Captures the complete context needed to reproduce the run:
    the experiment definition snapshot, parameters used, timing,
    and a link to the resulting metrics.

    Attributes:
        experiment_id: Link to the Experiment definition.
        run_number: Sequential run number within the experiment.
        dataset_config: Snapshot of the dataset config used for this run.
        simulation_config: Snapshot of the sim config used for this run.
        parameters: Parameters used for this specific run (overrides).
        result_id: Link to the ExperimentResult.
        started_at: When the run started.
        completed_at: When the run completed.
        duration_seconds: How long the run took.
        status: Run status (Pending, Running, Completed, Failed).
        run_hash: Deterministic hash of the run context.
        result_hash: Hash of the associated result (for integrity).
        trace: Human-readable trace of the run.
        tags: Tags for categorisation.
    """

    def __init__(
        self,
        experiment_id: str,
        run_number: int = 1,
        dataset_config: Optional[DatasetConfig] = None,
        simulation_config: Optional[SimulationConfig] = None,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ExperimentRun|{experiment_id}|{run_number}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.experiment_id = experiment_id
        self.run_number = run_number
        # Config snapshots (deep copies) decouple the recorded run from the
        # live experiment source config — later external mutation of the
        # source config must not affect this historical record (Issue #4).
        self.dataset_config = (dataset_config or DatasetConfig(source="")).snapshot()
        self.simulation_config = (simulation_config or SimulationConfig()).snapshot()
        self.parameters: Mapping[str, Any] = _freeze_mapping(parameters)
        self.result_id: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.duration_seconds: float = 0.0
        self.status = ExperimentStatus.DRAFT
        self.run_hash: str = ""
        self.result_hash: str = ""
        self.trace: str = ""
        self.tags: List[str] = list(tags or [])

        self.lifecycle.transition(
            LifecycleStage.DRAFT,
            reason="Experiment run created",
        )

    def start(self) -> None:
        """Mark the run as started."""
        self.started_at = utc_now()
        self.status = ExperimentStatus.RUNNING
        self.lifecycle.transition(
            LifecycleStage.IN_PROGRESS,
            reason="Experiment run started",
        )

    def complete(
        self,
        result_id: str,
        result_hash: str = "",
        duration_seconds: float = 0.0,
        trace: str = "",
    ) -> None:
        """Mark the run as completed with a result.

        Determinism closure (W1): ``duration_seconds`` is part of the
        deterministic ``run_hash``.  ``run_hash`` must represent the logical
        identity of the run, not runtime performance.  When no explicit
        positive duration is supplied, we keep the deterministic ``0.0``
        default and NEVER derive ``duration_seconds`` from wall clock — doing
        so would leak execution timing into the hash and make two identical
        logical runs hash differently.  The observational ``completed_at``
        timestamp (and any real execution timing) remains telemetry outside
        the hash (it is not part of ``_to_hashable_dict``).
        """
        self.completed_at = utc_now()
        self.result_id = result_id
        self.result_hash = result_hash
        if duration_seconds > 0:
            self.duration_seconds = duration_seconds
        else:
            # No explicit positive duration → deterministic 0.0.  Never derive
            # from wall clock (would make run_hash nondeterministic).
            self.duration_seconds = 0.0
        self.trace = trace
        self.status = ExperimentStatus.COMPLETED
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Experiment run completed: {duration_seconds:.2f}s",
        )

    def fail(self, reason: str = "") -> None:
        """Mark the run as failed."""
        self.completed_at = utc_now()
        self.status = ExperimentStatus.FAILED
        self.trace = reason
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.INVALIDATED,
            reason=f"Experiment run failed: {reason}" if reason else "Experiment run failed",
        )

    def _update_hash(self) -> None:
        """Compute the deterministic hash of this run."""
        content = self._to_hashable_dict()
        self.run_hash = deterministic_hash(content)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "run_number": self.run_number,
            "dataset_config": self.dataset_config.to_dict(),
            "simulation_config": self.simulation_config.to_dict(),
            "parameters": dict(sorted(self.parameters.items())) if self.parameters else {},
            "result_id": self.result_id or "",
            "result_hash": self.result_hash,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "trace": self.trace,
            "tags": sorted(self.tags),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "experiment_id": self.experiment_id,
            "run_number": self.run_number,
            "dataset_config": self.dataset_config.to_dict(),
            "simulation_config": self.simulation_config.to_dict(),
            "parameters": dict(self.parameters),
            "result_id": self.result_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "run_hash": self.run_hash,
            "result_hash": self.result_hash,
            "trace": self.trace,
            "tags": self.tags,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentRun":
        obj = super().from_dict(data)
        obj.experiment_id = data["experiment_id"]
        obj.run_number = int(data.get("run_number", 1))
        obj.dataset_config = DatasetConfig.from_dict(
            data.get("dataset_config", {"source": ""})
        )
        obj.simulation_config = SimulationConfig.from_dict(
            data.get("simulation_config", {})
        )
        obj.parameters = _freeze_mapping(data.get("parameters", {}))
        obj.result_id = data.get("result_id")
        obj.started_at = parse_timestamp(data["started_at"]) if data.get("started_at") else None
        obj.completed_at = parse_timestamp(data["completed_at"]) if data.get("completed_at") else None
        obj.duration_seconds = float(data.get("duration_seconds", 0.0))
        obj.status = ExperimentStatus(data.get("status", "Draft"))
        obj.run_hash = data.get("run_hash", "")
        obj.result_hash = data.get("result_hash", "")
        obj.trace = data.get("trace", "")
        obj.tags = list(data.get("tags", []))
        return obj


class ExperimentResult(BaseObject):
    """
    The metrics and outcomes produced by a single ExperimentRun.

    This is the output container — it stores all computed metrics,
    performance statistics, and any other data produced by the run.

    The ``metrics``, ``statistics``, ``performance`` and ``metadata``
    containers are read-only mapping views (``MappingProxyType``).  They are
    mutated only through the provided ``add_metric`` / ``add_statistic`` /
    ``set_metadata_item`` methods, which swap in a new read-only view and
    recompute the deterministic ``result_hash``.  This prevents post-hoc
    mutation leaking into the certified research record (Issue #3).

    Integrity verification (Issue B): ``from_dict`` recomputes the canonical
    ``result_hash`` from the deserialized content and raises ``ValueError`` if
    the recomputed hash does not match a stored non-empty hash.  Legacy
    payloads without a stored hash are recomputed and accepted (backward
    compatible).  ``verify_result_hash()`` exposes the same check live.

    Attributes:
        run_id: Link to the ExperimentRun that produced this result.
        metrics: Read-only mapping of metric names to computed values.
        statistics: Read-only mapping of statistical summaries.
        performance: Read-only mapping of performance metrics.
        signals: List of signal snapshots (if applicable).
        trades: List of trade records (if applicable).
        equity_curve: List of equity values over time (if applicable).
        metadata: Read-only mapping of additional result metadata.
        result_hash: Deterministic hash of the result content.
        trace: Human-readable trace of the result computation.
    """

    def __init__(
        self,
        run_id: str,
        metrics: Optional[Dict[str, float]] = None,
        statistics: Optional[Dict[str, Any]] = None,
        performance: Optional[Dict[str, Any]] = None,
        signals: Optional[List[Dict[str, Any]]] = None,
        trades: Optional[List[Dict[str, Any]]] = None,
        equity_curve: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ExperimentResult|{run_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.run_id = run_id
        self.metrics: Mapping[str, float] = _freeze_mapping(metrics)
        self.statistics: Mapping[str, Any] = _freeze_mapping(statistics)
        self.performance: Mapping[str, Any] = _freeze_mapping(performance)
        self.signals: List[Dict[str, Any]] = list(signals or [])
        self.trades: List[Dict[str, Any]] = list(trades or [])
        self.equity_curve: List[float] = list(equity_curve or [])
        self.metadata: Mapping[str, Any] = _freeze_mapping(metadata)
        self.result_hash: str = ""
        self.trace = trace
        # Observational backend execution telemetry (Phase 4.4). These are
        # intentionally NOT part of the deterministic ``result_hash``.
        self.backend_execution_time_ms: float = 0.0
        self.backend_execution_timestamp: Optional[str] = None

        self._update_hash()

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason="Experiment result computed",
        )

    def add_metric(self, name: str, value: float) -> None:
        """Add a single metric value (swaps in a new read-only view)."""
        new = dict(self.metrics)
        new[name] = value
        self.metrics = _freeze_mapping(new)
        self._update_hash()

    def add_statistic(self, name: str, value: Any) -> None:
        """Add a single statistic (swaps in a new read-only view)."""
        new = dict(self.statistics)
        new[name] = value
        self.statistics = _freeze_mapping(new)
        self._update_hash()

    def set_metadata_item(self, name: str, value: Any) -> None:
        """Set a single metadata item (swaps in a new read-only view)."""
        new = dict(self.metadata)
        new[name] = value
        self.metadata = _freeze_mapping(new)
        self._update_hash()

    def _update_hash(self) -> None:
        """Compute the deterministic hash of this result."""
        content = self._to_hashable_dict()
        self.result_hash = deterministic_hash(content)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "metrics": dict(sorted(self.metrics.items())) if self.metrics else {},
            "statistics": dict(sorted(self.statistics.items())) if self.statistics else {},
            "performance": dict(sorted(self.performance.items())) if self.performance else {},
            "metadata": dict(sorted(self.metadata.items())) if self.metadata else {},
            "trace": self.trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def verify_result_hash(self) -> bool:
        """Return True if the stored ``result_hash`` matches the canonical
        recomputation of the current content.

        A result with an empty ``result_hash`` is considered to have no
        stored signature; this method still verifies the content is
        internally consistent by recomputing (and returns True, matching the
        legacy/empty-hash convention).
        """
        canonical = deterministic_hash(self._to_hashable_dict())
        if not self.result_hash:
            return True
        return canonical == self.result_hash

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "run_id": self.run_id,
            "metrics": dict(self.metrics),
            "statistics": dict(self.statistics),
            "performance": dict(self.performance),
            "signals": self.signals,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "metadata": dict(self.metadata),
            "result_hash": self.result_hash,
            "trace": self.trace,
            "backend_execution_time_ms": self.backend_execution_time_ms,
            "backend_execution_timestamp": self.backend_execution_timestamp,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        obj = super().from_dict(data)
        obj.run_id = data["run_id"]
        obj.metrics = _freeze_mapping(data.get("metrics", {}))
        obj.statistics = _freeze_mapping(data.get("statistics", {}))
        obj.performance = _freeze_mapping(data.get("performance", {}))
        obj.signals = list(data.get("signals", []))
        obj.trades = list(data.get("trades", []))
        obj.equity_curve = list(data.get("equity_curve", []))
        obj.metadata = _freeze_mapping(data.get("metadata", {}))
        stored_hash = data.get("result_hash", "")
        obj.result_hash = stored_hash
        obj.trace = data.get("trace", "")
        obj.backend_execution_time_ms = float(data.get("backend_execution_time_ms", 0.0))
        obj.backend_execution_timestamp = data.get("backend_execution_timestamp")

        # Integrity verification (Issue B): recompute the canonical hash from
        # the deserialized content.  If a stored non-empty hash exists and it
        # does not match, the payload has been tampered with or corrupted.
        canonical = deterministic_hash(obj._to_hashable_dict())
        if stored_hash and stored_hash != canonical:
            raise ValueError(
                f"ExperimentResult hash mismatch: stored={stored_hash} "
                f"computed={canonical}"
            )
        if not stored_hash:
            # Legacy payload without a stored hash → recompute deterministically.
            obj.result_hash = canonical
        return obj
