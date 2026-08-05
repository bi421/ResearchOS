"""
ExperimentRunner — abstract interface and base implementation for running experiments.

Purpose:
    ExperimentRunner provides the execution engine for experiments. The abstract
    interface is designed so that a future C++ Quant Engine can implement it
    without changing the experiment objects or result types.

    The base implementation delegates all computation to QuantComputationInterface
    (PythonQuantBackend), ensuring deterministic, auditable, repeatable results.

Architecture:
    Experiment Framework
            |
            v
    QuantComputationInterface
            |
            |-- PythonQuantBackend (current)
            +-- CppQuantBackend (future)

    The Experiment Framework NEVER:
        - loads CSV files directly
        - parses OHLCV data
        - knows MT5/TradingView formats
        - contains financial calculation logic

Based on Article XVII: Object Model — Experiment Layer.

Design:
    The runner takes an Experiment and a dataset, executes the simulation
    via the QuantComputationInterface, and produces ExperimentRun + ExperimentResult
    objects. All computation is deterministic and versioned.

Phase 4.2 / 4.4:
    Every computation is routed through the certified ``BackendRouter``. When
    no router is supplied, the runner constructs an internal one whose
    reference backend is the configured ``backend`` (or ``PythonQuantBackend``).
    The router's execution metadata (backend identity, version, fallback
    behavior, validation status, error code, result hash, capability profile,
    and Phase 4.4 scheduler statistics) is propagated into the
    ``ExperimentResult`` statistics (and therefore the deterministic result
    hash), while the observational ``backend_execution_time_ms`` /
    ``backend_execution_timestamp`` are recorded on the result but never
    hashed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from researchos.experiments.experiment import Experiment
from researchos.experiments.result import ExperimentResult, ExperimentRun
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.quant_engine.router import BackendRouter
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)


class AbstractExperimentRunner(ABC):
    """
    Abstract interface for experiment execution.

    Implementations can be:
        - Pure Python reference implementation (BaseExperimentRunner)
        - C++ Quant Engine (future) via pybind11

    All implementations must accept the same Experiment and DatasetConfig
    and produce the same ExperimentRun + ExperimentResult types.
    """

    @abstractmethod
    def run(
        self,
        experiment: Experiment,
        dataset: Any,
    ) -> Tuple[ExperimentRun, ExperimentResult]:
        """
        Execute an experiment against a dataset.

        Args:
            experiment: The experiment definition to run.
            dataset: The dataset to run against (type is implementation-specific).

        Returns:
            Tuple of (ExperimentRun, ExperimentResult).

        Raises:
            RuntimeError: If the experiment is not in Ready status.
        """
        pass

    @abstractmethod
    def run_with_parameters(
        self,
        experiment: Experiment,
        dataset: Any,
        parameter_overrides: Dict[str, Any],
        run_number: int = 1,
    ) -> Tuple[ExperimentRun, ExperimentResult]:
        """
        Execute an experiment with parameter overrides.

        Args:
            experiment: The experiment definition.
            dataset: The dataset to run against.
            parameter_overrides: Parameters to override for this run.
            run_number: Sequential run number.

        Returns:
            Tuple of (ExperimentRun, ExperimentResult).
        """
        pass

    @abstractmethod
    def run_walk_forward(
        self,
        experiment: Experiment,
        dataset: Any,
        window_size: int = 252,
        step_size: int = 63,
    ) -> List[Tuple[ExperimentRun, ExperimentResult]]:
        """
        Execute a walk-forward analysis.

        Args:
            experiment: The experiment definition.
            dataset: The full dataset.
            window_size: Training window size in periods.
            step_size: Step size between windows.

        Returns:
            List of (ExperimentRun, ExperimentResult) tuples.
        """
        pass

    @abstractmethod
    def run_monte_carlo(
        self,
        experiment: Experiment,
        dataset: Any,
        num_simulations: int = 1000,
        seed: Optional[int] = None,
    ) -> List[Tuple[ExperimentRun, ExperimentResult]]:
        """
        Execute Monte Carlo simulations.

        Args:
            experiment: The experiment definition.
            dataset: The dataset for parameterising simulations.
            num_simulations: Number of simulation runs.
            seed: Optional random seed (uses experiment seed if not provided).

        Returns:
            List of (ExperimentRun, ExperimentResult) tuples.
        """
        pass


class BaseExperimentRunner(AbstractExperimentRunner):
    """
    Pure Python reference implementation of the ExperimentRunner.

    Delegates all computation to QuantComputationInterface (PythonQuantBackend),
    which provides deterministic, versioned financial calculations.

    The runner itself handles:
        - Experiment lifecycle management
        - Run creation and tracking
        - Result packaging with full provenance

    The Quant Engine handles:
        - Returns calculation
        - Metrics computation (Sharpe, Sortino, etc.)
        - Statistics computation
        - Performance analytics
    """

    def __init__(
        self,
        backend: Optional[QuantComputationInterface] = None,
        router: Optional[BackendRouter] = None,
    ) -> None:
        """
        Initialize the runner.

        Args:
            backend: Quant computation backend. Uses PythonQuantBackend if not provided.
            router: Optional BackendRouter (Phase 4.2/4.4). When provided, the
                runner routes each computation through the certified router
                flow and propagates deterministic backend metadata plus
                observational execution telemetry. When None, an internal
                router is constructed with ``backend`` as its reference.

        Raises:
            TypeError: If ``router`` is provided but is not a ``BackendRouter``.
        """
        if router is not None and not isinstance(router, BackendRouter):
            raise TypeError("router must be a BackendRouter or None")
        self._router = router
        if router is not None:
            self._backend = getattr(router, "reference_backend", backend or PythonQuantBackend())
        else:
            if backend is None:
                backend = PythonQuantBackend()
            self._backend = backend
            self._router = BackendRouter(reference_backend=backend)

    def _ensure_ready(self, experiment: Experiment) -> None:
        """Ensure the experiment is in Ready status before running."""
        if experiment.status.value != "Ready" and experiment.status.value != "Running":
            raise RuntimeError(
                f"Cannot run experiment in status '{experiment.status.value}'. "
                "Mark experiment as Ready first."
            )

    def run(
        self,
        experiment: Experiment,
        dataset: Any,
    ) -> Tuple[ExperimentRun, ExperimentResult]:
        """Execute an experiment against a dataset."""
        self._ensure_ready(experiment)

        sim_config = experiment.simulation_config

        run = ExperimentRun(
            experiment_id=experiment.id,
            run_number=1,
            dataset_config=experiment.dataset_config,
            simulation_config=sim_config,
        )
        run.start()

        try:
            result = self._execute_simulation(experiment, dataset, run)

            run.complete(
                result_id=result.id,
                result_hash=result.result_hash,
                duration_seconds=0.0,
                trace="BaseExperimentRunner: simulation completed via PythonQuantBackend",
            )

            return run, result

        except Exception as e:
            run.fail(reason=str(e))
            raise

    def run_with_parameters(
        self,
        experiment: Experiment,
        dataset: Any,
        parameter_overrides: Dict[str, Any],
        run_number: int = 1,
    ) -> Tuple[ExperimentRun, ExperimentResult]:
        """Execute an experiment with parameter overrides."""
        self._ensure_ready(experiment)

        merged_params = dict(experiment.parameters)
        merged_params.update(parameter_overrides)

        sim_config = experiment.simulation_config

        run = ExperimentRun(
            experiment_id=experiment.id,
            run_number=run_number,
            dataset_config=experiment.dataset_config,
            simulation_config=sim_config,
            parameters=merged_params,
        )
        run.start()

        try:
            result = self._execute_simulation(experiment, dataset, run)

            run.complete(
                result_id=result.id,
                result_hash=result.result_hash,
                duration_seconds=0.0,
                trace=f"BaseExperimentRunner: parameterised run {run_number}",
            )

            return run, result

        except Exception as e:
            run.fail(reason=str(e))
            raise

    def run_walk_forward(
        self,
        experiment: Experiment,
        dataset: Any,
        window_size: int = 252,
        step_size: int = 63,
    ) -> List[Tuple[ExperimentRun, ExperimentResult]]:
        """Execute a walk-forward analysis."""
        self._ensure_ready(experiment)

        results: List[Tuple[ExperimentRun, ExperimentResult]] = []
        num_windows = self._estimate_windows(dataset, window_size, step_size)

        for i in range(num_windows):
            sim_config = experiment.simulation_config

            run = ExperimentRun(
                experiment_id=experiment.id,
                run_number=i + 1,
                dataset_config=experiment.dataset_config,
                simulation_config=sim_config,
                parameters={"window": i, "window_size": window_size},
            )
            run.start()

            try:
                result = self._execute_simulation(experiment, dataset, run)
                run.complete(
                    result_id=result.id,
                    result_hash=result.result_hash,
                    duration_seconds=0.0,
                    trace=f"BaseExperimentRunner: walk-forward window {i}",
                )
                results.append((run, result))
            except Exception as e:
                run.fail(reason=str(e))
                results.append((run, ExperimentResult(
                    run_id=run.id,
                    trace=f"Failed: {e}",
                )))

        return results

    def run_monte_carlo(
        self,
        experiment: Experiment,
        dataset: Any,
        num_simulations: int = 1000,
        seed: Optional[int] = None,
    ) -> List[Tuple[ExperimentRun, ExperimentResult]]:
        """Execute Monte Carlo simulations."""
        self._ensure_ready(experiment)

        base_seed = seed if seed is not None else experiment.simulation_config.seed
        results: List[Tuple[ExperimentRun, ExperimentResult]] = []

        for i in range(num_simulations):
            run = ExperimentRun(
                experiment_id=experiment.id,
                run_number=i + 1,
                dataset_config=experiment.dataset_config,
                simulation_config=experiment.simulation_config,
                parameters={"simulation": i, "mc_seed": base_seed + i},
            )
            run.start()

            try:
                result = self._execute_simulation(experiment, dataset, run)
                run.complete(
                    result_id=result.id,
                    result_hash=result.result_hash,
                    duration_seconds=0.0,
                    trace=f"BaseExperimentRunner: MC simulation {i}",
                )
                results.append((run, result))
            except Exception as e:
                run.fail(reason=str(e))
                results.append((run, ExperimentResult(
                    run_id=run.id,
                    trace=f"Failed: {e}",
                )))

        return results

    def _execute_simulation(
        self,
        experiment: Experiment,
        dataset: Any,
        run: ExperimentRun,
    ) -> ExperimentResult:
        """
        Execute the core simulation logic via QuantComputationInterface.

        The runner:
            1. Builds a SimulationRequest from the experiment config
            2. Delegates computation to the Quant Engine backend (which owns
               all dataset-contract normalization — Candle / OHLCV parsing)
            3. Maps SimulationResult → ExperimentResult with full provenance

        The Experiment Framework NEVER:
            - loads CSV files directly
            - parses OHLCV data
            - knows MT5/TradingView formats
            - contains financial calculation logic

        Args:
            experiment: The experiment definition.
            dataset: The dataset contract (forwarded to backend for normalization).
            run: The run object to track execution.

        Returns:
            ExperimentResult with computed metrics, statistics, and performance.
        """
        sim_config = experiment.simulation_config
        dataset_config = experiment.dataset_config

        # Build SimulationRequest for the Quant Engine
        request = SimulationRequest(
            dataset_reference=(
                dataset_config.source or "experiment"
            ),
            dataset_version="1.0.0",
            calculation_version=CalculationVersion.CALCULATION_V1,
            start_time=dataset_config.start_date,
            end_time=dataset_config.end_date,
            parameters={
                "initial_capital": sim_config.initial_capital,
                "commission": sim_config.commission,
                "slippage": sim_config.slippage,
                "max_positions": sim_config.max_positions,
                **sim_config.parameters,
                **run.parameters,
            },
            seed=sim_config.seed,
            tags=experiment.tags,
        )

        # Execute computation through the certified router. The backend owns
        # all dataset-contract normalisation — the runner simply forwards the
        # raw contract (None, HistoricalDataset, list, etc.) unchanged.
        routing = self._router.execute(
            "run_simulation",
            {
                "request": request,
                "dataset": dataset,
                "calculation_version": CalculationVersion.CALCULATION_V1,
            },
        )
        sim_result: SimulationResult = routing.output
        router_meta = routing.metadata

        # Map SimulationResult → ExperimentResult
        result = ExperimentResult(run_id=run.id)

        # Map metrics
        for metric_name, metric_value in sim_result.metrics.items():
            result.add_metric(metric_name, float(metric_value))

        # Map statistics
        for stat_name, stat_value in sim_result.statistics.items():
            result.add_statistic(stat_name, stat_value)

        # Map performance analytics
        for perf_name, perf_value in sim_result.performance.items():
            result.add_statistic(perf_name, perf_value)

        # Add computation provenance
        result.add_statistic("computation_backend", router_meta.backend)
        result.add_statistic("calculation_version", sim_result.calculation_version.value)
        result.add_statistic("input_hash", sim_result.input_hash)
        result.add_statistic("result_hash", sim_result.result_hash)
        result.add_statistic("simulation_id", sim_result.simulation_id)
        result.add_statistic("dataset_reference", sim_result.dataset_reference)
        result.add_statistic("dataset_version", sim_result.dataset_version)
        result.add_statistic("seed", experiment.simulation_config.seed)
        result.add_statistic("run_number", run.run_number)

        # Store equity curve and returns as metadata
        result.metadata["equity_curve"] = sim_result.equity_curve
        result.metadata["returns"] = sim_result.returns

        # Propagate backtest artifacts (packaging only — the backend produced
        # these deterministically; the runner never parses or computes them).
        result.trades = list(sim_result.trades)
        result.signals = list(sim_result.signals)
        result.metadata["positions"] = list(sim_result.positions)
        result.metadata["execution_stats"] = dict(sim_result.execution_stats)

        # ── Phase 4.2/4.4: propagate router backend metadata ────────────
        self._propagate_router_stats(result, router_meta)

        return result

    def _propagate_router_stats(
        self,
        result: ExperimentResult,
        meta: Any,
    ) -> None:
        """Propagate deterministic backend metadata from the router.

        Copies the deterministic fields from the router execution metadata into
        result statistics (and therefore into the result hash); the
        observational timing/timestamp is recorded on the result but never
        hashed.
        """
        result.add_statistic("backend_id", meta.backend)
        result.add_statistic("backend_version", meta.version)
        result.add_statistic("backend_fallback_used", meta.fallback_used)
        result.add_statistic("backend_validation_status", meta.validation_status)
        result.add_statistic("backend_error_code", meta.error_code)
        result.add_statistic("backend_result_hash", meta.result_hash)
        result.add_statistic(
            "backend_capability_profile",
            meta.capability_profile.to_dict()
            if meta.capability_profile is not None
            else {},
        )
        # Phase 4.4 scheduler statistics
        result.add_statistic("backend_fallback_count", meta.fallback_count)
        result.add_statistic("backend_attempted_backends", list(meta.attempted_backends))
        result.add_statistic("backend_policy_version", meta.policy_version)
        result.add_statistic("backend_profile_version", meta.profile_version)
        decision = meta.scheduler_decision
        result.add_statistic(
            "backend_scheduler_decision",
            decision.to_dict() if decision is not None else {"selected_backend": meta.backend},
        )
        # Observational telemetry — never hashed.
        result.backend_execution_time_ms = meta.execution_time_ms
        result.backend_execution_timestamp = meta.execution_timestamp

    def _estimate_windows(
        self,
        dataset: Any,
        window_size: int,
        step_size: int,
    ) -> int:
        """
        Estimate the number of walk-forward windows.

        Args:
            dataset: The dataset (may have a length).
            window_size: Size of each training window.
            step_size: Step size between windows.

        Returns:
            Estimated number of windows.
        """
        # Default estimate: assume 5 years of daily data
        estimated_periods = 5 * 252
        if hasattr(dataset, "__len__"):
            estimated_periods = len(dataset)
        elif isinstance(dataset, list):
            estimated_periods = len(dataset)

        if estimated_periods <= window_size:
            return 1

        return (estimated_periods - window_size) // step_size + 1


# Default runner instance
_default_runner: Optional[BaseExperimentRunner] = None


def get_runner() -> BaseExperimentRunner:
    """
    Get the default experiment runner instance.

    Returns:
        BaseExperimentRunner singleton.
    """
    global _default_runner
    if _default_runner is None:
        _default_runner = BaseExperimentRunner()
    return _default_runner
