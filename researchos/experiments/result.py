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
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.experiments.contracts import (
    DatasetConfig,
    ExperimentStatus,
    SimulationConfig,
)


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
        self.dataset_config = dataset_config or DatasetConfig(source="")
        self.simulation_config = simulation_config or SimulationConfig()
        self.parameters: Dict[str, Any] = parameters or {}
        self.result_id: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.duration_seconds: float = 0.0
        self.status = ExperimentStatus.DRAFT
        self.run_hash: str = ""
        self.result_hash: str = ""
        self.trace: str = ""
        self.tags: List[str] = tags or []

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
        """Mark the run as completed with a result."""
        self.completed_at = utc_now()
        self.result_id = result_id
        self.result_hash = result_hash
        self.duration_seconds = duration_seconds if duration_seconds > 0 else (
            self.completed_at - (self.started_at or utc_now())
        ).total_seconds()
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
            "parameters": self.parameters,
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
        obj.parameters = dict(data.get("parameters", {}))
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

    Attributes:
        run_id: Link to the ExperimentRun that produced this result.
        metrics: Dict of metric names to computed values.
        statistics: Dict of statistical summaries.
        performance: Dict of performance metrics.
        signals: List of signal snapshots (if applicable).
        trades: List of trade records (if applicable).
        equity_curve: List of equity values over time (if applicable).
        metadata: Additional result metadata.
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
        self.metrics: Dict[str, float] = metrics or {}
        self.statistics: Dict[str, Any] = statistics or {}
        self.performance: Dict[str, Any] = performance or {}
        self.signals: List[Dict[str, Any]] = signals or []
        self.trades: List[Dict[str, Any]] = trades or []
        self.equity_curve: List[float] = equity_curve or []
        self.metadata: Dict[str, Any] = metadata or {}
        self.result_hash: str = ""
        self.trace = trace

        self._update_hash()

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason="Experiment result computed",
        )

    def add_metric(self, name: str, value: float) -> None:
        """Add a single metric value."""
        self.metrics[name] = value
        self._update_hash()

    def add_statistic(self, name: str, value: Any) -> None:
        """Add a single statistic."""
        self.statistics[name] = value
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

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "run_id": self.run_id,
            "metrics": self.metrics,
            "statistics": self.statistics,
            "performance": self.performance,
            "signals": self.signals,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "metadata": self.metadata,
            "result_hash": self.result_hash,
            "trace": self.trace,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        obj = super().from_dict(data)
        obj.run_id = data["run_id"]
        obj.metrics = dict(data.get("metrics", {}))
        obj.statistics = dict(data.get("statistics", {}))
        obj.performance = dict(data.get("performance", {}))
        obj.signals = list(data.get("signals", []))
        obj.trades = list(data.get("trades", []))
        obj.equity_curve = list(data.get("equity_curve", []))
        obj.metadata = dict(data.get("metadata", {}))
        obj.result_hash = data.get("result_hash", "")
        obj.trace = data.get("trace", "")
        return obj
