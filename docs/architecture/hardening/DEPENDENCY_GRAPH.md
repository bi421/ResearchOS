# DEPENDENCY_GRAPH.md — Machine-Verified Import Graph

**Date:** 2026-08-17
**Method:** AST parse of all 317 Python files in `researchos/` and `macro_intelligence/` (test directories excluded from edge *sources*; package-local tests counted separately). No inference from filenames.

---

## 1. Cross-Package Edges

```
researchos.*  <->  macro_intelligence.*   :  0 edges
```

**This is the definitive proof of the macro split-brain:** not a single import connects the two macro systems. The only textual reference is an unused adapter stub (`researchos/market_memory/integration.py: macro_intelligence_adapter: Optional[Callable] = None`), which imports nothing from the package.

---

## 2. researchos Subpackage DAG (verified edges)

```
researchos.core             -> (nothing)                          [Layer 0]
researchos.objects          -> core                                [Layer 1]
researchos.repository       -> core                                [Layer 1]
researchos.validation       -> core                                [Layer 1]
researchos.decision_engine  -> core                                [Layer 1]
researchos.data_engine      -> core, repository                    [Layer 2]
researchos.storage          -> core, repository, objects           [Layer 2]
researchos.memory           -> core, objects, repository           [Layer 2]
researchos.macro            -> core, objects, repository           [Layer 2]
researchos.market_memory    -> core, repository                    [Layer 2]
researchos.quant_engine     -> core, data_engine                   [Layer 3]
researchos.evidence         -> core, experiments, quant_engine, storage  [Layer 4]
researchos.experiments      -> core, data_engine, quant_engine     [Layer 3]
researchos.pipeline         -> objects, repository                 [Layer 3]
researchos.orchestration    -> quant_engine                        [Layer 4]
researchos.engines          -> core, objects, repository (+ macro) [Layer 3]
researchos.evaluation       -> orchestration, pipeline_repository  [Layer 5]
researchos.pipeline_repository -> orchestration                    [Layer 5]
researchos.agents           -> pipeline, storage, validation       [Layer 6]
researchos.benchmarks       -> quant_engine                        [Layer 6]
researchos (root __init__)  -> core, objects                       [—]
```

**No cycles exist.** The graph is a clean DAG. Two edges deserve attention:

- `quant_engine → data_engine`: the *computation* layer depends on the *data* layer (which hosts asset-specific loaders `xauusd_csv_loader.py`, `xauusd_dataset.py`). Any asset-specific leakage into computation enters here (see CROSS_ASSET_READINESS.md).
- `evidence → experiments, quant_engine`: the certification layer reads certified artifacts from the experiment/quant layers (emission modules), i.e. it is an *observer* of the scientific pipeline, not a peer computation.

---

## 3. External/Isolated Packages (verified)

| Package | Imports from researchos? | Imported by researchos? | Status |
|---------|--------------------------|--------------------------|--------|
| `macro_intelligence/` (90 files) | **No** | **No** | Fully isolated domain library; test-covered (86% overall), runtime-dead |
| `cpp_quant_engine/python/` | No (bridge protocol only) | Dynamically (`research_cpp_backend.py:73` — `import cpp_quant_engine.cpp_quant_backend` inside try/except, falls back to Python reference) | Optional acceleration backend |
| `monitoring/trading/` | No | No | Intentionally outside researchos (CONTRIBUTING.md:124) |
| `tools/`, `scripts/` | Yes (repo-root CWD) | No | Dev tooling |

## 4. Dynamic / String-Based References (verified)

- `researchos/quant_engine/research_cpp_backend.py:73` — dynamic import of the compiled pybind11 module with Python-reference fallback (warning, not error). **Only dynamic import boundary in the codebase.**
- No `importlib.import_module(<variable>` patterns elsewhere; no string-keyed module registries found that load modules by name at runtime (model registry uses explicit class references).
- SQLite schemas and JSON keys reference type *names* (e.g. `OBJECT_REGISTRY` in `storage/repository.py`) but load classes through explicit imports, not strings.

## 5. Test Dependency Map (who tests what)

| Test root | Targets | Count basis |
|-----------|---------|-------------|
| `researchos/tests/` (60 files) | researchos.* integration + architecture guards | CI suite part 1 |
| `tests/unit/test_backends/` | quant_engine backend/router/scheduler | CI suite part 2 |
| `tests/unit/test_macro_intelligence/` (15+ files) | **macro_intelligence only** | CI suite part 2 |
| `tests/unit/test_reasoning_engine/` | reasoning_engine contracts | CI suite part 2 |
| `researchos/data_engine/tests/`, `market_memory/tests/`, `experiments/phase51/tests/` | package-local | NOT in CI suite (see §7) |
| `cpp_quant_engine/tests/` (C++) | C++ engine | separate workflow |

## 6. Packaging Boundary (verified behavior)

`pyproject.toml` → `[tool.setuptools.packages.find] include = ["researchos*"]`.

Verified from outside the repo root: `importlib.util.find_spec("macro_intelligence")` returns **None**. Consequences:

1. `pip install researchos` ships **only** `researchos*`. `macro_intelligence`, `cpp_quant_engine/python`, `monitoring` are repo-local code.
2. Tests import `macro_intelligence` successfully only because pytest inserts the repo root into `sys.path` (repo-root execution). This works in CI (checkout + editable install + pytest from root) **by CWD accident, not by installation design**.
3. CI coverage measures `--cov=researchos` only — `macro_intelligence` coverage (86% locally) is invisible to CI.

## 7. CI Execution Graph (verified from `.github/workflows/`)

| Workflow | Runs | Gap |
|----------|------|-----|
| `test-python.yml` | `pytest researchos/tests/ tests/unit/` on py 3.10/3.11/3.12 | Package-local tests (`data_engine/tests`, `market_memory/tests`, `phase51/tests`) **not in CI**; local dev on 3.14.6 vs CI max 3.12 |
| `test-cpp.yml` | cmake + make + `ctest --verbose \|\| echo "⚠️ not available"` | **`\|\| echo` masks C++ test failures — C++ tests can never fail CI**; no Release config; installs boost (unused by CMakeLists) |
| `coverage.yml` | coverage on push/PR | `--cov=researchos` only (see §6) |
| `security.yml` | gitleaks + custom secret scan | OK |

## 8. Module Liveness (coverage-verified, full local run 2026-08-17)

| Module | Coverage | Verdict |
|--------|----------|---------|
| decision_engine/* | 83–100% | LIVE (actively tested; earlier "0%" reports were an artifact of a partial test-root run) |
| evidence/* | 83–100% | LIVE (certification layer) |
| intelligence/* | 92–100% | LIVE (Q12/Q13) |
| market_memory/* | 96–100% | LIVE |
| memory/engine.py | 94% | LIVE (via `researchos/tests/test_market_memory.py`) |
| macro/engine.py | 86% | LIVE |
| reasoning_engine/* | 89–100% | LIVE (contracts-only; no production importer yet — phase 4.5.1 foundation) |
| macro_intelligence/* | ~86% overall; `interfaces/`, `exceptions.py` at 0% | TESTED but runtime-dead; `interfaces/` + `exceptions.py` are unwired |
| cpp_quant_engine/python/* | 0% in Python runs | Bridge exercised only when compiled module present; C++ side covered by 526 C++ tests |
