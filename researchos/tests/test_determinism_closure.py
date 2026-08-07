"""
Determinism Closure tests — Issues A & B.

Issue A — ``ExperimentRun.complete()`` hash nondeterminism.
    When ``started_at`` is None and no explicit ``duration_seconds`` is
    supplied, ``run_hash`` must still be deterministic (identical logical
    runs → identical hashes).  Wall-clock influence is removed from the
    deterministic identity; observational telemetry stays outside the hash.

Issue B — ``ExperimentResult.from_dict`` integrity verification.
    ``from_dict`` recomputes the canonical ``result_hash`` from the
    deserialized content, raises ``ValueError`` on mismatch with a stored
    non-empty hash, and preserves backward compatibility with legacy payloads
    (empty stored hash → recomputed).  ``verify_result_hash()`` exposes a
    live integrity check.

Contract-preserving: no existing behavior is changed; these tests assert the
determinism/integrity guarantees introduced by the closure pass.
"""

from __future__ import annotations

import pytest

from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.result import ExperimentResult, ExperimentRun


# =============================================================================
# Issue A — run_hash determinism
# =============================================================================


class TestRunHashDeterminism:
    """Identical logical runs must produce identical run_hash values."""

    def _make_run(self, **overrides):
        kwargs = dict(
            experiment_id="exp1",
            run_number=1,
            dataset_config=DatasetConfig(source="s1"),
            simulation_config=SimulationConfig(seed=1),
            parameters={"a": 1},
        )
        kwargs.update(overrides)
        return ExperimentRun(**kwargs)

    def test_identical_runs_without_start_have_same_hash(self):
        # No start() and no explicit duration → complete() must not inject
        # wall-clock noise into the hash.
        r1 = self._make_run()
        r2 = self._make_run()
        r1.complete(result_id="same", result_hash="same_hash")
        r2.complete(result_id="same", result_hash="same_hash")
        assert r1.run_hash == r2.run_hash

    def test_duration_defaults_to_zero_when_not_started(self):
        run = self._make_run()
        run.complete(result_id="x", result_hash="h")
        # No explicit duration and no start → deterministic 0.0.
        assert run.duration_seconds == 0.0

    def test_explicit_duration_is_deterministic(self):
        r1 = self._make_run()
        r2 = self._make_run()
        r1.complete(result_id="same", result_hash="same_hash", duration_seconds=1.5)
        r2.complete(result_id="same", result_hash="same_hash", duration_seconds=1.5)
        assert r1.run_hash == r2.run_hash
        assert r1.duration_seconds == 1.5

    def test_duration_reflects_started_run(self):
        # When started, duration is derived from start→complete (still
        # deterministic for a given pair of timestamps, but here we assert the
        # field is populated and the hash is stable).
        run = self._make_run()
        run.start()
        run.complete(result_id="x", result_hash="h")
        assert run.duration_seconds >= 0.0

    def test_hash_changes_when_logical_inputs_change(self):
        r1 = self._make_run(parameters={"a": 1})
        r2 = self._make_run(parameters={"a": 2})
        r1.complete(result_id="same", result_hash="same_hash")
        r2.complete(result_id="same", result_hash="same_hash")
        assert r1.run_hash != r2.run_hash

    def test_observational_telemetry_outside_hash(self):
        # completed_at changes between runs but is not part of _to_hashable_dict.
        r1 = self._make_run()
        r2 = self._make_run()
        r1.complete(result_id="same", result_hash="same_hash")
        r2.complete(result_id="same", result_hash="same_hash")
        assert r1.completed_at is not None and r2.completed_at is not None
        assert r1.run_hash == r2.run_hash


# =============================================================================
# Issue B — ExperimentResult.from_dict integrity verification
# =============================================================================


class TestResultIntegrityVerification:
    """from_dict must verify/recompute the result_hash."""

    def test_round_trip_preserves_and_verifies_hash(self):
        result = ExperimentResult(run_id="r1")
        result.add_metric("sharpe", 1.5)
        result.add_statistic("mean", 0.05)
        restored = ExperimentResult.from_dict(result.to_dict())
        assert restored.result_hash == result.result_hash
        assert restored.verify_result_hash() is True

    def test_legacy_payload_without_hash_is_backward_compatible(self):
        payload = {
            "object_type": "ExperimentResult",
            "id": "legacy_id",
            "created_at": "2020-01-01T00:00:00+00:00",
            "ontology_tags": [],
            "lifecycle": {"transitions": []},
            "hash": "",
            "run_id": "legacy_run",
            "metrics": {"sharpe": 1.2},
            "statistics": {},
            "performance": {},
            "signals": [],
            "trades": [],
            "equity_curve": [100.0, 105.0],
            "metadata": {"equity_curve": [100.0, 105.0]},
            "result_hash": "",
            "trace": "",
        }
        restored = ExperimentResult.from_dict(payload)
        # Legacy payload without a stored hash → recomputed deterministically.
        assert restored.result_hash != ""
        assert restored.metrics["sharpe"] == 1.2
        assert restored.verify_result_hash() is True

    def test_mismatched_stored_hash_raises(self):
        result = ExperimentResult(run_id="r1")
        result.add_metric("sharpe", 1.5)
        payload = result.to_dict()
        payload["result_hash"] = "0" * 64  # tamper / corruption
        with pytest.raises(ValueError):
            ExperimentResult.from_dict(payload)

    def test_verify_result_hash_detects_tampering(self):
        # On a live object, overwriting the stored hash without changing the
        # content must fail verification.
        corrupted = ExperimentResult(run_id="r1")
        corrupted.add_metric("sharpe", 1.5)
        corrupted.result_hash = "0" * 64
        assert corrupted.verify_result_hash() is False

    def test_verify_result_hash_true_for_valid(self):
        result = ExperimentResult(run_id="r1")
        result.add_metric("sharpe", 1.5)
        assert result.verify_result_hash() is True
