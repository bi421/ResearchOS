"""
Tests for Phase 5.3c Step 2 — Lineage Query Engine.

Covers the read-only lineage query layer over the ``EvidenceRepository``
lineage graph:

1. Dataset → Experiment → Run → Result → Validation chain resolution
2. ancestors traversal
3. descendants traversal
4. lineage_tree structure
5. explain output completeness
6. resolve_reference correctness
7. resolve_full_chain correctness
8. missing artifact handling
9. cycle protection
10. deterministic output ordering

Verification requirements:
    - read-only: no mutation of the repository / no new artifact emission
    - deterministic output ordering (sorted by artifact_hash)
    - cycle-safe traversal
    - missing artifact → empty / None results
"""

from __future__ import annotations

from researchos.evidence.envelope import (
    build_envelope,
)
from researchos.evidence.lineage import (
    LineageQueryEngine,
)
from researchos.evidence.repository import EvidenceRepository
from researchos.storage.repository import ResearchRepository


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


def _chain_payloads() -> dict:
    """Return deterministic payloads for a full Dataset → Experiment → Run →
    Result → Validation chain, with the reference keys embedded (as the
    emission modules do)."""
    return {
        "dataset": {
            "feature_names": ["a", "b"],
            "features": [[1.0, 2.0], [3.0, 4.0]],
            "labels": [0.0, 1.0],
            "metadata": {"source": "yahoo"},
            "sample_count": 2,
            "feature_count": 2,
            "label_name": "target",
            "version": "1.0.0",
        },
        "experiment": {
            "experiment_hash": "exp-hash-1",
            "hypothesis_id": "hyp-1",
            "name": "Lineage Test",
            "dataset_config": {"source": "yahoo", "symbols": ["AAPL"]},
            "simulation_config": {"seed": 42},
            "parameters": {"lookback": 20},
            "version": "1.0.0",
            "status": "ready",
        },
        "run": {
            "run_hash": "run-hash-1",
            "experiment_id": "exp-1",
            "experiment_hash": "exp-hash-1",
            "parameters": {"lookback": 20},
            "dataset_config": {"source": "yahoo"},
            "simulation_config": {"seed": 42},
        },
        "result": {
            "result_hash": "result-hash-1",
            "run_id": "run-1",
            "run_hash": "run-hash-1",
            "experiment_hash": "exp-hash-1",
            "metrics": {"sharpe": 1.5},
            "statistics": {"mean": 0.05},
            "performance": {"win_rate": 0.6},
            "metadata": {},
        },
        "validation": {
            "validation_hash": "validation-hash-1",
            "method": "walk_forward",
            "version": "1.0.0",
            "result_hash": "result-hash-1",
            "run_hash": "run-hash-1",
            "experiment_hash": "exp-hash-1",
            "metrics": {"accuracy": 0.8},
            "parameters": {"train_size": 10, "validation_size": 5, "fold_count": 3},
            "metadata": {},
        },
    }


def _build_chain(repo: EvidenceRepository) -> dict:
    """Emit a full Dataset → Experiment → Run → Result → Validation chain and
    return a mapping of name → artifact_hash."""
    payloads = _chain_payloads()

    dataset = build_envelope("Dataset", payloads["dataset"], version="1.0.0")
    experiment = build_envelope(
        "Experiment",
        payloads["experiment"],
        version="1.0.0",
        parent_hashes=[dataset.artifact_hash],
    )
    run = build_envelope(
        "Run",
        payloads["run"],
        version="1.0.0",
        parent_hashes=[experiment.artifact_hash],
    )
    result = build_envelope(
        "Result",
        payloads["result"],
        version="1.0.0",
        parent_hashes=[run.artifact_hash],
    )
    validation = build_envelope(
        "Validation",
        payloads["validation"],
        version="1.0.0",
        parent_hashes=[result.artifact_hash],
    )

    for env in (dataset, experiment, run, result, validation):
        repo.append_artifact(env)

    return {
        "dataset": dataset.artifact_hash,
        "experiment": experiment.artifact_hash,
        "run": run.artifact_hash,
        "result": result.artifact_hash,
        "validation": validation.artifact_hash,
    }


class TestChainResolution:
    def test_full_chain_edges_present(self):
        repo = _make_repo()
        h = _build_chain(repo)
        # Dataset -> Experiment -> Run -> Result -> Validation
        assert h["experiment"] in repo.get_children(h["dataset"])
        assert h["run"] in repo.get_children(h["experiment"])
        assert h["result"] in repo.get_children(h["run"])
        assert h["validation"] in repo.get_children(h["result"])
        # Reverse
        assert h["dataset"] in repo.get_parents(h["experiment"])
        assert h["run"] in repo.get_parents(h["result"])
        assert h["result"] in repo.get_parents(h["validation"])

    def test_resolve_full_chain_returns_all_five(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        chain = engine.resolve_full_chain(h["result"])
        assert chain is not None
        assert chain.dataset is not None
        assert chain.experiment is not None
        assert chain.run is not None
        assert chain.result is not None
        assert chain.validation is not None
        assert chain.dataset.artifact_hash == h["dataset"]
        assert chain.experiment.artifact_hash == h["experiment"]
        assert chain.run.artifact_hash == h["run"]
        assert chain.result.artifact_hash == h["result"]
        assert chain.validation.artifact_hash == h["validation"]


class TestAncestors:
    def test_result_ancestors(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        ans = engine.ancestors(h["result"])
        hashes = {a.artifact_hash for a in ans}
        assert h["dataset"] in hashes
        assert h["experiment"] in hashes
        assert h["run"] in hashes
        # Result itself is not its own ancestor.
        assert h["result"] not in hashes

    def test_validation_ancestors_include_all(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        ans = engine.ancestors(h["validation"])
        hashes = {a.artifact_hash for a in ans}
        assert h["dataset"] in hashes
        assert h["experiment"] in hashes
        assert h["run"] in hashes
        assert h["result"] in hashes

    def test_dataset_has_no_ancestors(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        assert engine.ancestors(h["dataset"]) == ()


class TestDescendants:
    def test_dataset_descendants(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        desc = engine.descendants(h["dataset"])
        hashes = {d.artifact_hash for d in desc}
        assert h["experiment"] in hashes
        assert h["run"] in hashes
        assert h["result"] in hashes
        assert h["validation"] in hashes

    def test_result_descendants(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        desc = engine.descendants(h["result"])
        assert {d.artifact_hash for d in desc} == {h["validation"]}

    def test_validation_has_no_descendants(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        assert engine.descendants(h["validation"]) == ()


class TestLineageTree:
    def test_tree_structure_root_is_requested(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        tree = engine.lineage_tree(h["result"])
        assert tree is not None
        assert tree.node.artifact_hash == h["result"]
        assert tree.node.artifact_type == "Result"
        # Parent chain: Run, Experiment, Dataset
        run_nodes = {p.node.artifact_hash for p in tree.parents}
        assert h["run"] in run_nodes
        # Child chain: Validation
        child_hashes = {c.node.artifact_hash for c in tree.children}
        assert h["validation"] in child_hashes

    def test_tree_recurses_to_dataset(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        tree = engine.lineage_tree(h["result"])
        # Walk down to Dataset via Run -> Experiment -> Dataset.
        run_node = next(p for p in tree.parents if p.node.artifact_hash == h["run"])
        exp_node = next(p for p in run_node.parents if p.node.artifact_hash == h["experiment"])
        dataset_node = next(p for p in exp_node.parents if p.node.artifact_hash == h["dataset"])
        assert dataset_node.node.artifact_type == "Dataset"

    def test_tree_to_dict_is_deterministic(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        t1 = engine.lineage_tree(h["result"]).to_dict()
        t2 = engine.lineage_tree(h["result"]).to_dict()
        assert t1 == t2


class TestExplain:
    def test_explain_target_completeness(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        exp = engine.explain(h["result"])
        assert exp is not None
        assert exp.artifact.artifact_hash == h["result"]
        assert exp.artifact_type == "Result"
        assert len(exp.parents) == 1
        assert exp.parents[0].artifact.artifact_hash == h["run"]
        assert len(exp.children) == 1
        assert exp.children[0].artifact.artifact_hash == h["validation"]

    def test_explain_lineage_path_present(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        exp = engine.explain(h["result"])
        assert set(exp.lineage_path) == {
            h["dataset"],
            h["experiment"],
            h["run"],
            h["result"],
        }

    def test_explain_includes_verified_flag(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        exp = engine.explain(h["result"])
        assert all(p.verified for p in exp.parents)
        assert all(c.verified for c in exp.children)


class TestResolveReference:
    def test_resolve_result_references(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        refs = engine.resolve_reference(h["result"])
        # Result payload references run_hash and experiment_hash.
        assert refs["run_hash"] is not None
        assert refs["run_hash"].artifact_hash == h["run"]
        assert refs["experiment_hash"] is not None
        assert refs["experiment_hash"].artifact_hash == h["experiment"]

    def test_resolve_validation_references(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        refs = engine.resolve_reference(h["validation"])
        assert refs["result_hash"] is not None
        assert refs["result_hash"].artifact_hash == h["result"]
        assert refs["run_hash"] is not None
        assert refs["experiment_hash"] is not None

    def test_resolve_dataset_version(self):
        repo = _make_repo()
        _build_chain(repo)
        engine = LineageQueryEngine(repo)
        # Dataset payload has a "version" key; resolve_reference returns it as
        # dataset_version when present. Build a dedicated payload with it.
        ds_env = build_envelope(
            "Dataset",
            {
                "feature_names": [],
                "features": [],
                "labels": [],
                "metadata": {},
                "sample_count": 0,
                "feature_count": 0,
                "label_name": "t",
                "version": "3.2.1",
            },
        )
        repo.append_artifact(ds_env)
        refs = engine.resolve_reference(ds_env.artifact_hash)
        # The payload uses "version"; dataset_version is a derived reference.
        assert refs["dataset_version"] == "3.2.1"

    def test_resolve_unresolvable_returns_none(self):
        repo = _make_repo()
        # A Result referencing a run_hash that was never stored.
        env = build_envelope(
            "Result",
            {
                "result_hash": "r",
                "run_id": "x",
                "run_hash": "missing-run",
                "experiment_hash": "missing-exp",
                "metrics": {},
                "statistics": {},
                "performance": {},
                "metadata": {},
            },
        )
        repo.append_artifact(env)
        engine = LineageQueryEngine(repo)
        refs = engine.resolve_reference(env.artifact_hash)
        assert refs["run_hash"] is None
        assert refs["experiment_hash"] is None


class TestPath:
    def test_path_between_dataset_and_validation(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        path = engine.path(h["dataset"], h["validation"])
        assert path[0] == h["dataset"]
        assert path[-1] == h["validation"]

    def test_path_is_contiguous_via_edges(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        path = engine.path(h["dataset"], h["result"])
        # Every consecutive pair must share a lineage edge.
        for a, b in zip(path, path[1:]):
            assert b in repo.get_children(a) or a in repo.get_children(b)

    def test_path_missing_artifact_returns_empty(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        assert engine.path(h["dataset"], "missing-hash") == ()

    def test_path_same_node(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        assert engine.path(h["result"], h["result"]) == (h["result"],)


class TestMissingArtifact:
    def test_explain_missing_returns_none(self):
        repo = _make_repo()
        engine = LineageQueryEngine(repo)
        assert engine.explain("missing") is None

    def test_ancestors_missing_returns_empty(self):
        repo = _make_repo()
        engine = LineageQueryEngine(repo)
        assert engine.ancestors("missing") == ()

    def test_descendants_missing_returns_empty(self):
        repo = _make_repo()
        engine = LineageQueryEngine(repo)
        assert engine.descendants("missing") == ()

    def test_lineage_tree_missing_returns_none(self):
        repo = _make_repo()
        engine = LineageQueryEngine(repo)
        assert engine.lineage_tree("missing") is None

    def test_resolve_reference_missing_returns_empty(self):
        repo = _make_repo()
        engine = LineageQueryEngine(repo)
        assert engine.resolve_reference("missing") == {}

    def test_resolve_full_chain_non_result_returns_none(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        # A Dataset hash is not a Result.
        assert engine.resolve_full_chain(h["dataset"]) is None


class TestCycleProtection:
    def test_ancestors_with_cycle_terminates(self):
        repo = _make_repo()
        a = build_envelope("Dataset", {"x": 1})
        b = build_envelope("Feature", {"x": 2}, parent_hashes=[a.artifact_hash])
        repo.append_artifact(a)
        repo.append_artifact(b)
        # Create a cycle: a -> b, b -> a.
        repo.add_lineage_edge(a.artifact_hash, b.artifact_hash)
        repo.add_lineage_edge(b.artifact_hash, a.artifact_hash)
        engine = LineageQueryEngine(repo)
        # Must terminate and return a finite set.
        ans = engine.ancestors(a.artifact_hash)
        assert isinstance(ans, tuple)
        assert len(ans) <= 2

    def test_descendants_with_cycle_terminates(self):
        repo = _make_repo()
        a = build_envelope("Dataset", {"x": 1})
        b = build_envelope("Feature", {"x": 2})
        repo.append_artifact(a)
        repo.append_artifact(b)
        repo.add_lineage_edge(a.artifact_hash, b.artifact_hash)
        repo.add_lineage_edge(b.artifact_hash, a.artifact_hash)
        engine = LineageQueryEngine(repo)
        desc = engine.descendants(a.artifact_hash)
        assert isinstance(desc, tuple)
        assert len(desc) <= 2

    def test_lineage_tree_with_cycle_terminates(self):
        repo = _make_repo()
        a = build_envelope("Dataset", {"x": 1})
        b = build_envelope("Feature", {"x": 2})
        repo.append_artifact(a)
        repo.append_artifact(b)
        repo.add_lineage_edge(a.artifact_hash, b.artifact_hash)
        repo.add_lineage_edge(b.artifact_hash, a.artifact_hash)
        engine = LineageQueryEngine(repo)
        tree = engine.lineage_tree(a.artifact_hash)
        assert tree is not None


class TestDeterministicOrdering:
    def test_ancestors_ordered_by_hash(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        ans = engine.ancestors(h["result"])
        hashes = [a.artifact_hash for a in ans]
        assert hashes == sorted(hashes)

    def test_descendants_ordered_by_hash(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        desc = engine.descendants(h["dataset"])
        hashes = [d.artifact_hash for d in desc]
        assert hashes == sorted(hashes)

    def test_repeated_queries_identical(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine1 = LineageQueryEngine(repo)
        engine2 = LineageQueryEngine(repo)
        assert engine1.explain(h["result"]).to_dict() == engine2.explain(h["result"]).to_dict()
        assert engine1.ancestors(h["result"]) == engine2.ancestors(h["result"])
        assert engine1.lineage_tree(h["result"]).to_dict() == engine2.lineage_tree(h["result"]).to_dict()


class TestReadOnly:
    def test_queries_do_not_mutate_repository(self):
        repo = _make_repo()
        h = _build_chain(repo)
        before_artifacts = repo.count_artifacts()
        before_edges = repo.count_edges()
        engine = LineageQueryEngine(repo)
        engine.explain(h["result"])
        engine.ancestors(h["result"])
        engine.descendants(h["result"])
        engine.lineage_tree(h["result"])
        engine.resolve_reference(h["result"])
        engine.resolve_full_chain(h["result"])
        engine.path(h["dataset"], h["validation"])
        assert repo.count_artifacts() == before_artifacts
        assert repo.count_edges() == before_edges

    def test_queries_do_not_emit_new_artifacts(self):
        repo = _make_repo()
        h = _build_chain(repo)
        engine = LineageQueryEngine(repo)
        engine.resolve_full_chain(h["result"])
        assert repo.count_artifacts() == 5
