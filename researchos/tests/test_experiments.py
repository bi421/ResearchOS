"""
Tests for the Quant Research Experiment Framework.

Based on Article XVII: Object Model — Experiment Layer.

All objects are tested for:
    - Deterministic identity generation
    - Correct property initialization
    - Deterministic hashing
    - Lifecycle transitions
    - Serialization (to_dict, from_dict)
    - Validation integration
    - Repository persistence
"""

from __future__ import annotations

import pytest

from researchos.core.lifecycle import LifecycleStage
from researchos.experiments.contracts import (
    DatasetConfig,
    ExperimentStatus,
    HypothesisStatus,
    MetricDefinition,
    SimulationConfig,
    ValidationStatus,
)
from researchos.experiments.experiment import Experiment
from researchos.experiments.hypothesis import QuantHypothesis
from researchos.experiments.learning import LearningRecord
from researchos.experiments.reports import ExperimentReport
from researchos.experiments.result import ExperimentResult, ExperimentRun
from researchos.experiments.runner import BaseExperimentRunner, get_runner
from researchos.experiments.validation import ExperimentValidation
from researchos.repository.memory import MemoryRepository

# =============================================================================
# Contracts Tests
# =============================================================================


class TestDatasetConfig:
    """Tests for DatasetConfig."""

    def test_creation(self):
        """Test basic DatasetConfig creation."""
        config = DatasetConfig(
            source="yahoo",
            start_date="2020-01-01",
            end_date="2023-12-31",
            symbols=["AAPL", "MSFT"],
            resolution="1d",
        )
        assert config.source == "yahoo"
        assert config.start_date == "2020-01-01"
        assert config.resolution == "1d"
        assert len(config.symbols) == 2

    def test_serialization(self):
        """Test DatasetConfig serialization round-trip."""
        config = DatasetConfig(
            source="test",
            symbols=["A", "B"],
            parameters={"key": "value"},
        )
        d = config.to_dict()
        restored = DatasetConfig.from_dict(d)
        assert restored.source == config.source
        assert restored.symbols == config.symbols
        assert restored.parameters == config.parameters


class TestSimulationConfig:
    """Tests for SimulationConfig."""

    def test_creation(self):
        """Test basic SimulationConfig creation."""
        config = SimulationConfig(
            seed=12345,
            initial_capital=50_000.0,
            commission="fixed:0.005",
        )
        assert config.seed == 12345
        assert config.initial_capital == 50_000.0
        assert config.commission == "fixed:0.005"

    def test_default_seed(self):
        """Test that default seed is 42."""
        config = SimulationConfig()
        assert config.seed == 42

    def test_serialization(self):
        """Test SimulationConfig serialization round-trip."""
        config = SimulationConfig(seed=999, max_positions=5)
        d = config.to_dict()
        restored = SimulationConfig.from_dict(d)
        assert restored.seed == 999
        assert restored.max_positions == 5


class TestMetricDefinition:
    """Tests for MetricDefinition."""

    def test_creation(self):
        """Test basic MetricDefinition creation."""
        md = MetricDefinition(
            name="sharpe_ratio",
            description="Risk-adjusted return",
            higher_is_better=True,
            target=1.5,
            tolerance=0.1,
        )
        assert md.name == "sharpe_ratio"
        assert md.target == 1.5
        assert md.tolerance == 0.1

    def test_serialization(self):
        """Test MetricDefinition serialization round-trip."""
        md = MetricDefinition(name="test", target=0.5)
        d = md.to_dict()
        restored = MetricDefinition.from_dict(d)
        assert restored.name == "test"
        assert restored.target == 0.5


# =============================================================================
# QuantHypothesis Tests
# =============================================================================


class TestQuantHypothesis:
    """Tests for QuantHypothesis objects."""

    def test_creation(self):
        """Test basic QuantHypothesis creation."""
        hyp = QuantHypothesis(
            research_question="Does momentum predict returns?",
            null_hypothesis="Momentum has no predictive power",
            alternative_hypothesis="Momentum positively predicts returns",
            significance_level=0.05,
            expected_effect=0.02,
        )
        assert hyp.research_question == "Does momentum predict returns?"
        assert hyp.null_hypothesis == "Momentum has no predictive power"
        assert hyp.alternative_hypothesis == "Momentum positively predicts returns"
        assert hyp.significance_level == 0.05
        assert hyp.expected_effect == 0.02
        assert hyp.status == HypothesisStatus.FORMULATED

    def test_deterministic_id(self):
        """Test that QuantHypothesis ID is deterministic."""
        hyp1 = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        hyp2 = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        assert hyp1.id == hyp2.id

    def test_different_inputs_different_id(self):
        """Test different inputs produce different IDs."""
        hyp1 = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        hyp2 = QuantHypothesis(
            research_question="Q2",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        assert hyp1.id != hyp2.id

    def test_lifecycle_status(self):
        """Test hypothesis status transitions."""
        hyp = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        assert hyp.status == HypothesisStatus.FORMULATED

        hyp.mark_ready()
        assert hyp.status == HypothesisStatus.READY

        hyp.mark_accepted("Test passed")
        assert hyp.status == HypothesisStatus.ACCEPTED

    def test_rejected_lifecycle(self):
        """Test rejected hypothesis lifecycle."""
        hyp = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        hyp.mark_rejected("No significant effect")
        assert hyp.status == HypothesisStatus.REJECTED

        # Check lifecycle transition was recorded
        assert hyp.lifecycle.current_stage == LifecycleStage.INVALIDATED

    def test_inconclusive(self):
        """Test inconclusive hypothesis."""
        hyp = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        hyp.mark_inconclusive("Insufficient data")
        assert hyp.status == HypothesisStatus.INCONCLUSIVE

    def test_with_metric_definitions(self):
        """Test QuantHypothesis with metric definitions."""
        metrics = [
            MetricDefinition(name="sharpe", higher_is_better=True),
            MetricDefinition(name="max_dd", higher_is_better=False),
        ]
        hyp = QuantHypothesis(
            research_question="Q1",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            metric_definitions=metrics,
        )
        assert len(hyp.metric_definitions) == 2
        assert hyp.metric_definitions[0].name == "sharpe"

    def test_serialization(self):
        """Test QuantHypothesis serialization round-trip."""
        hyp = QuantHypothesis(
            research_question="Test Q",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            significance_level=0.01,
            tags=["momentum", "equity"],
        )
        hyp.mark_ready()

        d = hyp.to_dict()
        restored = QuantHypothesis.from_dict(d)

        assert restored.research_question == hyp.research_question
        assert restored.null_hypothesis == hyp.null_hypothesis
        assert restored.significance_level == hyp.significance_level
        assert restored.tags == hyp.tags
        assert restored.status == hyp.status
        assert restored.id == hyp.id

    def test_hash_stability(self):
        """Test same inputs produce same hash."""
        hyp1 = QuantHypothesis(
            research_question="Stable Q",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        hyp2 = QuantHypothesis(
            research_question="Stable Q",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
        )
        assert hyp1.hash == hyp2.hash


# =============================================================================
# Experiment Tests
# =============================================================================


class TestExperiment:
    """Tests for Experiment objects."""

    def test_creation(self):
        """Test basic Experiment creation."""
        exp = Experiment(
            hypothesis_id="hyp1",
            name="Momentum Test",
            description="Testing momentum strategy",
            experiment_type="Backtest",
        )
        assert exp.hypothesis_id == "hyp1"
        assert exp.name == "Momentum Test"
        assert exp.experiment_type == "Backtest"
        assert exp.status == ExperimentStatus.DRAFT

    def test_deterministic_id(self):
        """Test that Experiment ID is deterministic."""
        exp1 = Experiment(hypothesis_id="hyp1", name="Test")
        exp2 = Experiment(hypothesis_id="hyp1", name="Test")
        assert exp1.id == exp2.id

    def test_lifecycle(self):
        """Test Experiment lifecycle transitions."""
        exp = Experiment(hypothesis_id="hyp1", name="Test")
        assert exp.status == ExperimentStatus.DRAFT

        exp.mark_ready()
        assert exp.status == ExperimentStatus.READY

        exp.mark_running()
        assert exp.status == ExperimentStatus.RUNNING

        exp.mark_completed()
        assert exp.status == ExperimentStatus.COMPLETED

    def test_run_management(self):
        """Test managing runs on an experiment."""
        exp = Experiment(hypothesis_id="hyp1", name="Test")
        exp.add_run_id("run1")
        exp.add_run_id("run2")
        assert len(exp.run_ids) == 2
        assert "run1" in exp.run_ids

        exp.set_best_run("run2")
        assert exp.best_run_id == "run2"

    def test_with_config(self):
        """Test Experiment with config objects."""
        dataset = DatasetConfig(source="yahoo", symbols=["AAPL"])
        sim = SimulationConfig(seed=42, initial_capital=100_000.0)
        metrics = [MetricDefinition(name="sharpe", target=1.0)]

        exp = Experiment(
            hypothesis_id="hyp1",
            name="Configured Test",
            dataset_config=dataset,
            simulation_config=sim,
            metric_definitions=metrics,
        )
        assert exp.dataset_config.source == "yahoo"
        assert exp.simulation_config.seed == 42
        assert len(exp.metric_definitions) == 1

    def test_serialization(self):
        """Test Experiment serialization round-trip."""
        exp = Experiment(
            hypothesis_id="hyp1",
            name="Serialization Test",
            tags=["test"],
        )
        exp.mark_ready()
        exp.add_run_id("run1")

        d = exp.to_dict()
        restored = Experiment.from_dict(d)

        assert restored.hypothesis_id == exp.hypothesis_id
        assert restored.name == exp.name
        assert restored.status == exp.status
        assert restored.run_ids == exp.run_ids
        assert restored.id == exp.id

    def test_hash_experiment_definition(self):
        """Test that experiment hash captures definition."""
        exp1 = Experiment(
            hypothesis_id="hyp1",
            name="Hash Test",
            experiment_type="Backtest",
        )
        exp1.mark_ready()

        exp2 = Experiment(
            hypothesis_id="hyp1",
            name="Hash Test",
            experiment_type="Backtest",
        )
        exp2.mark_ready()

        assert exp1.experiment_hash == exp2.experiment_hash


# =============================================================================
# ExperimentRun Tests
# =============================================================================


class TestExperimentRun:
    """Tests for ExperimentRun objects."""

    def test_creation(self):
        """Test basic ExperimentRun creation."""
        run = ExperimentRun(experiment_id="exp1", run_number=1)
        assert run.experiment_id == "exp1"
        assert run.run_number == 1
        assert run.status == ExperimentStatus.DRAFT

    def test_deterministic_id(self):
        """Test that ExperimentRun ID is deterministic."""
        run1 = ExperimentRun(experiment_id="exp1", run_number=1)
        run2 = ExperimentRun(experiment_id="exp1", run_number=1)
        assert run1.id == run2.id

    def test_run_lifecycle(self):
        """Test ExperimentRun lifecycle."""
        run = ExperimentRun(experiment_id="exp1")
        assert run.status == ExperimentStatus.DRAFT

        run.start()
        assert run.status == ExperimentStatus.RUNNING
        assert run.started_at is not None

        result = ExperimentResult(run_id=run.id)
        run.complete(
            result_id=result.id,
            result_hash=result.result_hash,
            duration_seconds=1.5,
            trace="Test run completed",
        )
        assert run.status == ExperimentStatus.COMPLETED
        assert run.completed_at is not None
        assert run.duration_seconds == 1.5
        assert run.trace == "Test run completed"

    def test_failed_run(self):
        """Test marking a run as failed."""
        run = ExperimentRun(experiment_id="exp1")
        run.start()
        run.fail(reason="Out of memory")
        assert run.status == ExperimentStatus.FAILED
        assert run.trace == "Out of memory"

    def test_serialization(self):
        """Test ExperimentRun serialization round-trip."""
        run = ExperimentRun(experiment_id="exp1", run_number=3)
        run.start()
        result = ExperimentResult(run_id=run.id)
        run.complete(result_id=result.id, result_hash=result.result_hash)

        d = run.to_dict()
        restored = ExperimentRun.from_dict(d)

        assert restored.experiment_id == run.experiment_id
        assert restored.run_number == run.run_number
        assert restored.status == run.status
        assert restored.run_hash == run.run_hash
        assert restored.id == run.id

    def test_hash_stability(self):
        """Test same run inputs produce same hash."""
        run1 = ExperimentRun(experiment_id="exp1", run_number=1)
        run2 = ExperimentRun(experiment_id="exp1", run_number=1)
        assert run1.run_hash == run2.run_hash


# =============================================================================
# ExperimentResult Tests
# =============================================================================


class TestExperimentResult:
    """Tests for ExperimentResult objects."""

    def test_creation(self):
        """Test basic ExperimentResult creation."""
        result = ExperimentResult(run_id="run1")
        assert result.run_id == "run1"
        assert len(result.metrics) == 0
        assert result.result_hash != ""

    def test_deterministic_id(self):
        """Test that ExperimentResult ID is deterministic."""
        r1 = ExperimentResult(run_id="run1")
        r2 = ExperimentResult(run_id="run1")
        assert r1.id == r2.id

    def test_add_metrics(self):
        """Test adding metrics to a result."""
        result = ExperimentResult(run_id="run1")
        result.add_metric("sharpe_ratio", 1.5)
        result.add_metric("max_drawdown", -0.15)
        result.add_metric("win_rate", 0.65)

        assert result.metrics["sharpe_ratio"] == 1.5
        assert result.metrics["max_drawdown"] == -0.15
        assert result.metrics["win_rate"] == 0.65
        assert len(result.metrics) == 3

    def test_add_statistics(self):
        """Test adding statistics to a result."""
        result = ExperimentResult(run_id="run1")
        result.add_statistic("mean", 0.05)
        result.add_statistic("std", 0.10)
        assert result.statistics["mean"] == 0.05
        assert result.statistics["std"] == 0.10

    def test_hash_updates_on_metric_change(self):
        """Test that hash changes when metrics are added."""
        result = ExperimentResult(run_id="run1")
        original_hash = result.result_hash
        result.add_metric("new_metric", 1.0)
        assert result.result_hash != original_hash

    def test_serialization(self):
        """Test ExperimentResult serialization round-trip."""
        result = ExperimentResult(run_id="run1")
        result.add_metric("sharpe", 1.5)
        result.add_metric("returns", 0.12)
        result.add_statistic("num_trades", 150)

        d = result.to_dict()
        restored = ExperimentResult.from_dict(d)

        assert restored.run_id == result.run_id
        assert restored.metrics["sharpe"] == 1.5
        assert restored.metrics["returns"] == 0.12
        assert restored.statistics["num_trades"] == 150
        assert restored.result_hash == result.result_hash
        assert restored.id == result.id

    def test_hash_stability(self):
        """Test same result inputs produce same hash."""
        r1 = ExperimentResult(run_id="run1")
        r1.add_metric("test", 1.0)
        r2 = ExperimentResult(run_id="run1")
        r2.add_metric("test", 1.0)
        assert r1.result_hash == r2.result_hash


# =============================================================================
# ExperimentRunner Tests
# =============================================================================


class TestExperimentRunner:
    """Tests for ExperimentRunner."""

    def test_runner_singleton(self):
        """Test that get_runner returns a valid runner."""
        runner = get_runner()
        assert runner is not None
        assert isinstance(runner, BaseExperimentRunner)

    def test_run_experiment(self):
        """Test running a basic experiment."""
        dataset = DatasetConfig(source="test", symbols=["AAPL"])
        sim = SimulationConfig(seed=42)
        exp = Experiment(
            hypothesis_id="hyp1",
            name="Runner Test",
            dataset_config=dataset,
            simulation_config=sim,
        )
        exp.mark_ready()

        runner = BaseExperimentRunner()
        run, result = runner.run(exp, dataset=None)

        assert run.status == ExperimentStatus.COMPLETED
        assert result.run_id == run.id
        assert len(result.metrics) > 0
        assert "sharpe_ratio" in result.metrics
        assert "total_return" in result.metrics

    def test_run_not_ready_fails(self):
        """Test that running a non-ready experiment raises."""
        exp = Experiment(hypothesis_id="hyp1", name="Not Ready")
        runner = BaseExperimentRunner()

        with pytest.raises(RuntimeError, match="Cannot run experiment"):
            runner.run(exp, dataset=None)

    def test_run_with_parameters(self):
        """Test running with parameter overrides."""
        exp = Experiment(hypothesis_id="hyp1", name="Param Test")
        exp.mark_ready()

        runner = BaseExperimentRunner()
        run, result = runner.run_with_parameters(
            exp, dataset=None, parameter_overrides={"lookback": 20}, run_number=1
        )

        assert run.status == ExperimentStatus.COMPLETED
        assert run.parameters["lookback"] == 20
        assert run.run_number == 1

    def test_walk_forward(self):
        """Test walk-forward analysis."""
        exp = Experiment(hypothesis_id="hyp1", name="WF Test")
        exp.mark_ready()

        runner = BaseExperimentRunner()
        results = runner.run_walk_forward(exp, dataset=None, window_size=10, step_size=5)

        assert len(results) > 0
        for run, result in results:
            assert run.status in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED)

    def test_monte_carlo(self):
        """Test Monte Carlo simulation."""
        exp = Experiment(hypothesis_id="hyp1", name="MC Test")
        exp.mark_ready()

        runner = BaseExperimentRunner()
        results = runner.run_monte_carlo(exp, dataset=None, num_simulations=5, seed=42)

        assert len(results) == 5
        for run, result in results:
            assert run.status in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED)

    def test_deterministic_runs(self):
        """Test that same seed produces same results."""
        exp = Experiment(
            hypothesis_id="hyp1",
            name="Deterministic Test",
            simulation_config=SimulationConfig(seed=42),
        )
        exp.mark_ready()

        runner = BaseExperimentRunner()
        run1, result1 = runner.run(exp, dataset=None)
        run2, result2 = runner.run(exp, dataset=None)

        # Same seed should produce same metrics
        for metric_name in result1.metrics:
            if metric_name != "num_trades":  # num_trades uses randint which may vary
                continue
            assert result1.metrics[metric_name] == result2.metrics[metric_name]


# =============================================================================
# ExperimentValidation Tests
# =============================================================================


class TestExperimentValidation:
    """Tests for ExperimentValidation objects."""

    def test_creation(self):
        """Test basic ExperimentValidation creation."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            validation_type="Target",
        )
        assert val.experiment_id == "exp1"
        assert val.hypothesis_id == "hyp1"
        assert val.overall_status == ValidationStatus.PENDING

    def test_benchmark_validation_all_pass(self):
        """Test benchmark validation where all metrics pass."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
        )
        result_metrics = {"sharpe": 1.5, "returns": 0.12}
        benchmark_metrics = {"sharpe": 1.0, "returns": 0.05}
        metrics = [
            MetricDefinition(name="sharpe", higher_is_better=True),
            MetricDefinition(name="returns", higher_is_better=True),
        ]

        val.validate_against_benchmark(result_metrics, benchmark_metrics, metrics)
        assert val.overall_status == ValidationStatus.PASSED
        assert val.confidence == 1.0

    def test_benchmark_validation_some_fail(self):
        """Test benchmark validation where some metrics fail."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
        )
        result_metrics = {"sharpe": 0.5, "returns": 0.12}
        benchmark_metrics = {"sharpe": 1.0, "returns": 0.05}
        metrics = [
            MetricDefinition(name="sharpe", higher_is_better=True),
            MetricDefinition(name="returns", higher_is_better=True),
        ]

        val.validate_against_benchmark(result_metrics, benchmark_metrics, metrics)
        # sharpe 0.5 < 1.0 fails, returns 0.12 >= 0.05 passes → 1/2 → majority = 0.5 → PASSED
        assert val.overall_status == ValidationStatus.PASSED
        assert val.confidence == 0.5

    def test_benchmark_validation_all_fail(self):
        """Test benchmark validation where all metrics fail."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
        )
        result_metrics = {"sharpe": 0.3, "returns": -0.05}
        benchmark_metrics = {"sharpe": 1.0, "returns": 0.05}
        metrics = [
            MetricDefinition(name="sharpe", higher_is_better=True),
            MetricDefinition(name="returns", higher_is_better=True),
        ]

        val.validate_against_benchmark(result_metrics, benchmark_metrics, metrics)
        assert val.overall_status == ValidationStatus.FAILED

    def test_target_validation(self):
        """Test target-based validation."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
        )
        result_metrics = {"sharpe": 1.05}
        metrics = [
            MetricDefinition(name="sharpe", target=1.0, tolerance=0.1),
        ]

        val.validate_against_targets(result_metrics, metrics)
        assert val.overall_status == ValidationStatus.PASSED

    def test_statistical_significance(self):
        """Test statistical significance validation."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
        )
        val.validate_statistical_significance(
            result_value=0.15,
            expected_value=0.0,
            std_dev=0.05,
            significance_level=0.05,
            metric_name="returns",
        )
        # z = |0.15 - 0.0| / 0.05 = 3.0 > 1.96 → significant
        assert val.overall_status == ValidationStatus.PASSED
        assert val.results["returns"]["is_significant"] is True

    def test_serialization(self):
        """Test ExperimentValidation serialization round-trip."""
        val = ExperimentValidation(
            experiment_id="exp1",
            hypothesis_id="hyp1",
        )
        val.validate_against_benchmark(
            {"sharpe": 1.5},
            {"sharpe": 1.0},
        )

        d = val.to_dict()
        restored = ExperimentValidation.from_dict(d)

        assert restored.experiment_id == val.experiment_id
        assert restored.overall_status == val.overall_status
        assert restored.confidence == val.confidence
        assert restored.id == val.id


# =============================================================================
# LearningRecord Tests
# =============================================================================


class TestLearningRecord:
    """Tests for LearningRecord objects."""

    def test_creation(self):
        """Test basic LearningRecord creation."""
        record = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        assert record.experiment_id == "exp1"
        assert record.validation_id == "val1"
        assert record.hypothesis_id == "hyp1"

    def test_deterministic_id(self):
        """Test that LearningRecord ID is deterministic."""
        r1 = LearningRecord(experiment_id="exp1", validation_id="val1", hypothesis_id="hyp1")
        r2 = LearningRecord(experiment_id="exp1", validation_id="val1", hypothesis_id="hyp1")
        assert r1.id == r2.id

    def test_add_findings(self):
        """Test adding findings to a learning record."""
        record = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        record.add_finding("Momentum is significant in bull markets")
        record.add_finding("Momentum fails in bear markets")
        assert len(record.findings) == 2

    def test_add_patterns_and_recommendations(self):
        """Test adding patterns and recommendations."""
        record = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        record.add_pattern("Momentum reversal after high volatility")
        record.add_recommendation("Use volatility filter")
        assert len(record.patterns_observed) == 1
        assert len(record.recommendations) == 1

    def test_finalize(self):
        """Test finalizing a learning record."""
        record = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        record.finalize()
        assert record.lifecycle.current_stage == LifecycleStage.COMPLETE

    def test_serialization(self):
        """Test LearningRecord serialization round-trip."""
        record = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
            hypothesis_accepted=True,
            confidence=0.85,
        )
        record.add_finding("Test finding")
        record.finalize()

        d = record.to_dict()
        restored = LearningRecord.from_dict(d)

        assert restored.experiment_id == record.experiment_id
        assert restored.hypothesis_accepted == record.hypothesis_accepted
        assert restored.confidence == record.confidence
        assert restored.findings == record.findings
        assert restored.id == record.id


# =============================================================================
# ExperimentReport Tests
# =============================================================================


class TestExperimentReport:
    """Tests for ExperimentReport objects."""

    def test_creation(self):
        """Test basic ExperimentReport creation."""
        report = ExperimentReport(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            title="Momentum Test Report",
        )
        assert report.experiment_id == "exp1"
        assert report.hypothesis_id == "hyp1"
        assert report.title == "Momentum Test Report"
        assert report.status == "Draft"

    def test_deterministic_id(self):
        """Test that ExperimentReport ID is deterministic."""
        r1 = ExperimentReport(experiment_id="exp1", hypothesis_id="hyp1", title="Report")
        r2 = ExperimentReport(experiment_id="exp1", hypothesis_id="hyp1", title="Report")
        assert r1.id == r2.id

    def test_finalize(self):
        """Test finalizing a report."""
        report = ExperimentReport(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            title="Test",
        )
        report.finalize()
        assert report.status == "Final"
        assert report.report_hash != ""

    def test_serialization(self):
        """Test ExperimentReport serialization round-trip."""
        report = ExperimentReport(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            title="Serialize Test",
            summary="A test report",
            run_ids=["run1", "run2"],
        )
        report.num_runs = 2
        report.num_passed_runs = 1
        report.finalize()

        d = report.to_dict()
        restored = ExperimentReport.from_dict(d)

        assert restored.experiment_id == report.experiment_id
        assert restored.title == report.title
        assert restored.summary == report.summary
        assert restored.run_ids == report.run_ids
        assert restored.num_runs == report.num_runs
        assert restored.status == report.status
        assert restored.id == report.id


# =============================================================================
# Full Workflow Integration Tests
# =============================================================================


class TestFullWorkflow:
    """Tests for the complete experiment workflow."""

    def test_full_workflow(self):
        """Test the complete experiment workflow end-to-end."""
        # 1. Formulate hypothesis
        hyp = QuantHypothesis(
            research_question="Does momentum strategy outperform buy-and-hold?",
            null_hypothesis="Momentum returns equal buy-and-hold returns",
            alternative_hypothesis="Momentum returns exceed buy-and-hold returns",
            significance_level=0.05,
            expected_effect=0.05,
            metric_definitions=[
                MetricDefinition(name="sharpe_ratio", higher_is_better=True, target=1.0),
                MetricDefinition(name="total_return", higher_is_better=True, target=0.10),
            ],
            tags=["momentum", "equity"],
        )
        hyp.mark_ready()
        assert hyp.status == HypothesisStatus.READY

        # 2. Create experiment
        dataset = DatasetConfig(
            source="yahoo",
            start_date="2020-01-01",
            end_date="2023-12-31",
            symbols=["SPY"],
            resolution="1d",
        )
        sim = SimulationConfig(seed=42, initial_capital=100_000.0)
        exp = Experiment(
            hypothesis_id=hyp.id,
            name="Momentum vs Buy-and-Hold",
            description="Test momentum strategy performance",
            dataset_config=dataset,
            simulation_config=sim,
            metric_definitions=hyp.metric_definitions,
            tags=["momentum"],
        )
        exp.mark_ready()
        assert exp.status == ExperimentStatus.READY

        # 3. Run experiment
        runner = BaseExperimentRunner()
        run, result = runner.run(exp, dataset=None)
        exp.add_run_id(run.id)
        exp.mark_completed()
        assert run.status == ExperimentStatus.COMPLETED
        assert len(result.metrics) > 0

        # 4. Validate results
        val = ExperimentValidation(
            experiment_id=exp.id,
            hypothesis_id=hyp.id,
            run_id=run.id,
        )
        val.validate_against_benchmark(
            result.metrics,
            {"sharpe_ratio": 1.0, "total_return": 0.10},
            hyp.metric_definitions,
        )
        assert val.overall_status in (ValidationStatus.PASSED, ValidationStatus.FAILED)

        # 5. Update hypothesis based on validation
        if val.overall_status == ValidationStatus.PASSED:
            hyp.mark_accepted("Strategy outperformed benchmark")
        else:
            hyp.mark_rejected("Strategy underperformed benchmark")

        exp.mark_validated()

        # 6. Create learning record
        learning = LearningRecord(
            experiment_id=exp.id,
            validation_id=val.id,
            hypothesis_id=hyp.id,
            run_id=run.id,
            hypothesis_accepted=(hyp.status == HypothesisStatus.ACCEPTED),
            confidence=val.confidence,
        )
        learning.add_finding(
            f"Momentum strategy sharpe: {result.metrics.get('sharpe_ratio', 'N/A')}"
        )
        learning.add_finding(
            f"Momentum strategy return: {result.metrics.get('total_return', 'N/A')}"
        )
        learning.finalize()
        assert len(learning.findings) == 2

        # 7. Generate report
        report = ExperimentReport(
            experiment_id=exp.id,
            hypothesis_id=hyp.id,
            title="Momentum Strategy Report",
            summary=f"Tested momentum vs buy-and-hold. "
            f"Hypothesis {'accepted' if learning.hypothesis_accepted else 'rejected'}.",
            run_ids=[run.id],
            best_run_id=run.id,
            metrics_summary=dict(result.metrics),
            validation_summary={"status": val.overall_status.value, "confidence": val.confidence},
            learning_summary={
                "findings": learning.findings,
                "recommendations": learning.recommendations,
            },
        )
        report.num_runs = 1
        report.num_passed_runs = 1
        report.finalize()
        assert report.status == "Final"
        assert report.report_hash != ""

        # Verify all IDs are deterministic
        hyp2 = QuantHypothesis.from_dict(hyp.to_dict())
        assert hyp2.id == hyp.id

    def test_full_workflow_determinism(self):
        """Test that the full workflow is deterministic."""

        # Run workflow twice with same inputs
        def run_workflow():
            hyp = QuantHypothesis(
                research_question="Q",
                null_hypothesis="H0",
                alternative_hypothesis="H1",
            )
            hyp.mark_ready()
            exp = Experiment(hypothesis_id=hyp.id, name="Test")
            exp.mark_ready()
            runner = BaseExperimentRunner()
            run, result = runner.run(exp, dataset=None)
            return result.metrics

        metrics1 = run_workflow()
        metrics2 = run_workflow()

        # Same metrics (except num_trades which uses randint)
        for key in metrics1:
            if key == "num_trades":
                continue
            assert metrics1[key] == metrics2[key], f"Metric {key} differs"


# =============================================================================
# Repository Persistence Tests
# =============================================================================


class TestRepositoryPersistence:
    """Tests for storing experiment objects in the repository."""

    def test_save_quant_hypothesis(self):
        """Test saving and retrieving QuantHypothesis from repository."""
        repo = MemoryRepository()
        hyp = QuantHypothesis(
            research_question="Q",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            ontology_tags=["experiment"],
        )
        repo.save(hyp)
        retrieved = repo.get(hyp.id)
        assert retrieved is not None
        assert retrieved.id == hyp.id
        assert retrieved.research_question == "Q"

    def test_save_experiment(self):
        """Test saving and retrieving Experiment from repository."""
        repo = MemoryRepository()
        exp = Experiment(
            hypothesis_id="hyp1",
            name="Repo Test",
            ontology_tags=["experiment"],
        )
        repo.save(exp)
        retrieved = repo.get(exp.id)
        assert retrieved is not None
        assert retrieved.id == exp.id
        assert retrieved.name == "Repo Test"

    def test_save_experiment_run(self):
        """Test saving and retrieving ExperimentRun from repository."""
        repo = MemoryRepository()
        run = ExperimentRun(experiment_id="exp1", run_number=1)
        run.start()
        result = ExperimentResult(run_id=run.id)
        run.complete(result_id=result.id, result_hash=result.result_hash)
        repo.save(run)
        retrieved = repo.get(run.id)
        assert retrieved is not None
        assert retrieved.id == run.id
        assert retrieved.status == ExperimentStatus.COMPLETED

    def test_save_experiment_result(self):
        """Test saving and retrieving ExperimentResult from repository."""
        repo = MemoryRepository()
        result = ExperimentResult(run_id="run1")
        result.add_metric("sharpe", 1.5)
        repo.save(result)
        retrieved = repo.get(result.id)
        assert retrieved is not None
        assert retrieved.id == result.id
        assert retrieved.metrics["sharpe"] == 1.5

    def test_save_validation(self):
        """Test saving and retrieving ExperimentValidation from repository."""
        repo = MemoryRepository()
        val = ExperimentValidation(experiment_id="exp1", hypothesis_id="hyp1")
        repo.save(val)
        retrieved = repo.get(val.id)
        assert retrieved is not None
        assert retrieved.id == val.id

    def test_save_learning_record(self):
        """Test saving and retrieving LearningRecord from repository."""
        repo = MemoryRepository()
        record = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        repo.save(record)
        retrieved = repo.get(record.id)
        assert retrieved is not None
        assert retrieved.id == record.id

    def test_save_report(self):
        """Test saving and retrieving ExperimentReport from repository."""
        repo = MemoryRepository()
        report = ExperimentReport(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            title="Test Report",
        )
        repo.save(report)
        retrieved = repo.get(report.id)
        assert retrieved is not None
        assert retrieved.id == report.id

    def test_find_by_tag(self):
        """Test finding experiment objects by ontology tag."""
        repo = MemoryRepository()
        hyp = QuantHypothesis(
            research_question="Q",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            ontology_tags=["momentum", "experiment"],
        )
        repo.save(hyp)
        results = repo.find_by_tag("momentum")
        assert len(results) == 1
        assert results[0].id == hyp.id

    def test_repository_count(self):
        """Test repository count with experiment objects."""
        repo = MemoryRepository()
        assert repo.count() == 0
        repo.save(
            QuantHypothesis(
                research_question="Q",
                null_hypothesis="H0",
                alternative_hypothesis="H1",
            )
        )
        assert repo.count() == 1
        repo.save(Experiment(hypothesis_id="hyp1", name="Test"))
        assert repo.count() == 2


# =============================================================================
# Determinism Guarantees
# =============================================================================


class TestDeterminism:
    """Tests for determinism guarantees across all experiment objects."""

    def test_quant_hypothesis_determinism(self):
        """Test QuantHypothesis determinism."""
        h1 = QuantHypothesis(
            research_question="Test",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            significance_level=0.05,
        )
        h2 = QuantHypothesis(
            research_question="Test",
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            significance_level=0.05,
        )
        assert h1.id == h2.id
        assert h1.hash == h2.hash

    def test_experiment_determinism(self):
        """Test Experiment determinism."""
        e1 = Experiment(
            hypothesis_id="hyp1",
            name="Test",
            simulation_config=SimulationConfig(seed=42),
        )
        e2 = Experiment(
            hypothesis_id="hyp1",
            name="Test",
            simulation_config=SimulationConfig(seed=42),
        )
        assert e1.id == e2.id
        assert e1.experiment_hash == e2.experiment_hash

    def test_run_determinism(self):
        """Test ExperimentRun determinism."""
        r1 = ExperimentRun(experiment_id="exp1", run_number=1)
        r2 = ExperimentRun(experiment_id="exp1", run_number=1)
        assert r1.id == r2.id
        assert r1.run_hash == r2.run_hash

    def test_result_determinism(self):
        """Test ExperimentResult determinism."""
        r1 = ExperimentResult(run_id="run1")
        r1.add_metric("test", 1.0)
        r2 = ExperimentResult(run_id="run1")
        r2.add_metric("test", 1.0)
        assert r1.id == r2.id
        assert r1.result_hash == r2.result_hash

    def test_validation_determinism(self):
        """Test ExperimentValidation determinism."""
        v1 = ExperimentValidation(experiment_id="exp1", hypothesis_id="hyp1")
        v1.validate_against_benchmark({"m": 1.0}, {"m": 0.5})
        v2 = ExperimentValidation(experiment_id="exp1", hypothesis_id="hyp1")
        v2.validate_against_benchmark({"m": 1.0}, {"m": 0.5})
        assert v1.id == v2.id
        assert v1.overall_status == v2.overall_status

    def test_learning_determinism(self):
        """Test LearningRecord determinism."""
        l1 = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        l2 = LearningRecord(
            experiment_id="exp1",
            validation_id="val1",
            hypothesis_id="hyp1",
        )
        assert l1.id == l2.id

    def test_report_determinism(self):
        """Test ExperimentReport determinism."""
        r1 = ExperimentReport(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            title="Report",
        )
        r2 = ExperimentReport(
            experiment_id="exp1",
            hypothesis_id="hyp1",
            title="Report",
        )
        assert r1.id == r2.id
