"""
W1 determinism closure — run_hash logical identity (runner flow).

The ``BaseExperimentRunner`` creates started runs (``run.start()`` sets
``started_at``) and completes them with ``duration_seconds=0.0``.  Before the
W1 fix, ``ExperimentRun.complete()`` derived ``duration_seconds`` from wall
clock when ``duration_seconds <= 0`` and ``started_at`` existed, leaking
runtime performance into ``run_hash`` so two identical logical runs hashed
differently.

Required behavior (verified here):
    1. Two identical ``BaseExperimentRunner`` runs produce identical run_hash.
    2. Changing logical parameters changes run_hash.
    3. Runtime duration does not affect run_hash.
    4. Existing result_hash determinism remains unchanged.

These tests exercise the full Dataset → Experiment → Run → Result chain through
the certified ``BackendRouter`` path.
"""

from __future__ import annotations

from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.runner import BaseExperimentRunner


def _make_experiment(**overrides):
    params = dict(
        hypothesis_id="h1",
        name="W1 Chain Test",
        dataset_config=DatasetConfig(source="s1", symbols=["AAPL"]),
        simulation_config=SimulationConfig(seed=42, initial_capital=100000.0),
    )
    params.update(overrides)
    exp = Experiment(**params)
    exp.mark_ready()
    return exp


def _make_dataset(base=100.0):
    return [
        {
            "open": base + i,
            "high": base + i + 1.0,
            "low": base + i - 0.5,
            "close": base + i + 0.25,
            "volume": 1000.0 + i * 10.0,
        }
        for i in range(20)
    ]


class TestRunnerRunHashDeterminism:
    """End-to-end runner determinism for run_hash."""

    def test_identical_runs_produce_identical_run_hash(self):
        runner = BaseExperimentRunner()
        run1, _ = runner.run(_make_experiment(), _make_dataset(100.0))
        run2, _ = runner.run(_make_experiment(), _make_dataset(100.0))
        assert run1.run_hash == run2.run_hash

    def test_changing_logical_parameters_changes_run_hash(self):
        runner = BaseExperimentRunner()
        # Different seed (logical change) must change run_hash.
        exp_a = _make_experiment(simulation_config=SimulationConfig(seed=1, initial_capital=100000.0))
        exp_b = _make_experiment(simulation_config=SimulationConfig(seed=2, initial_capital=100000.0))
        run_a, _ = runner.run(exp_a, _make_dataset(100.0))
        run_b, _ = runner.run(exp_b, _make_dataset(100.0))
        assert run_a.run_hash != run_b.run_hash

    def test_runtime_duration_does_not_affect_run_hash(self):
        # Complete two identical runs; the wall-clock time elapsed between
        # start() and complete() must not leak into run_hash.
        runner = BaseExperimentRunner()
        run1, _ = runner.run(_make_experiment(), _make_dataset(100.0))
        run2, _ = runner.run(_make_experiment(), _make_dataset(100.0))
        # duration_seconds is deterministic 0.0 (no explicit positive duration).
        assert run1.duration_seconds == 0.0
        assert run2.duration_seconds == 0.0
        assert run1.run_hash == run2.run_hash

    def test_result_hash_determinism_unchanged(self):
        runner = BaseExperimentRunner()
        _, res1 = runner.run(_make_experiment(), _make_dataset(100.0))
        _, res2 = runner.run(_make_experiment(), _make_dataset(100.0))
        # result_hash determinism is preserved (unchanged by W1).
        assert res1.result_hash == res2.result_hash

    def test_run_hash_links_result_identity(self):
        runner = BaseExperimentRunner()
        run, res = runner.run(_make_experiment(), _make_dataset(100.0))
        # The run's stored result_hash must equal the result's deterministic
        # result_hash (chain linkage preserved).
        assert run.result_hash == res.result_hash
        assert res.run_id == run.id
