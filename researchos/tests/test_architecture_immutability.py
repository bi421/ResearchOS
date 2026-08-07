"""
Architecture Hardening — Immutability & Provenance tests (Issues #3, #4, #5).

Confirmed issues being covered:
    #3 — ``ExperimentResult`` containers (metrics/statistics/performance/
         metadata) must be immutable read-only mapping views; only the
         provided mutators may change them, and any change recomputes the
         deterministic ``result_hash``.
    #4 — ``ExperimentRun`` must freeze its parameters and take deep-copied
         config snapshots so later external mutation of the source config
         cannot corrupt the historical record.
    #5 — The ``BaseExperimentRunner`` must derive real dataset provenance
         (a deterministic content hash) instead of a hardcoded ``"1.0.0"``
         dataset version.

Contract-preserving: no existing behavior is changed; these tests assert the
new immutability/provenance guarantees introduced by the hardening pass.
"""

from __future__ import annotations

import pytest

from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.result import ExperimentResult, ExperimentRun
from researchos.experiments.runner import BaseExperimentRunner


# =============================================================================
# Issue #3 — Immutable ExperimentResult containers
# =============================================================================


class TestExperimentResultImmutability:
    """The result containers must be read-only mapping views."""

    def test_metrics_is_read_only(self):
        result = ExperimentResult(run_id="run1")
        result.add_metric("sharpe", 1.5)
        with pytest.raises(TypeError):
            result.metrics["sharpe"] = 99.0

    def test_statistics_is_read_only(self):
        result = ExperimentResult(run_id="run1")
        result.add_statistic("mean", 0.05)
        with pytest.raises(TypeError):
            result.statistics["mean"] = 0.99

    def test_performance_is_read_only(self):
        result = ExperimentResult(run_id="run1", performance={"win_rate": 0.6})
        with pytest.raises(TypeError):
            result.performance["win_rate"] = 1.0

    def test_metadata_is_read_only(self):
        result = ExperimentResult(run_id="run1")
        result.set_metadata_item("equity_curve", [100.0, 105.0])
        with pytest.raises(TypeError):
            result.metadata["equity_curve"] = [1.0]

    def test_delete_raises(self):
        result = ExperimentResult(run_id="run1")
        result.add_metric("sharpe", 1.5)
        with pytest.raises(TypeError):
            del result.metrics["sharpe"]

    def test_mutator_updates_hash(self):
        result = ExperimentResult(run_id="run1")
        original = result.result_hash
        result.add_metric("sharpe", 1.5)
        assert result.result_hash != original

    def test_serialization_round_trip_preserves_immutability(self):
        result = ExperimentResult(run_id="run1")
        result.add_metric("sharpe", 1.5)
        result.add_statistic("mean", 0.05)
        restored = ExperimentResult.from_dict(result.to_dict())
        with pytest.raises(TypeError):
            restored.metrics["sharpe"] = 0.0


# =============================================================================
# Issue #4 — ExperimentRun freezes parameters and config snapshots
# =============================================================================


class TestExperimentRunImmutability:
    """The run must freeze its parameters and snapshot its configs."""

    def test_parameters_are_read_only(self):
        run = ExperimentRun(
            experiment_id="exp1",
            parameters={"lookback": 20, "seed": 42},
        )
        with pytest.raises(TypeError):
            run.parameters["lookback"] = 99

    def test_config_snapshot_decouples_from_source(self):
        dataset = DatasetConfig(source="yahoo", symbols=["AAPL"])
        sim = SimulationConfig(seed=42)

        run = ExperimentRun(
            experiment_id="exp1",
            dataset_config=dataset,
            simulation_config=sim,
        )

        # Mutate the source configs after the run was created.
        dataset.source = "mutated_source"
        dataset.symbols.append("MSFT")
        sim.seed = 999
        sim.parameters["new"] = "value"

        # The recorded run must be unaffected.
        assert run.dataset_config.source == "yahoo"
        assert run.dataset_config.symbols == ["AAPL"]
        assert run.simulation_config.seed == 42
        assert "new" not in run.simulation_config.parameters

    def test_run_hash_stable_for_same_inputs(self):
        r1 = ExperimentRun(
            experiment_id="exp1",
            run_number=1,
            dataset_config=DatasetConfig(source="s1"),
            simulation_config=SimulationConfig(seed=1),
            parameters={"a": 1},
        )
        r2 = ExperimentRun(
            experiment_id="exp1",
            run_number=1,
            dataset_config=DatasetConfig(source="s1"),
            simulation_config=SimulationConfig(seed=1),
            parameters={"a": 1},
        )
        # Explicit duration_seconds keeps the run hash deterministic (when
        # started_at is None, complete() derives duration from wall-clock,
        # which would introduce nondeterministic microsecond noise).
        r1.complete(result_id="same", result_hash="same_hash", duration_seconds=1.0)
        r2.complete(result_id="same", result_hash="same_hash", duration_seconds=1.0)
        assert r1.run_hash == r2.run_hash

    def test_run_hash_changes_with_parameters(self):
        r1 = ExperimentRun(
            experiment_id="exp1",
            dataset_config=DatasetConfig(source="s1"),
            simulation_config=SimulationConfig(seed=1),
            parameters={"a": 1},
        )
        r2 = ExperimentRun(
            experiment_id="exp1",
            dataset_config=DatasetConfig(source="s1"),
            simulation_config=SimulationConfig(seed=1),
            parameters={"a": 2},
        )
        # run_hash is computed on completion; complete both and compare.
        r1.complete(result_id="r1", result_hash="h1")
        r2.complete(result_id="r2", result_hash="h2")
        assert r1.run_hash != r2.run_hash


# =============================================================================
# Issue #5 — Real dataset provenance in the runner
# =============================================================================


def _price_dataset(length: int = 20, base: float = 100.0) -> list:
    """Build a deterministic OHLCV-style dataset with enough bars."""
    return [
        {
            "open": base + i,
            "high": base + i + 1.0,
            "low": base + i - 0.5,
            "close": base + i + 0.25,
            "volume": 1000.0 + i * 10.0,
        }
        for i in range(length)
    ]


class TestDatasetProvenance:
    """The runner must derive a real deterministic dataset hash."""

    def _make_ready_experiment(self):
        exp = Experiment(hypothesis_id="hyp1", name="Provenance Test")
        exp.mark_ready()
        return exp

    def test_dataset_provenance_is_deterministic(self):
        runner = BaseExperimentRunner()
        dataset = _price_dataset(10)
        h1 = runner._dataset_provenance(dataset)
        h2 = runner._dataset_provenance(dataset)
        assert h1 == h2
        assert h1 != "1.0.0"

    def test_dataset_provenance_differs_by_content(self):
        runner = BaseExperimentRunner()
        d1 = _price_dataset(10, base=100.0)
        d2 = _price_dataset(10, base=101.0)
        assert runner._dataset_provenance(d1) != runner._dataset_provenance(d2)

    def test_run_records_real_dataset_version(self):
        runner = BaseExperimentRunner()
        exp = self._make_ready_experiment()
        run, result = runner.run(exp, dataset=_price_dataset(20))
        # The recorded dataset version must be a real content hash, not the
        # hardcoded "1.0.0".
        assert result.statistics["dataset_version"] != "1.0.0"
        assert len(result.statistics["dataset_version"]) == 64  # sha256 hex

    def test_different_datasets_produce_different_run_versions(self):
        runner = BaseExperimentRunner()
        exp = self._make_ready_experiment()
        _, r1 = runner.run(exp, dataset=_price_dataset(20, base=100.0))
        _, r2 = runner.run(exp, dataset=_price_dataset(20, base=101.0))
        assert (
            r1.statistics["dataset_version"]
            != r2.statistics["dataset_version"]
        )
