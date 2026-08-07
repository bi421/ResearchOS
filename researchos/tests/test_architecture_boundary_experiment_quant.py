"""
Architecture Boundary Guard Tests — Experiment Framework ↔ Quant Computation Engine.

Freeze enforcement for the architectural boundary:

    Data Engine
        ↓
    Dataset / Historical Data Contract
        ↓
    QuantComputationInterface
        ↓
    PythonQuantBackend
        ↓
    ExperimentRunner
        ↓
    ExperimentResult

These tests are PERMANENT REGRESSION GUARDS, not features. They prevent any
future change from re-introducing:

    - OHLCV / Candle / price-extraction logic into the Experiment Framework
    - RNG state or random calls in the experiment execution path
    - Fake metric generation / synthetic simulation outputs
    - Knowledge of broker / exchange / vendor market data formats

Design notes (avoiding false positives):
    - AST-based source guards parse the *executable* source of the runner and
      strip docstrings/comments before scanning for forbidden patterns.
    - Runtime guards verify *behavior* (determinism, provenance, backend
      ownership) rather than only implementation details.
"""

from __future__ import annotations

import ast
import inspect
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.runner import BaseExperimentRunner
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)

RUNNER_PATH = Path(inspect.getfile(BaseExperimentRunner)).resolve()
BACKEND_PATH = Path(inspect.getfile(PythonQuantBackend)).resolve()


# ─────────────────────────────────────────────────────────────────────────────
# Static helpers (AST-based source scanning)
# ─────────────────────────────────────────────────────────────────────────────

def _executable_source(path: Path) -> str:
    """Return the module source with docstrings and comments stripped.

    This avoids false positives from documentation strings and comment lines
    while still scanning every executable statement in the file.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        # Remove docstrings (module, class, function level).
        if (
            isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and ast.get_docstring(node) is not None
        ):
            ast.get_docstring(node, clean=False)
            # Remove the string literal node(s) used as the docstring.
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    body.pop(0)
                elif isinstance(body[0].value.value, tuple):  # implicit concatenation
                    pass
    # Re-generate source from the cleaned tree.
    cleaned = ast.unparse(tree)
    return cleaned


def _forbidden_import(path: Path, forbidden: List[str]) -> List[str]:
    """Return forbidden import/from-import module names found in the file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name == f or alias.name.startswith(f + ".") for f in forbidden):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod == f or mod.startswith(f + ".") for f in forbidden):
                hits.append(mod)
    return sorted(set(hits))


def _forbidden_tokens(source: str, tokens: List[str]) -> List[str]:
    """Return forbidden identifier/attribute tokens present in executable source."""
    return [t for t in tokens if t in source]


# ─────────────────────────────────────────────────────────────────────────────
# TEST-001: ExperimentRunner cannot access OHLCV parsing logic
# ─────────────────────────────────────────────────────────────────────────────

class TestRunnerNoOhlcvKnowledge:
    """ExperimentRunner must be orchestration-only and MUST NOT know OHLCV."""

    def test_runner_has_no_data_engine_import(self):
        """runner.py must not import from researchos.data_engine."""
        forbidden = ["researchos.data_engine", "researchos.data_engine.dataset",
                     "researchos.data_engine.candle"]
        hits = _forbidden_import(RUNNER_PATH, forbidden)
        assert hits == [], f"ExperimentRunner imports data_engine symbols: {hits}"

    def test_runner_executable_source_has_no_ohlcv_field_access(self):
        """No .open/.high/.low/.close/.volume attribute access outside docstrings."""
        source = _executable_source(RUNNER_PATH)
        tokens = [".open", ".high", ".low", ".close", ".volume", "OHLCV",
                  "historical", "HistoricalDataset", "Candle", "records"]
        hits = _forbidden_tokens(source, tokens)
        assert hits == [], f"OHLCV/record-field patterns found in runner source: {hits}"

    def test_runner_has_no_price_extraction_helper(self):
        """_extract_prices and friends must not exist in the runner."""
        runner = BaseExperimentRunner()
        forbidden = [name for name in dir(runner) if "price" in name.lower() or "extract" in name.lower()]
        assert forbidden == [], f"Price-extraction helpers found on runner: {forbidden}"

    def test_runner_forwards_raw_dataset_contract(self):
        """The runner must pass the dataset contract through unchanged."""
        captured: Dict[str, Any] = {}

        class RecordingBackend(PythonQuantBackend):
            def run_simulation(self, request, dataset, calculation_version=CalculationVersion.CALCULATION_V1, strategy=None):
                captured["dataset"] = dataset
                captured["request"] = request
                return super().run_simulation(request, dataset, calculation_version, strategy)

        runner = BaseExperimentRunner(backend=RecordingBackend())
        exp = _make_experiment()
        contract = _make_dataset_contract()

        runner.run(exp, contract)

        assert captured["dataset"] is contract  # unchanged reference
        assert isinstance(captured["request"], SimulationRequest)


# ─────────────────────────────────────────────────────────────────────────────
# TEST-002: ExperimentRunner has no RNG dependency
# ─────────────────────────────────────────────────────────────────────────────

class TestRunnerNoRngDependency:
    """ExperimentRunner must not import random, own RNG state, or call RNG."""

    def test_runner_has_no_random_import(self):
        """random must not be imported in runner.py."""
        hits = _forbidden_import(RUNNER_PATH, ["random"])
        assert hits == [], f"random imported in runner: {hits}"

    def test_runner_executable_source_has_no_rng_patterns(self):
        """No random.Random / .uniform / randint / choice / shuffle / random() calls."""
        source = _executable_source(RUNNER_PATH)
        tokens = ["random.", "_rng", "Random(", "uniform(", "randint(", "choice(", "shuffle(", "np.random"]
        hits = _forbidden_tokens(source, tokens)
        assert hits == [], f"RNG patterns found in runner source: {hits}"

    def test_runner_has_no_rng_state_attribute(self):
        """BaseExperimentRunner instances must not hold an RNG state attribute."""
        runner = BaseExperimentRunner()
        attrs = [k for k in vars(runner).keys() if "rng" in k.lower() or "random" in k.lower()]
        assert attrs == [], f"Hidden RNG state on runner: {attrs}"

    def test_experiment_execution_is_rng_free(self, monkeypatch):
        """Running an experiment must never touch the random module."""
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("random module accessed during experiment execution")

        for name in ("random", "uniform", "randint", "randrange", "choice",
                     "shuffle", "sample", "gauss", "normalvariate", "Random", "seed"):
            monkeypatch.setattr(random, name, _raise, raising=False)

        runner = BaseExperimentRunner()
        exp = _make_experiment()
        run, result = runner.run(exp, _prices())

        assert run.status.value == "Completed"
        assert len(result.metrics) > 0


# ─────────────────────────────────────────────────────────────────────────────
# TEST-003: Backend produces deterministic result_hash
# ─────────────────────────────────────────────────────────────────────────────

class TestBackendDeterminism:
    """PythonQuantBackend must produce identical hashes for identical inputs."""

    def test_backend_stateless(self):
        """Backend instance must hold no RNG / hidden mutable random state."""
        backend = PythonQuantBackend()
        assert not any("rng" in k.lower() or "random" in k.lower() for k in vars(backend))

    def test_backend_deterministic_result_hash(self):
        backend = PythonQuantBackend()
        request = SimulationRequest(dataset_reference="det", parameters={"initial_capital": 100000.0}, seed=42)
        prices = _prices()
        r1: SimulationResult = backend.run_simulation(request, prices)
        r2: SimulationResult = backend.run_simulation(request, prices)
        assert r1.result_hash == r2.result_hash
        assert r1.metrics == r2.metrics
        assert r1.statistics == r2.statistics
        assert r1.equity_curve == r2.equity_curve

    def test_backend_rng_free(self, monkeypatch):
        """Backend simulation must not call random even with monkeypatched raising."""
        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("random accessed in backend computation")

        for name in ("random", "uniform", "randint", "choice", "gauss", "Random"):
            monkeypatch.setattr(random, name, _raise, raising=False)

        backend = PythonQuantBackend()
        request = SimulationRequest(dataset_reference="rng", seed=1)
        result = backend.run_simulation(request, _prices())
        assert result.result_hash


# ─────────────────────────────────────────────────────────────────────────────
# TEST-004: Same dataset + same configuration = identical result
# ─────────────────────────────────────────────────────────────────────────────

class TestSameInputsSameResult:
    """Identical dataset + configuration must yield identical ExperimentResult."""

    def test_same_dataset_same_config_identical_result(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        r1, res1 = runner.run(exp, _prices())
        r2, res2 = runner.run(exp, _prices())
        assert r1.result_hash == r2.result_hash
        assert res1.result_hash == res2.result_hash
        assert res1.metrics == res2.metrics

    def test_same_contract_same_result(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        contract = _make_dataset_contract()
        _, res1 = runner.run(exp, contract)
        _, res2 = runner.run(exp, contract)
        assert res1.result_hash == res2.result_hash


# ─────────────────────────────────────────────────────────────────────────────
# TEST-005: Different dataset = different result
# ─────────────────────────────────────────────────────────────────────────────

class TestDifferentDatasetDifferentResult:
    """Changing the dataset must change the computed result."""

    def test_different_prices_different_result(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        _, up = runner.run(exp, _prices(drift=0.001))
        _, down = runner.run(exp, _prices(drift=-0.001))
        assert up.result_hash != down.result_hash
        assert up.metrics != down.metrics

    def test_different_input_hash_on_change(self):
        backend = PythonQuantBackend()
        req_a = SimulationRequest(dataset_reference="A", seed=42)
        req_b = SimulationRequest(dataset_reference="B", seed=42)
        res_a = backend.run_simulation(req_a, _prices())
        res_b = backend.run_simulation(req_b, _prices())
        assert res_a.input_hash != res_b.input_hash
        assert res_a.result_hash != res_b.result_hash


# ─────────────────────────────────────────────────────────────────────────────
# TEST-006: ExperimentResult contains required provenance fields
# ─────────────────────────────────────────────────────────────────────────────

class TestExperimentResultProvenance:
    """Every ExperimentResult must preserve full computation provenance."""

    def test_result_contains_all_provenance_fields(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        run, result = runner.run(exp, _prices())

        stats = result.statistics
        assert stats["computation_backend"] == "PythonQuantBackend"
        assert stats["calculation_version"] == "CALCULATION_V1"
        assert stats["input_hash"]
        assert stats["result_hash"]
        assert stats["simulation_id"].startswith("sim_")
        assert stats["dataset_reference"] == "integration_source"
        # Issue #5: dataset_version is now a real content hash, not "1.0.0".
        assert stats["dataset_version"] != "1.0.0"
        assert len(stats["dataset_version"]) == 64  # sha256 hex
        assert stats["seed"] == 42
        assert stats["run_number"] == 1

        # Metrics / statistics / performance metadata
        assert len(result.metrics) > 0
        assert len(result.statistics) > 0

        # Equity curve + returns metadata
        assert "equity_curve" in result.metadata
        assert "returns" in result.metadata
        assert len(result.metadata["equity_curve"]) > 0
        assert len(result.metadata["returns"]) > 0

    def test_backtest_artifacts_preserved(self):
        """Mode B backtest artifacts flow into the ExperimentResult."""
        exp = Experiment(
            hypothesis_id="hyp_backtest",
            name="Backtest Provenance",
            dataset_config=DatasetConfig(source="backtest_source"),
            simulation_config=SimulationConfig(
                seed=42,
                initial_capital=100_000.0,
                commission="fixed:10.0",
                slippage="fixed:0.01",
                parameters={"mode": "backtest", "position_size": 100.0},
            ),
        )
        exp.mark_ready()
        runner = BaseExperimentRunner()
        prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0, 108.0, 110.0, 112.0]
        _, result = runner.run(exp, prices)

        assert len(result.trades) == 1
        assert len(result.signals) == 2
        assert len(result.metadata["positions"]) == len(prices)
        assert result.metadata["execution_stats"]["num_fills"] == 2
        assert result.metadata["execution_stats"]["num_trades"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures / helpers
# ─────────────────────────────────────────────────────────────────────────────

def _prices(n: int = 252, base: float = 100.0, drift: float = 0.0001) -> List[float]:
    """Deterministic synthetic price series."""
    return [base * (1.0 + drift * i) for i in range(n)]


def _make_dataset_contract() -> List[Dict[str, Any]]:
    """A list-of-dicts OHLCV-style dataset contract (backend must normalize)."""
    out: List[Dict[str, Any]] = []
    ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(252):
        out.append({
            "timestamp": ts,
            "open": price,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": 1000 + i,
        })
        price *= 1.0001
        ts = ts.replace(day=ts.day + 1) if ts.day < 28 else ts.replace(month=ts.month + 1, day=1)
    return out


def _make_experiment(name: str = "Boundary Test") -> Experiment:
    exp = Experiment(
        hypothesis_id="hyp_boundary",
        name=name,
        dataset_config=DatasetConfig(source="integration_source"),
        simulation_config=SimulationConfig(seed=42, initial_capital=100_000.0),
    )
    exp.mark_ready()
    return exp

