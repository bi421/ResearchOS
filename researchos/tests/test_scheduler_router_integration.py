"""
Integration tests: BackendRouter ↔ BackendScheduler (Phase 4.4).

Verifies that the router now behaves as an adaptive production scheduler:

    1. Deterministic profile-driven selection (dataset size + operation +
       capability + certified performance profile).
    2. Deterministic result_hash preserved for identical inputs + identical
       router configuration (scheduling must not break determinism).
    3. Multi-attempt fallback chain: a failing / diverging candidate falls
       through to the next candidate, then to the Python reference.
    4. Fallback metadata: fallback_count, attempted_backends, error_code.
    5. Execution telemetry recorded observationally (never hashed).
    6. Explicit recalibrate_profile() folds historical performance into a
       versioned profile.
    7. ExperimentResult propagation: deterministic scheduling stats hashed;
       wall-clock duration observational.
"""

from __future__ import annotations

from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.result import ExperimentResult
from researchos.experiments.runner import BaseExperimentRunner
from researchos.quant_engine import (
    ERROR_OK,
    ERROR_VALIDATION_FAILED,
    BackendCapabilities,
    BackendRouter,
    PythonQuantBackend,
)
from researchos.quant_engine.capabilities import QUANT_OPERATIONS
from researchos.quant_engine.models import CalculationVersion
from researchos.quant_engine.scheduler import (
    BackendScheduler,
    CertifiedPerformanceProfile,
    DatasetSizeClass,
    PerformanceStat,
)

_V1 = CalculationVersion.CALCULATION_V1


def _prices(n: int, base: float = 100.0) -> list[float]:
    return [base + i * 0.1 for i in range(n)]


class _NamedBackend(PythonQuantBackend):
    BACKEND_NAME = "NamedBackend"
    BACKEND_VERSION = "1.0.0"

    def capabilities(self):
        return BackendCapabilities(
            backend_name=self.BACKEND_NAME,
            version=self.BACKEND_VERSION,
            supported_operations=QUANT_OPERATIONS,
        )


class _FastBackend(_NamedBackend):
    BACKEND_NAME = "FastBackend"


class _SlowBackend(_NamedBackend):
    BACKEND_NAME = "SlowBackend"


class _RaisingBackend(_NamedBackend):
    BACKEND_NAME = "RaisingBackend"

    def calculate_returns(self, prices, return_type="percentage", calculation_version=_V1):
        raise RuntimeError("candidate exploded")


class _DivergingBackend(_NamedBackend):
    BACKEND_NAME = "DivergingBackend"

    def calculate_returns(self, prices, return_type="percentage", calculation_version=_V1):
        out = super().calculate_returns(prices, return_type, calculation_version)
        return [x + 1.0 for x in out]


def _profile_for(op: str) -> CertifiedPerformanceProfile:
    """Profile where FastBackend beats SlowBackend for `op` at every size."""
    profile = CertifiedPerformanceProfile(version="1.0.0", source="test")
    for size in DatasetSizeClass:
        profile = profile.add("FastBackend", op, size, PerformanceStat(1.0)).add("SlowBackend", op, size, PerformanceStat(10.0))
    return profile


def _make_experiment() -> Experiment:
    exp = Experiment(
        hypothesis_id="hyp_sched",
        name="Scheduler Integration",
        dataset_config=DatasetConfig(source="sched_source"),
        simulation_config=SimulationConfig(seed=42, initial_capital=100_000.0),
    )
    exp.mark_ready()
    return exp


class TestAdaptiveSelection:
    def test_profile_selects_fastest_backend(self):
        router = BackendRouter(
            candidates=[_SlowBackend(), _FastBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.backend == "FastBackend"
        assert result.metadata.error_code == ERROR_OK
        assert result.metadata.fallback_used is False
        assert result.metadata.policy_version
        assert result.metadata.profile_version == "1.0.0"
        assert result.metadata.fallback_count == 0

    def test_size_class_drives_selection(self):
        profile = (
            CertifiedPerformanceProfile(version="1.0.0", source="test")
            .add("FastBackend", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(50.0))
            .add("SlowBackend", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(5.0))
            .add("FastBackend", "calculate_returns", DatasetSizeClass.LARGE, PerformanceStat(5.0))
            .add("SlowBackend", "calculate_returns", DatasetSizeClass.LARGE, PerformanceStat(50.0))
        )
        router = BackendRouter(
            candidates=[_FastBackend(), _SlowBackend()],
            scheduler=BackendScheduler(profile=profile),
        )
        small = router.execute("calculate_returns", {"prices": _prices(100)})
        large = router.execute("calculate_returns", {"prices": _prices(100_000)})
        # SMALL → SlowBackend is faster; LARGE → FastBackend is faster.
        assert small.metadata.backend == "SlowBackend"
        assert large.metadata.backend == "FastBackend"

    def test_decision_recorded_in_metadata(self):
        router = BackendRouter(
            candidates=[_SlowBackend(), _FastBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        decision = result.metadata.scheduler_decision
        assert decision is not None
        assert decision.selected_backend == "FastBackend"
        assert "FastBackend" in decision.candidates_considered
        rejected_name, rejected_reason = decision.rejected_reasons[0]
        assert rejected_name == "SlowBackend"
        assert rejected_reason.startswith("estimated slower")

    def test_no_scheduler_preserves_first_candidate(self):
        router = BackendRouter(candidates=[_SlowBackend(), _FastBackend()])
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.backend == "SlowBackend"

    def test_scheduler_can_deliberately_select_reference(self):
        # The Python reference is a schedulable option when a scheduler is
        # configured: the per-operation adoption policy selects it when it is
        # the faster certified backend (not a failure-driven fallback).
        profile = (
            CertifiedPerformanceProfile(version="1.0.0", source="test")
            .add("FastBackend", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(50.0))
            .add(
                "PythonQuantBackend",
                "calculate_returns",
                DatasetSizeClass.SMALL,
                PerformanceStat(5.0),
            )
        )
        router = BackendRouter(
            candidates=[_FastBackend()],
            scheduler=BackendScheduler(profile=profile),
        )
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.backend == "PythonQuantBackend"
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_OK  # deliberate, not a failure
        assert result.metadata.validation_status == "not_required"
        assert result.metadata.fallback_count == 0
        assert result.metadata.scheduler_decision.selected_backend == "PythonQuantBackend"
        assert result.output == PythonQuantBackend().calculate_returns(_prices(200))


class TestDeterminism:
    def test_result_hash_stable_with_scheduler(self):
        router = BackendRouter(
            candidates=[_SlowBackend(), _FastBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        a = router.execute("calculate_returns", {"prices": _prices(200)})
        b = router.execute("calculate_returns", {"prices": _prices(200)})
        assert a.metadata.result_hash == b.metadata.result_hash
        assert a.metadata.backend == b.metadata.backend
        assert a.metadata.scheduler_decision.to_dict() == b.metadata.scheduler_decision.to_dict()

    def test_metadata_roundtrip_preserves_scheduler_fields(self):
        router = BackendRouter(
            candidates=[_SlowBackend(), _FastBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        restored = type(result.metadata).from_dict(result.metadata.to_dict())
        assert restored.to_dict() == result.metadata.to_dict()
        assert restored.fallback_count == result.metadata.fallback_count
        assert restored.attempted_backends == result.metadata.attempted_backends


class TestFallbackChain:
    def test_failing_candidate_falls_through_to_next(self):
        router = BackendRouter(candidates=[_RaisingBackend(), _FastBackend()])
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.backend == "FastBackend"
        assert result.metadata.fallback_used is False
        assert result.metadata.fallback_count == 1
        assert result.metadata.attempted_backends == ("RaisingBackend",)
        assert result.metadata.error_code == ERROR_OK

    def test_diverging_candidate_falls_through_to_next(self):
        router = BackendRouter(candidates=[_DivergingBackend(), _FastBackend()])
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.backend == "FastBackend"
        assert result.metadata.fallback_count == 1
        assert result.metadata.attempted_backends == ("DivergingBackend",)
        assert result.output == PythonQuantBackend().calculate_returns(_prices(200))

    def test_all_candidates_fail_falls_back_to_reference(self):
        router = BackendRouter(candidates=[_RaisingBackend(), _DivergingBackend()])
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.backend == "PythonQuantBackend"
        assert result.metadata.fallback_used is True
        assert result.metadata.fallback_count == 2
        assert result.metadata.attempted_backends == ("RaisingBackend", "DivergingBackend")
        assert result.metadata.error_code == ERROR_VALIDATION_FAILED
        assert result.output == PythonQuantBackend().calculate_returns(_prices(200))

    def test_reference_fallback_preserves_decision(self):
        router = BackendRouter(
            candidates=[_RaisingBackend(), _DivergingBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        result = router.execute("calculate_returns", {"prices": _prices(200)})
        assert result.metadata.scheduler_decision is not None
        assert result.metadata.profile_version == "1.0.0"


class TestTelemetry:
    def test_history_records_every_execution(self):
        router = BackendRouter(candidates=[_FastBackend()])
        router.execute("calculate_returns", {"prices": _prices(200)})
        router.execute("calculate_returns", {"prices": _prices(200)})
        assert len(router.history) == 2
        record = router.history.records[0]
        assert record.operation == "calculate_returns"
        assert record.backend == "FastBackend"
        assert record.size_class == DatasetSizeClass.SMALL.value
        assert record.duration_ms >= 0.0
        assert record.validation_status == "passed"
        assert record.error_code == ERROR_OK
        assert record.fallback_count == 0

    def test_history_summary(self):
        router = BackendRouter(candidates=[_RaisingBackend(), _FastBackend()])
        router.execute("calculate_returns", {"prices": _prices(200)})
        summary = router.history.summary()
        assert summary["total_executions"] == 1
        assert summary["total_fallbacks"] == 1
        assert summary["executions_per_backend"] == {"FastBackend": 1}

    def test_telemetry_not_part_of_result_hash(self):
        router = BackendRouter(
            candidates=[_SlowBackend(), _FastBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        result = router.execute("calculate_returns", {"prices": _prices(200)})

        # result_hash covers operation/backend/version/input/output only — the
        # scheduling decision and timings are observational and excluded.
        from researchos.quant_engine.backend_hash import (
            compute_backend_result_hash,
            compute_input_hash,
        )

        recomputed = compute_backend_result_hash(
            result.metadata.operation,
            result.metadata.backend,
            result.metadata.version,
            compute_input_hash({"prices": _prices(200)}),
            result.output,
        )
        assert result.metadata.result_hash == recomputed


class TestRecalibration:
    def test_recalibrate_learns_from_history(self):
        router = BackendRouter(
            candidates=[_FastBackend(), _SlowBackend()],
            scheduler=BackendScheduler(profile=_profile_for("calculate_returns")),
        )
        for _ in range(3):
            router.execute("calculate_returns", {"prices": _prices(200)})

        new_profile = router.recalibrate_profile(version="2.0.0")
        assert new_profile is not None
        assert new_profile.version == "2.0.0"
        assert new_profile.measured() > 0
        # The recalibrated profile now contains history entries for both backends.
        assert new_profile.estimate_ms("FastBackend", "calculate_returns", DatasetSizeClass.SMALL) is not None

    def test_recalibration_is_explicit_and_versioned(self):
        router = BackendRouter(candidates=[_FastBackend()])
        router.execute("calculate_returns", {"prices": _prices(200)})
        p1 = router.recalibrate_profile()
        p2 = router.recalibrate_profile()
        assert p1 is not None and p2 is not None
        assert p1.version != p2.version


class TestExperimentPropagation:
    def test_scheduling_stats_recorded(self):
        router = BackendRouter(candidates=[_FastBackend()])
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        _, result = runner.run(exp, _prices(252))

        assert result.statistics["backend_id"] == "FastBackend"
        assert result.statistics["backend_fallback_count"] == 0
        assert result.statistics["backend_attempted_backends"] == []
        # No scheduler configured → policy/profile versions are empty strings.
        assert result.statistics["backend_policy_version"] == ""
        assert result.statistics["backend_profile_version"] == ""
        assert result.statistics["backend_scheduler_decision"]["selected_backend"] == "FastBackend"

    def test_fallback_stats_recorded(self):
        router = BackendRouter(candidates=[_RaisingBackend(), _FastBackend()])
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        _, result = runner.run(exp, _prices(252))

        assert result.statistics["backend_id"] == "FastBackend"
        assert result.statistics["backend_fallback_count"] == 1
        assert result.statistics["backend_attempted_backends"] == ["RaisingBackend"]

    def test_duration_observational_not_hashed(self):
        router = BackendRouter(candidates=[_FastBackend()])
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        _, result = runner.run(exp, _prices(252))

        assert result.backend_execution_time_ms > 0.0
        hashed = result._to_hashable_dict()
        assert "backend_execution_time_ms" not in hashed
        assert "backend_execution_timestamp" not in hashed

    def test_deterministic_result_hash_with_scheduler(self):
        router = BackendRouter(
            candidates=[_SlowBackend(), _FastBackend()],
            scheduler=BackendScheduler(profile=_profile_for("run_simulation")),
        )
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()

        _, r1 = runner.run(exp, _prices(252))
        _, r2 = runner.run(exp, _prices(252))
        assert r1.result_hash == r2.result_hash
        assert r1.statistics == r2.statistics
        assert r1.statistics["backend_id"] == "FastBackend"

    def test_roundtrip_preserves_telemetry(self):
        router = BackendRouter(candidates=[_FastBackend()])
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        _, result = runner.run(exp, _prices(252))

        restored = ExperimentResult.from_dict(result.to_dict())
        assert restored.backend_execution_time_ms == result.backend_execution_time_ms
        assert restored.statistics["backend_fallback_count"] == result.statistics["backend_fallback_count"]
