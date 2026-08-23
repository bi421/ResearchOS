# Phase 4.5 — C++ Quant Engine Performance Audit (STEP 1)

Agent: **AI Agent B** — C++ quant engine numerical-performance optimization only.
Scope boundary: this audit covers the pure numerical kernels in
`cpp_quant_engine/` (sources under `src/`, headers under `include/`) and the
pybind11 shim in `bindings/python_bindings.cpp`. It does **not** touch trading
logic, strategy config, broker/MQL5 layer, or the Python `QuantComputationInterface`
adapter contract (those are Agent A's scope).

## 0. Platform mismatch (required disclosure)

| Aspect | Task brief says | Actual environment |
|---|---|---|
| OS | Linux | **Windows** (win32) |
| Compiler | — | **MSVC 14.44.35207** (VS 2022 17.14, `\Microsoft Visual Studio\2022\BuildTools`) |
| Arch | — | **x86-64** (Hostx64/x64 toolchain) |
| Build | CMake | CMake 4.4.0 (cache at `build/CMakeCache.txt`) |
| Python | 3.14.6 | 3.14.6 (CPython, `cp314` ABI) |
| Module | `.so` | `cpp_quant_backend.cp314-win_amd64.pyd` |

**Consequence:** Linux-only tooling (perf, valgrind, `-march=native` GNU
extensions, OpenMP via libgomp) is **not** used. Profiling strategy relies on
MSVC tools: `/O2` optimization reports, optional Visual Studio Profiler
(availability to be confirmed), native `benchmark_main.cpp` timing, and
`std::chrono::steady_clock` wall-clock + `GetProcessMemoryInfo` peak
working-set memory (already wired into the harness at `benchmarks/benchmark_main.cpp:52`).
The x86-64 host supports **AVX2/AVX/SSE** (`/arch:AVX2` is valid for MSVC x64);
OpenMP is available via MSVC `/openmp` but its reduction semantics for
floating-point sums are **non-associative** and would break determinism — so
OpenMP is excluded unless reductions are made order-stable.

## 1. Source inventory (numerical kernels in scope)

- `include/quant_engine.hpp` — master public API (statistics, market_data,
  simulation, metrics namespaces). Versioned (`ENGINE_VERSION "1.0.0"`,
  `CALCULATION_V1`).
- `src/quant_engine.cpp` — returns (absolute/percentage/log),
  `rolling_volatility_series`, `rolling_volatility`,
  `volatility_change`, `max_drawdown`.
- `src/statistics.cpp` — `mean`, `variance`, `standard_deviation`,
  `z_score`, `skewness`, `kurtosis`, `distribution_summary`.
- `src/metrics.cpp` — `sharpe_ratio`, `sortino_ratio`, `calmar_ratio`,
  `profit_factor`, `win_rate`, `average_return`, `compute_all_metrics`,
  `downside_deviation`.
- `src/simulation.cpp` — `run_simulation`, equity-curve build, FNV-1a input
  hash, `ostringstream`-based result serialization/hashing.
- `src/statistics/descriptive.cpp` — `DescriptiveStats::compute` (mean/var/
  min/max/skew/kurt + sorted quantiles), `compute_weighted`, covariance,
  autocorrelation. (Separate API used by `quant::` namespaces below the
  `quant_engine::` shim; the legacy `CppQuantBackend` uses the
  `quant_engine::` path — see `bindings/python_bindings.cpp:383`.)
- `src/strategy/strategy_kernel.cpp` — per-bar simulation kernel; **already
  optimized** (single pass, `reserve`d vectors, no per-bar allocation) —
  no action expected here.
- `src/research/optimizer.cpp` — grid/random seeded/reseeded optimizer,
  **already parallel** via `std::thread` pool (lines 306-321); deterministic
  stable_sort ranking. Parallelization of the optimizer is therefore
  already handled and out of scope for 4.5's parallel-computation step
  (only single-run kernels are candidates).
- `bindings/python_bindings.cpp` — pybind11 shim. `CppQuantBackend`
  (legacy `QuantComputationInterface`) delegates to the `quant_engine::`
  functions; `Backend` delegates to the `quant::bridge` path.

## 2. Hot functions (by execution cost)

Identified from source analysis + Phase 4.3 Python-side benchmark numbers
(`researchos/benchmarks/benchmark_cpp.py`):

| Rank | Function | Location | Why hot |
|---|---|---|---|
| 1 | `rolling_volatility_series` | `src/quant_engine.cpp:87` | **O(n·w)** — copies each window into a temp `std::vector` and calls `standard_deviation` (which allocates + full-passes mean+variance). For n=10M, w=21 → ~210M element ops + 10M allocations. Headline target. |
| 2 | `distribution_summary` | `src/statistics.cpp:130` | ~5 full passes: `std::accumulate` (sum) + `minmax_element` + `variance` (accumulate mean + loop) + `standard_deviation` (sqrt of variance, re-walking) + `skewness` (own mean+std passes) + `kurtosis` (own mean+std passes). Redundant passes dominate at n=10M. |
| 3 | `compute_all_metrics` | `src/metrics.cpp:147` | `downside_deviation` (alloc temp + `standard_deviation`), `sharpe_ratio` (recompute mean+std), `sortino_ratio` (recompute mean+downside), `calmar_ratio` (recompute mean + `max_drawdown`), `profit_factor`/`win_rate` (extra passes). 6-7 passes over `returns`. |
| 4 | `run_simulation` hash/serialize | `src/simulation.cpp:76-85` | `serialize_vector` builds an `ostringstream` per element → O(n) string allocations for `returns`, `equity_curve`, and each map entry. Large n (1M+) serialization dominates tail of `run_simulation`. |
| 5 | `calculate_returns` (pybind) | `bindings/python_bindings.cpp:387` | Phase 4.3: **0.42x** C++/Python @100k — bound by pybind11 `py::cast<std::vector<double>>` copy + per-call dispatch, not compute. |
| 6 | `mean`/`variance`/`standard_deviation` | `src/statistics.cpp:38..66` | Each independently recomputes the mean via `std::accumulate`. No single-pass reuse possible across the public API (each is a standalone entry point) — but internal callers can be consolidated. |
| 7 | `value_at_risk` (CVaR) | `src/statistics/risk.cpp:12` | Extra `std::sort` (O(n log n)) + linear CVaR sums. Sort is unavoidable for historical VaR, but only needed when VaR path is exercised (Phase 4.5 baseline focuses on returns/stats/vol/metrics/sim, so lower priority). |

## 3. Memory issues (no API/numeric-output changes)

- **`rolling_volatility_series` (src/quant_engine.cpp:101-109):** constructs a
  fresh `std::vector<double> window_returns(begin+i, begin+i+w)` per window —
  1 allocation + 1 copy per window. Eliminate by an incremental running
  sum-of-squares / Welford pass over the sliding window (O(n) time, O(1)
  extra memory). Must preserve the exact variance formula (ddof via
  `standard_deviation(window)` = population-ish with `ddof=1` default) so
  outputs and the Phase 4.3/4.4 parity hash are byte-identical.
- **`downside_deviation` (src/metrics.cpp:26-40):** allocates a full
  `std::vector<double> negative_returns` per call. Replace with an
  in-place accumulator (single pass; count + sum of squares of negatives).
- **`DescriptiveStats::compute` (src/statistics/descriptive.cpp:35):**
  `auto sorted = data;` full copy + `std::sort`. Quantiles are only needed
  when callers request q1/median/q3 — the `quant_engine::` shim's
  `distribution_summary` does **not** compute quantiles, so this copy is
  irrelevant to the 4.5 baseline ops; no change needed for 4.3/4.4 parity
  path.
- **`run_simulation` / hash serialization:** `serialize_vector` allocates
  per element via `ostringstream`. Can be replaced with a fast buffer-backed
  formatting loop (no numeric change — same `%.10f`, same `FNV-1a-64`
  hash). This is a pure perf path with zero output impact.
- **pybind copies:** `get_double_list` / `py::cast<std::vector<double>>`
  deep-copies Python lists into C++ vectors. Candidate for zero-copy
  `py::array_t<double, py::array::c_style>` buffer-protocol interop (Phase 4.5
  SIMD/memory step), guarded so the legacy dict-based API still works.

## 4. Vectorization / SIMD opportunities

- MSVC x64 with `/arch:AVX2` enables 4-wide `double` SIMD in auto-vectorized
  loops (`std::transform`, `std::accumulate`, `std::adjacent_difference`).
  Candidate loops: returns construction (`src/quant_engine.cpp:32`, `simulation.cpp:121`),
  max-drawdown pass (`quant_engine.cpp:169`), equity-curve build
  (`simulation.cpp:89`), drawdown/volatility rolling sums.
- The existing code uses range-based `for (double r : returns)` and index
  loops that MSVC can vectorize once `/O2` + `/arch:AVX2` are set; the
  compiler will emit AVX2 for `std::accumulate`-style reductions but
  **floating-point reductions are order-sensitive** — vectorized SIMD
  horizontal adds change rounding vs. the scalar reference. To preserve
  parity within `atol=1e-12`/`rtol=1e-10`, vectorize with an explicit
  multiple-pass partial sums + deterministic scalar fold, or restrict SIMD
  to order-independent ops (e.g., element-wise transform in
  `percentage_returns`, `log_returns`).
- Strategy kernel (`strategy_kernel.cpp`) already notes "SIMD-friendly"
  contiguous vectors; no manual intrinsics needed there.

## 5. Parallel-computation opportunities

- `Optimizer::optimize` (src/research/optimizer.cpp:306-321) **already uses**
  a `std::thread` pool over parameter combos; parallel step for the optimizer
  is NOT applicable.
- Single-run kernels (`run_simulation`, `compute_all_metrics`,
  `distribution_summary`) are sequential by nature and not split across
  threads in the current contract; parallelizing them would require new API
  and would reorder FP reductions (determinism risk). **Excluded** from 4.5
  unless a thread-local partial-sum + deterministic merge is designed.
- `rolling_volatility_series` could be parallelized across windows, but
  floating-sum order across windows is independent per-window (each window
  result is independent), so window-level parallelism is **safe and
  deterministic** — candidate for the parallel step if memory-bound
  (it is not; it is O(n·w)).

## 6. Compiler / build options (current vs. target)

- Current cache (`build/CMakeCache.txt`):
  - `CMAKE_CXX_FLAGS = /DWIN32 /D_WINDOWS /EHsc` (base, no optimization).
  - `CMAKE_CXX_FLAGS_DEBUG = /Zi /Ob0 /Od /RTC1` (Debug — used by existing `build/`).
  - `CMAKE_CXX_FLAGS_RELEASE = /O2 /Ob2 /DNDEBUG`.
  - `CMAKE_CXX_FLAGS_RELEASE` has **`/O2` only** — no `/arch:`, no `/fp:`,
    no `/GL`/LTCG, no `/Ot`, no `/fp:contract`. `HAS_MSVC_GL_LTCG:INTERNAL=1`
    was detected by CMake → LTCG is available.
- No `/openmp` flag present → OpenMP disabled.
- `quant_engine` is a **STATIC** library (`CMakeLists.txt:23`) — LTCG at the
  static-lib level plus `/LTCG:FAST` at the `.pyd`/exe link step is the
  portable path.
- The existing build dir is **Debug**; Phase 4.5 baseline must benchmark a
  **Release** build (with `/O2` at minimum) for realistic numbers, then show
  the delta when `/arch:AVX2` + LTCG + `/Ot` are added.

## 7. Expected improvement (per step target, to be confirmed by baseline)

| Target | Current | Expected after 4.5 |
|---|---|---|
| `rolling_volatility_series` (1M, w=21) | O(n·w) w/ n allocs | O(n), O(1) extra mem → **~50-200x** time, **~10M fewer allocs** |
| `distribution_summary` (10M) | ~5 passes | ~2 passes (sum+min+max via `minmax_element`, then var+skew+kurt reusing mean) → **~1.5-2x** |
| `compute_all_metrics` (10M) | ~6 passes | collapsed to ~3 passes (mean+var once, shared drawdown) → **~1.5-2x** |
| `run_simulation` large-n hash (1M+) | per-element `ostringstream` | buffer-backed formatting → **~2-5x** on serialize |
| `calculate_returns` (per-call pybind) | 0.42x (overhead-bound) | zero-copy `py::array_t` + avoid vector copy → cross-even at n≥10k |
| Compiler (`/O2`→+AVX2+LTCG) | baseline Release | scalar + link-time IPO across the above → **~1.05-1.15x** on raw loops |

**Overall headline:** fixing `rolling_volatility_series` alone removes the
single largest super-linear hotspot and converts the volatility path from
the Phase 4.3 "C++ slower than Python" regime to orders-of-magnitude faster
for large n, while `compute_all_metrics`/`distribution_summary` deduplication
delivers single-digit-x on the aggregate paths. The pybind copy overhead fix
restores parity for the per-call-bound returns path.

## 8. Verification constraints (parity contract from 4.3/4.4)

- Numerical parity vs `PythonQuantBackend` within `atol=1e-12` /
  `rtol=1e-10` for all functions touched.
- `result_hash` (FNV-1a-64) and `input_hash` must remain **identical** for
  the same inputs before vs. after optimization (timing fields in
  `experiments/result.py` are observational-only, already excluded from the
  hash per Phase 4.4).
- C++ unit tests (`cpp_quant_engine/tests`, 169 passed +1 skipped) must pass
  unchanged.
- Phase 4.3 perf gates (`researchos/tests/test_cpp_benchmarks.py`,
  `RESEARCHOS_PERF=1`) and Phase 4.4 scheduler/router tests must remain green.

## 9. Audit verdict

`rolling_volatility_series` is the dominant bottleneck (super-linear +
per-window allocation). Secondary wins are redundant reduction passes in
`distribution_summary`, `compute_all_metrics`, and `run_simulation` hash
serialization, plus the pybind copy overhead on small per-call ops. Compiler
flags are unset for performance (`/O2` only in Release; no AVX2/LTCG). The
strategy kernel and optimizer are already optimized/parallelized and need no
changes. Proceed to STEP 2 (baseline benchmark) before any code change.
