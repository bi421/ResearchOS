"""
Tests for Phase 5.3c Step 3 — Reproduction Engine.

Covers the deterministic reproduction of a certified Result artifact through
the certified ``BaseExperimentRunner`` boundary:

1. full Dataset → Experiment → Run → Result reproduction success
2. identical result_hash
3. missing dataset (typed MissingArtifact)
4. tampered artifact (typed IntegrityFailure)
5. invalid payload reconstruction (typed ReconstructionFailure)
6. hash mismatch detection (typed HashMismatch)
7. deterministic reproduction report
8. no repository mutation
9. validation chain preserved

Verification requirements:
    - reproduced result_hash equals original result_hash on success
    - typed failures are raised (no generic exceptions) for expected modes
    - reproduction is read-only w.r.t. the evidence repository
    - validation lineage is preserved and reported
    - deterministic report output for identical inputs
"""

from __future__ import annotations

import pytest

from researchos.evidence.dataset_emission import (
    build_dataset_envelope,
    emit_dataset,
)
from researchos.evidence.envelope import build_envelope
from researchos.evidence.experiment_emission import (
    build_experiment_envelope,
    emit_experiment_with_dataset,
)
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.reproduction import (
    ExecutionFailure,
    HashMismatch,
    IntegrityFailure,
    MissingArtifact,
    ReconstructionFailure,
    ReproductionEngine,
    ReproductionError,
    ReproductionReport,
    research_dataset_to_runner_dataset,
)
from researchos.evidence.result_emission import (
    build_result_envelope,
    emit_result_for_run,
)
from researchos.evidence.run_emission import (
    build_run_envelope,
    emit_run_for_experiment,
)
from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.runner import BaseExperimentRunner
from researchos.quant_engine.machine_learning.dataset_contracts import (
    ResearchDataset,
)
from researchos.storage.repository import ResearchRepository


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


def _make_dataset() -> ResearchDataset:
    # A 252-row dataset (each row is a feature vector whose first element is
    # treated as the close price via ``research_dataset_to_runner_dataset``).
    rows = [100.0 * (1.0 + 0.0001 * i) for i in range(252)]
    return ResearchDataset(
        feature_names=("close", "volume"),
        features=[(close, 1000.0 + i) for i, close in enumerate(rows)],
        labels=tuple(0.0 for _ in rows),
        metadata={"source": "yahoo", "symbol": "AAPL"},
        sample_count=len(rows),
        feature_count=2,
        label_name="target",
        version="1.0.0",
    )


def _runner_dataset() -> list:
    """Return the OHLCV list-of-dicts the runner/backend consume directly."""
    return research_dataset_to_runner_dataset(_make_dataset())


def _make_experiment() -> Experiment:
    exp = Experiment(
        hypothesis_id="hyp-1",
        name="Reproduction Test",
        experiment_type="Backtest",
        dataset_config=DatasetConfig(source="s1", symbols=["AAPL"]),
        simulation_config=SimulationConfig(seed=42, initial_capital=100000.0),
        parameters={"lookback": 20},
        version="1.0.0",
    )
    exp.mark_ready()
    return exp


def _build_full_chain(
    repo: EvidenceRepository,
) -> dict:
    """Build a full, verified Dataset→Experiment→Run→Result→Validation chain
    with a real runner execution, so the original result_hash matches what a
    reproduction will produce.

    The runner consumes the OHLCV list-of-dicts contract; the ``ResearchDataset``
    is emitted as the Dataset evidence artifact. Both are derived from the same
    ``_make_dataset()`` source so ``research_dataset_to_runner_dataset`` (which
    the ReproductionEngine uses) rebuilds exactly the runner dataset.

    Returns a mapping of name → artifact_hash plus the emitted objects.
    """
    dataset = _make_dataset()
    experiment = _make_experiment()

    # Execute through the certified runner to obtain a canonical result.
    runner = BaseExperimentRunner()
    run, result = runner.run(experiment, _runner_dataset())

    # Emit Dataset.
    ds_env = emit_dataset(build_dataset_envelope(dataset), repo)

    # Emit Experiment, linked to Dataset.
    exp_env = emit_experiment_with_dataset(experiment, ds_env.artifact_hash, repo)

    # Emit Run, linked to Experiment, carrying backend identity.
    run_env = emit_run_for_experiment(
        run,
        exp_env.artifact_hash,
        repo,
        backend_identity={
            "backend_id": "PythonQuantBackend",
            "backend_version": "1.0.0",
        },
    )

    # Emit Result, linked to Run.
    res_env = emit_result_for_run(
        result,
        run_env.artifact_hash,
        repo,
        experiment_hash=exp_env.artifact_hash,
        backend_identity={
            "backend_id": "PythonQuantBackend",
            "backend_version": "1.0.0",
        },
    )

    # Emit Validation, linked to Result.
    validation_env = build_envelope(
        "Validation",
        {
            "validation_hash": "val-hash-1",
            "method": "walk_forward",
            "version": "1.0.0",
            "result_hash": res_env.artifact_hash,
            "run_hash": run_env.artifact_hash,
            "experiment_hash": exp_env.artifact_hash,
            "metrics": {"accuracy": 0.8},
            "parameters": {"train_size": 10, "validation_size": 5, "fold_count": 3},
            "metadata": {},
        },
        version="1.0.0",
        parent_hashes=[res_env.artifact_hash],
    )
    repo.append_artifact(validation_env)

    return {
        "dataset": ds_env.artifact_hash,
        "experiment": exp_env.artifact_hash,
        "run": run_env.artifact_hash,
        "result": res_env.artifact_hash,
        "validation": validation_env.artifact_hash,
        "result_object": result,
    }


# =========================================================================
# 1. Full-chain reproduction success
# =========================================================================


class TestFullChainReproduction:
    def test_full_chain_reproduction_succeeds(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        engine = ReproductionEngine(repository=repo)
        report = engine.reproduce(chain["result"])
        assert report.success is True
        assert report.original_hash == chain["result"]
        assert report.reproduced_hash != ""
        for typ in ("Dataset", "Experiment", "Run", "Result", "Validation"):
            assert typ in report.artifact_chain
            assert report.artifact_chain[typ] == chain[typ.lower()]
        assert report.verification_errors == []
        assert report.divergence_details == {}

    def test_full_chain_result_hash_identical(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        original_result_hash = chain["result_object"].result_hash

        engine = ReproductionEngine(repository=repo)
        report = engine.reproduce(chain["result"])
        assert report.reproduced_hash == original_result_hash

    def test_reproduction_report_is_deterministic(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        engine = ReproductionEngine(repository=repo)
        r1 = engine.reproduce(chain["result"]).to_dict()
        r2 = engine.reproduce(chain["result"]).to_dict()
        assert r1 == r2


# =========================================================================
# 2. Missing artifact handling
# =========================================================================


class TestMissingArtifact:
    def test_missing_result_hash_raises(self):
        repo = _make_repo()
        engine = ReproductionEngine(repository=repo)
        with pytest.raises(MissingArtifact):
            engine.reproduce("missing-result-hash")

    def test_missing_dataset_raises(self):
        repo = _make_repo()
        experiment = _make_experiment()
        runner = BaseExperimentRunner()
        run, result = runner.run(experiment, _runner_dataset())

        exp_env = build_experiment_envelope(experiment)
        repo.append_artifact(exp_env)
        run_env = build_run_envelope(run)
        run_linked = build_envelope(
            "Run",
            run_env.payload,
            version="1.0.0",
            parent_hashes=[exp_env.artifact_hash],
        )
        repo.append_artifact(run_linked)
        res_env = build_result_envelope(
            result,
            run_hash=run_linked.artifact_hash,
            experiment_hash=exp_env.artifact_hash,
        )
        res_linked = build_envelope(
            "Result",
            res_env.payload,
            version="1.0.0",
            parent_hashes=[run_linked.artifact_hash],
        )
        repo.append_artifact(res_linked)

        engine = ReproductionEngine(repository=repo)
        with pytest.raises(MissingArtifact):
            engine.reproduce(res_linked.artifact_hash)

    def test_missing_run_raises(self):
        repo = _make_repo()
        experiment = _make_experiment()
        runner = BaseExperimentRunner()
        run, result = runner.run(experiment, _runner_dataset())
        ds_env = build_dataset_envelope(_make_dataset())
        repo.append_artifact(ds_env)
        exp_env = build_experiment_envelope(experiment)
        exp_linked = build_envelope(
            "Experiment",
            exp_env.payload,
            version="1.0.0",
            parent_hashes=[ds_env.artifact_hash],
        )
        repo.append_artifact(exp_linked)
        res_env = build_result_envelope(result)
        repo.append_artifact(res_env)
        engine = ReproductionEngine(repository=repo)
        with pytest.raises(MissingArtifact):
            engine.reproduce(res_env.artifact_hash)


# =========================================================================
# 3. Tampered artifact handling
# =========================================================================


class TestTamperedArtifact:
    def test_tampered_dataset_raises_integrity_failure(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        self._tamper_artifact(repo, chain["dataset"], {"tampered": True})
        engine = ReproductionEngine(repository=repo)
        with pytest.raises(IntegrityFailure):
            engine.reproduce(chain["result"])

    def test_tampered_experiment_raises_integrity_failure(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        self._tamper_artifact(repo, chain["experiment"], {"evil": 1})
        engine = ReproductionEngine(repository=repo)
        with pytest.raises(IntegrityFailure):
            engine.reproduce(chain["result"])

    def _tamper_artifact(self, repo, artifact_hash, extra_fields):
        """Tamper with an artifact's stored payload via direct DB update.

        This simulates mutation of the underlying record, which must be
        detected by ``envelope.verify()`` during reproduction.
        """
        conn = repo._repo._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT payload FROM evidence WHERE artifact_hash = ?",
            (artifact_hash,),
        )
        row = cur.fetchone()
        payload = __import__("json").loads(row[0])
        payload.update(extra_fields)
        # Directly corrupt the stored payload WITHOUT updating lineage_hash,
        # so verify() (which recomputes lineage_hash) will fail.
        cur.execute(
            "UPDATE evidence SET payload = ? WHERE artifact_hash = ?",
            (
                __import__("json").dumps(payload, ensure_ascii=False, default=str),
                artifact_hash,
            ),
        )
        conn.commit()


# =========================================================================
# 4. Invalid / missing configuration reconstruction
# =========================================================================


class TestReconstructionFailure:
    def test_payload_without_result_hash_raises(self):
        repo = _make_repo()
        experiment = _make_experiment()
        runner = BaseExperimentRunner()
        run, result = runner.run(experiment, _runner_dataset())
        ds_env = build_dataset_envelope(_make_dataset())
        repo.append_artifact(ds_env)
        exp_env = build_experiment_envelope(experiment)
        exp_linked = build_envelope(
            "Experiment",
            exp_env.payload,
            version="1.0.0",
            parent_hashes=[ds_env.artifact_hash],
        )
        repo.append_artifact(exp_linked)
        run_env = build_run_envelope(run)
        run_linked = build_envelope(
            "Run",
            run_env.payload,
            version="1.0.0",
            parent_hashes=[exp_linked.artifact_hash],
        )
        repo.append_artifact(run_linked)
        # Build a Result envelope with an EMPTY result_hash payload.
        res_payload = {
            "result_hash": "",
            "run_id": run.id,
            "run_hash": run.run_hash,
            "experiment_hash": exp_env.artifact_hash,
            "metrics": {},
            "statistics": {},
            "performance": {},
            "metadata": {},
        }
        res_env = build_envelope(
            "Result",
            res_payload,
            version="1.0.0",
            parent_hashes=[run_linked.artifact_hash],
        )
        repo.append_artifact(res_env)
        engine = ReproductionEngine(repository=repo)
        with pytest.raises(ReconstructionFailure):
            engine.reproduce(res_env.artifact_hash)


# =========================================================================
# 5. Hash mismatch detection
# =========================================================================


class TestHashMismatch:
    def test_result_hash_mismatch_detected(self):
        repo = _make_repo()
        experiment = _make_experiment()
        runner = BaseExperimentRunner()
        run, result = runner.run(experiment, _runner_dataset())
        ds_env = build_dataset_envelope(_make_dataset())
        repo.append_artifact(ds_env)
        exp_env = build_experiment_envelope(experiment)
        exp_linked = build_envelope(
            "Experiment",
            exp_env.payload,
            version="1.0.0",
            parent_hashes=[ds_env.artifact_hash],
        )
        repo.append_artifact(exp_linked)
        run_env = build_run_envelope(run)
        run_linked = build_envelope(
            "Run",
            run_env.payload,
            version="1.0.0",
            parent_hashes=[exp_linked.artifact_hash],
        )
        repo.append_artifact(run_linked)
        # Result payload records a WRONG result_hash (simulating an intended
        # reproduction that would be detected as a divergent outcome).
        wrong_hash = "deadbeef" * 8
        res_payload = {
            "result_hash": wrong_hash,
            "run_id": run.id,
            "run_hash": run.run_hash,
            "experiment_hash": exp_env.artifact_hash,
            "metrics": dict(result.metrics),
            "statistics": dict(result.statistics),
            "performance": dict(result.performance),
            "metadata": dict(result.metadata),
        }
        res_env = build_envelope(
            "Result",
            res_payload,
            version="1.0.0",
            parent_hashes=[run_linked.artifact_hash],
        )
        repo.append_artifact(res_env)
        engine = ReproductionEngine(repository=repo)
        with pytest.raises(HashMismatch):
            engine.reproduce(res_env.artifact_hash)


# =========================================================================
# 9. Validation chain preserved
# =========================================================================


class TestValidationChainPreserved:
    def test_reproduction_preserves_validation_chain(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        engine = ReproductionEngine(repository=repo)
        report = engine.reproduce(chain["result"])
        assert report.artifact_chain["Validation"] == chain["validation"]

    def test_reproduction_does_not_mutate_validation(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        before = repo.get_artifact(chain["validation"]).to_dict()
        engine = ReproductionEngine(repository=repo)
        engine.reproduce(chain["result"])
        after = repo.get_artifact(chain["validation"]).to_dict()
        assert before == after


# =========================================================================
# 8. Repository immutability
# =========================================================================


class TestRepositoryImmutability:
    def test_reproduction_does_not_add_artifacts(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        before = repo.count_artifacts()
        engine = ReproductionEngine(repository=repo)
        engine.reproduce(chain["result"])
        assert repo.count_artifacts() == before

    def test_reproduction_does_not_add_edges(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        before = repo.count_edges()
        engine = ReproductionEngine(repository=repo)
        engine.reproduce(chain["result"])
        assert repo.count_edges() == before

    def test_reproduction_does_not_mutate_evidence_records(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        snapshots = {
            hash_: repo.get_artifact(hash_).to_dict()
            for hash_ in [
                chain["dataset"],
                chain["experiment"],
                chain["run"],
                chain["result"],
            ]
        }
        engine = ReproductionEngine(repository=repo)
        engine.reproduce(chain["result"])
        for hash_, snap in snapshots.items():
            assert repo.get_artifact(hash_).to_dict() == snap


# =========================================================================
# Report contract
# =========================================================================


class TestReproductionReportContract:
    def test_report_is_dataclass_and_immutable(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        engine = ReproductionEngine(repository=repo)
        report = engine.reproduce(chain["result"])
        assert isinstance(report, ReproductionReport)
        with pytest.raises(Exception):
            report.success = False  # type: ignore[misc]

    def test_report_to_dict_roundtrip_keys(self):
        repo = _make_repo()
        chain = _build_full_chain(repo)
        engine = ReproductionEngine(repository=repo)
        report = engine.reproduce(chain["result"])
        d = report.to_dict()
        assert set(d.keys()) == {
            "success",
            "original_hash",
            "reproduced_hash",
            "artifact_chain",
            "verification_errors",
            "divergence_details",
        }
        assert d["success"] is True


# =========================================================================
# Acceptance criteria
# =========================================================================


class TestAcceptanceCriteria:
    def test_acceptance_all_typed_failures_are_subclasses(self):
        assert issubclass(MissingArtifact, ReproductionError)
        assert issubclass(IntegrityFailure, ReproductionError)
        assert issubclass(ReconstructionFailure, ReproductionError)
        assert issubclass(ExecutionFailure, ReproductionError)
        assert issubclass(HashMismatch, ReproductionError)
