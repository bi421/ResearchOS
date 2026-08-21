"""
Tests: BackendScheduler — deterministic, profile-driven candidate selection.

Phase 4.4: intelligent backend scheduling & production hardening.

Covers:
    - dataset-size classification (deterministic binning)
    - operation complexity classification
    - certified performance profile (add / estimate / faster_than /
      from_benchmark / roundtrip / recalibrate)
    - scheduler decision logic (pure, deterministic; profile-less fallback)
    - execution history / telemetry aggregation
"""

from __future__ import annotations

import pytest

from researchos.quant_engine.scheduler import (
    OPERATION_COMPLEXITY,
    POLICY_VERSION,
    BackendScheduler,
    CertifiedPerformanceProfile,
    DatasetSizeClass,
    ExecutionHistory,
    ExecutionRecord,
    OperationComplexity,
    PerformanceStat,
    SchedulerDecision,
    classify_size,
    estimate_dataset_size,
    operation_complexity,
)


class TestDatasetSizeClass:
    def test_boundaries(self):
        assert classify_size(None) == DatasetSizeClass.SMALL
        assert classify_size(0) == DatasetSizeClass.SMALL
        assert classify_size(1_000) == DatasetSizeClass.SMALL
        assert classify_size(1_001) == DatasetSizeClass.MEDIUM
        assert classify_size(10_000) == DatasetSizeClass.MEDIUM
        assert classify_size(10_001) == DatasetSizeClass.LARGE

    def test_custom_thresholds(self):
        assert classify_size(500, (1000, 5000)) == DatasetSizeClass.SMALL
        assert classify_size(1500, (1000, 5000)) == DatasetSizeClass.MEDIUM
        assert classify_size(9000, (1000, 5000)) == DatasetSizeClass.LARGE

    def test_deterministic(self):
        for n in (0, 7, 999, 1000, 1001, 5000, 10_000, 10_001, 10_000_000):
            assert classify_size(n) == classify_size(n)


class TestOperationComplexity:
    def test_known_mappings(self):
        assert operation_complexity("calculate_returns") == OperationComplexity.LIGHT
        assert operation_complexity("calculate_volatility") == OperationComplexity.STANDARD
        assert operation_complexity("run_simulation") == OperationComplexity.HEAVY
        assert operation_complexity("calculate_metrics") == OperationComplexity.HEAVY

    def test_unknown_defaults_to_standard(self):
        assert operation_complexity("no_such_op") == OperationComplexity.STANDARD

    def test_all_quant_ops_classified(self):
        from researchos.quant_engine.capabilities import QUANT_OPERATIONS

        for op in QUANT_OPERATIONS:
            assert op in OPERATION_COMPLEXITY


class TestSizeEstimation:
    def test_price_list(self):
        assert estimate_dataset_size({"prices": [1.0] * 100}) == 100

    def test_simulation_inputs(self):
        assert estimate_dataset_size({"request": object(), "dataset": [1.0] * 250}) == 250

    def test_no_sequence_is_none(self):
        assert estimate_dataset_size({"request": object(), "dataset": None}) is None
        assert estimate_dataset_size({"a": 1}) is None

    def test_structured_dataset_no_length_is_none(self):
        class _NoLen:
            pass

        assert estimate_dataset_size({"dataset": _NoLen()}) is None


class TestPerformanceStat:
    def test_roundtrip(self):
        stat = PerformanceStat(mean_ms=12.5, count=3, last_ms=10.0)
        assert PerformanceStat.from_dict(stat.to_dict()) == stat

    def test_from_measurement(self):
        stat = PerformanceStat.from_measurement(3.5)
        assert stat.mean_ms == 3.5
        assert stat.count == 1
        assert stat.last_ms == 3.5


class TestCertifiedPerformanceProfile:
    def test_estimate_unknown_is_none(self):
        profile = CertifiedPerformanceProfile()
        assert profile.estimate_ms("BackendA", "calculate_returns", DatasetSizeClass.SMALL) is None

    def test_add_and_estimate(self):
        profile = CertifiedPerformanceProfile()
        stat = PerformanceStat(mean_ms=1.0)
        updated = profile.add("BackendA", "calculate_returns", DatasetSizeClass.SMALL, stat)
        assert profile.estimate_ms("BackendA", "calculate_returns", DatasetSizeClass.SMALL) is None
        assert updated.estimate_ms("BackendA", "calculate_returns", DatasetSizeClass.SMALL) == 1.0

    def test_immutable_add_returns_new_profile(self):
        profile = CertifiedPerformanceProfile()
        updated = profile.add("A", "op", DatasetSizeClass.SMALL, PerformanceStat(1.0))
        assert updated is not profile
        assert updated.measured() == 1
        assert profile.measured() == 0

    def test_faster_than(self):
        profile = CertifiedPerformanceProfile().add("Fast", "op", DatasetSizeClass.LARGE, PerformanceStat(5.0)).add("Slow", "op", DatasetSizeClass.LARGE, PerformanceStat(50.0))
        assert profile.faster_than("op", DatasetSizeClass.LARGE, "Fast", "Slow") is True
        assert profile.faster_than("op", DatasetSizeClass.LARGE, "Slow", "Fast") is False

    def test_faster_than_unknown_is_false(self):
        profile = CertifiedPerformanceProfile().add("Fast", "op", DatasetSizeClass.SMALL, PerformanceStat(5.0))
        assert profile.faster_than("op", DatasetSizeClass.LARGE, "Fast", "Slow") is False

    def test_roundtrip(self):
        profile = CertifiedPerformanceProfile().add("A", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(2.5)).add("B", "run_simulation", DatasetSizeClass.LARGE, PerformanceStat(50.0))
        restored = CertifiedPerformanceProfile.from_dict(profile.to_dict())
        assert restored.version == profile.version
        assert restored.source == profile.source
        assert restored.thresholds == profile.thresholds
        assert restored.measured() == profile.measured()
        assert restored.estimate_ms("A", "calculate_returns", DatasetSizeClass.SMALL) == 2.5

    def test_from_benchmark(self):
        rows = [
            {
                "operation": "calculate_returns",
                "measurements": [
                    {"size": 1000, "python_s": 0.001, "cpp_s": 0.0005, "speedup": 2.0},
                    {"size": 100000, "python_s": 0.010, "cpp_s": 0.005, "speedup": 2.0},
                ],
            }
        ]
        profile = CertifiedPerformanceProfile.from_benchmark(rows, backend_name="CppQuantAdapter", reference_backend_name="PythonQuantBackend")
        # 1 operation × 2 sizes × 2 backends
        assert profile.measured() == 4
        cpp_small = profile.estimate_ms("CppQuantAdapter", "calculate_returns", DatasetSizeClass.SMALL)
        py_large = profile.estimate_ms("PythonQuantBackend", "calculate_returns", DatasetSizeClass.LARGE)
        assert cpp_small == pytest.approx(0.5)
        assert py_large == pytest.approx(10.0)

    def test_recalibrate_bumps_version(self):
        history = ExecutionHistory()
        history.record(
            ExecutionRecord(
                operation="calculate_returns",
                backend="A",
                size_class="small",
                duration_ms=8.0,
                validation_status="passed",
                error_code="ok",
            )
        )
        profile = CertifiedPerformanceProfile(version="1.0.0", source="benchmark").add("A", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(4.0, count=2))
        new_profile = profile.recalibrate(history)
        assert new_profile.version == "1.0.0.1"
        assert new_profile is not profile
        # (4.0*2 + 8.0) / 3 == 5.333...
        est = new_profile.estimate_ms("A", "calculate_returns", DatasetSizeClass.SMALL)
        assert est == pytest.approx((4.0 * 2 + 8.0) / 3)

    def test_recalibrate_with_explicit_version(self):
        history = ExecutionHistory()
        profile = CertifiedPerformanceProfile(version="0", source="x")
        assert profile.recalibrate(history, version="2.0.0").version == "2.0.0"


class TestBackendScheduler:
    def test_no_profile_selects_first(self):
        scheduler = BackendScheduler()
        decision = scheduler.decide(
            "calculate_returns",
            {"prices": [1.0] * 100},
            [("A", object()), ("B", object())],
        )
        assert decision.selected_backend == "A"
        assert decision.policy_version == POLICY_VERSION
        assert decision.profile_version == ""

    def test_profile_selects_fastest(self):
        profile = (
            CertifiedPerformanceProfile().add("Slow", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(50.0)).add("Fast", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(5.0))
        )
        scheduler = BackendScheduler(profile=profile)
        decision = scheduler.decide(
            "calculate_returns",
            {"prices": [1.0] * 100},
            [("Slow", object()), ("Fast", object())],
        )
        assert decision.selected_backend == "Fast"
        assert decision.profile_version == profile.version
        rejected_name, rejected_reason = decision.rejected_reasons[0]
        assert rejected_name == "Slow"
        assert rejected_reason.startswith("estimated slower")

    def test_no_measurements_for_size_selects_first(self):
        profile = CertifiedPerformanceProfile().add("Fast", "calculate_returns", DatasetSizeClass.SMALL, PerformanceStat(5.0))
        scheduler = BackendScheduler(profile=profile)
        # LARGE dataset has no measurements → first eligible wins.
        decision = scheduler.decide(
            "calculate_returns",
            {"prices": [1.0] * 100_000},
            [("A", object()), ("B", object())],
        )
        assert decision.selected_backend == "A"

    def test_empty_eligible(self):
        scheduler = BackendScheduler()
        decision = scheduler.decide("op", {}, [])
        assert decision.selected_backend is None
        assert "reference" in decision.rationale

    def test_decision_roundtrip(self):
        decision = SchedulerDecision(
            selected_backend="Fast",
            rationale="chose Fast",
            policy_version="1.0.0",
            profile_version="3",
            candidates_considered=("Slow", "Fast"),
            rejected_reasons=(("Slow", "estimated slower"),),
        )
        restored = SchedulerDecision.from_dict(decision.to_dict())
        assert restored == decision

    def test_deterministic_decision(self):
        profile = CertifiedPerformanceProfile().add("A", "op", DatasetSizeClass.MEDIUM, PerformanceStat(1.0)).add("B", "op", DatasetSizeClass.MEDIUM, PerformanceStat(2.0))
        scheduler = BackendScheduler(profile=profile)
        inputs = {"prices": [1.0] * 5_000}
        d1 = scheduler.decide("op", inputs, [("A", object()), ("B", object())])
        d2 = scheduler.decide("op", inputs, [("A", object()), ("B", object())])
        assert d1.selected_backend == d2.selected_backend == "A"
        assert d1.to_dict() == d2.to_dict()


class TestExecutionHistory:
    def test_record_and_summary(self):
        history = ExecutionHistory()
        history.record(ExecutionRecord("op1", "A", "small", 1.0, "passed", "ok"))
        history.record(ExecutionRecord("op1", "B", "small", 2.0, "passed", "ok", fallback_count=1))
        summary = history.summary()
        assert summary["total_executions"] == 2
        assert summary["total_fallbacks"] == 1
        assert summary["total_duration_ms"] == 3.0
        assert summary["executions_per_backend"] == {"A": 1, "B": 1}

    def test_roundtrip(self):
        history = ExecutionHistory()
        history.record(ExecutionRecord("op", "A", "large", 9.0, "passed", "ok"))
        restored = ExecutionHistory.from_dict(history.to_dict())
        assert len(restored) == 1
        assert restored.records[0].operation == "op"
        assert restored.records[0].size_class == "large"
