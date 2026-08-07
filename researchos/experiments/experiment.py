"""
Experiment — the core definition for testing a hypothesis against historical data.

Purpose:
    An Experiment binds a QuantHypothesis to a specific dataset and simulation
    configuration, defining exactly what will be run, how it will be measured,
    and what parameters will be used. It is the blueprint for an experiment run.

Based on Article XVII: Object Model — Experiment Layer.

Guarantees:
    - Deterministic: Same hypothesis + config → same experiment ID
    - Auditable: Full lifecycle tracking from Draft to Archived
    - Repeatable: Complete parameter capture enables exact re-execution
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.experiments.contracts import (
    DatasetConfig,
    ExperimentStatus,
    MetricDefinition,
    SimulationConfig,
)


class Experiment(BaseObject):
    """
    Blueprint for testing a hypothesis against historical data.

    An Experiment defines:
        1. Which hypothesis to test
        2. What dataset to use
        3. How the simulation should run
        4. What metrics to track
        5. What parameters to vary

    Attributes:
        hypothesis_id: Link to the QuantHypothesis being tested.
        name: Human-readable name for this experiment.
        description: Detailed description of the experiment.
        experiment_type: The type of experiment (Backtest, WalkForward, etc.).
        dataset_config: Configuration for the dataset to use.
        simulation_config: Configuration for the simulation engine.
        metric_definitions: Metrics to track during the experiment.
        parameters: Additional experiment parameters.
        run_ids: IDs of all ExperimentRuns executed for this experiment.
        best_run_id: ID of the best-performing run (by primary metric).
        experiment_hash: Deterministic hash of the experiment definition.
        status: Current lifecycle status.
        version: Experiment version (for tracking changes).
        tags: Tags for categorisation.
        experiment_trace: How this experiment was constructed.
    """

    def __init__(
        self,
        hypothesis_id: str,
        name: str = "",
        description: str = "",
        experiment_type: str = "Backtest",
        dataset_config: Optional[DatasetConfig] = None,
        simulation_config: Optional[SimulationConfig] = None,
        metric_definitions: Optional[List[MetricDefinition]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        experiment_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Experiment|{hypothesis_id}|{name}|{experiment_type}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.hypothesis_id = hypothesis_id
        self.name = name
        self.description = description
        self.experiment_type = experiment_type
        self.dataset_config = dataset_config or DatasetConfig(source="")
        self.simulation_config = simulation_config or SimulationConfig()
        self.metric_definitions: List[MetricDefinition] = metric_definitions or []
        self.parameters: Dict[str, Any] = parameters or {}
        self.run_ids: List[str] = []
        self.best_run_id: Optional[str] = None
        self.experiment_hash: str = ""
        self.version = version
        self.tags: List[str] = tags or []
        self.experiment_trace = experiment_trace
        self.status = ExperimentStatus.DRAFT
        self.created_at = utc_now()

        self.lifecycle.transition(
            LifecycleStage.DRAFT,
            reason="Experiment created in draft",
        )

    def mark_ready(self) -> None:
        """Mark the experiment as ready to run."""
        self.status = ExperimentStatus.READY
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason="Experiment marked ready",
        )

    def mark_running(self) -> None:
        """Mark the experiment as currently running."""
        self.status = ExperimentStatus.RUNNING
        self.lifecycle.transition(
            LifecycleStage.IN_PROGRESS,
            reason="Experiment started",
        )

    def mark_completed(self) -> None:
        """Mark the experiment as completed."""
        self.status = ExperimentStatus.COMPLETED
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason="Experiment completed",
        )

    def mark_failed(self, reason: str = "") -> None:
        """Mark the experiment as failed."""
        self.status = ExperimentStatus.FAILED
        self.lifecycle.transition(
            LifecycleStage.INVALIDATED,
            reason=f"Experiment failed: {reason}" if reason else "Experiment failed",
        )

    def mark_validated(self) -> None:
        """Mark the experiment as validated."""
        self.status = ExperimentStatus.VALIDATED
        self._update_hash()
        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason="Experiment validated",
        )

    def add_run_id(self, run_id: str) -> None:
        """Register a run ID for this experiment."""
        if run_id not in self.run_ids:
            self.run_ids.append(run_id)

    def set_best_run(self, run_id: str) -> None:
        """Set the best-performing run ID."""
        self.best_run_id = run_id
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Best run set to {run_id}",
        )

    def _update_hash(self) -> None:
        """Compute the deterministic hash of this experiment definition."""
        content = self._to_hashable_dict()
        self.experiment_hash = deterministic_hash(content)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "name": self.name,
            "description": self.description,
            "experiment_type": self.experiment_type,
            "dataset_config": self.dataset_config.to_dict(),
            "simulation_config": self.simulation_config.to_dict(),
            "metric_definitions": sorted(
                [m.to_dict() for m in self.metric_definitions],
                key=lambda x: x["name"],
            ),
            "parameters": dict(sorted(self.parameters.items())) if self.parameters else {},
            "version": self.version,
            "tags": sorted(self.tags),
            "experiment_trace": self.experiment_trace,
            "status": self.status.value,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "hypothesis_id": self.hypothesis_id,
            "name": self.name,
            "description": self.description,
            "experiment_type": self.experiment_type,
            "dataset_config": self.dataset_config.to_dict(),
            "simulation_config": self.simulation_config.to_dict(),
            "metric_definitions": [m.to_dict() for m in self.metric_definitions],
            "parameters": self.parameters,
            "run_ids": self.run_ids,
            "best_run_id": self.best_run_id,
            "experiment_hash": self.experiment_hash,
            "version": self.version,
            "tags": self.tags,
            "experiment_trace": self.experiment_trace,
            "status": self.status.value,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experiment":
        obj = super().from_dict(data)
        obj.hypothesis_id = data["hypothesis_id"]
        obj.name = data.get("name", "")
        obj.description = data.get("description", "")
        obj.experiment_type = data.get("experiment_type", "Backtest")
        obj.dataset_config = DatasetConfig.from_dict(
            data.get("dataset_config", {"source": ""})
        )
        obj.simulation_config = SimulationConfig.from_dict(
            data.get("simulation_config", {})
        )
        obj.metric_definitions = [
            MetricDefinition.from_dict(m) for m in data.get("metric_definitions", [])
        ]
        obj.parameters = dict(data.get("parameters", {}))
        obj.run_ids = list(data.get("run_ids", []))
        obj.best_run_id = data.get("best_run_id")
        obj.experiment_hash = data.get("experiment_hash", "")
        obj.version = data.get("version", "1.0.0")
        obj.tags = list(data.get("tags", []))
        obj.experiment_trace = data.get("experiment_trace", "")
        obj.status = ExperimentStatus(data.get("status", "Draft"))
        obj.created_at = parse_timestamp(data["created_at"]) if data.get("created_at") else utc_now()
        return obj
