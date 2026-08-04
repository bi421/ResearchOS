# ResearchOS — Compute Backend Performance Baseline

**Version:** 1.0.0
**Date:** 2026-08-04
**Status:** BASELINE — Reference Only (Python, No Optimization)
**Classification:** Internal — Quantitative Platform
**Related:** `docs/COMPUTE_BACKEND_ARCHITECTURE.md`

---

## Purpose

This document records the **performance baseline** of the Python reference
compute backend. The baseline is:

- **Pure Python, standard library only** — no numpy / scipy / BLAS / LAPACK,
  no C++ kernels, no optimization of any kind.
- The numbers are the **source-of-truth reference** against which any future
  accelerated backend (e.g. the future C++ `CppQuantAdapter`) must be
  measured. A faster backend is only useful if it is *also* numerically
  correct — see the certification layer in `COMPUTE_BACKEND_ARCHITECTURE.md`.

Phase 4.1 is explicitly **not** a C++ acceleration phase. This baseline exists
so that future acceleration work has a fixed, reproducible reference point.

## Methodology

- **Hardware/OS:** Windows, x86-64 (this repository's development machine).
- **Interpreter:** Python 3.14.6, CPython.
- **Workloads:** matrix multiply (ijk), matrix transpose, linear solve
  (Gaussian elimination with partial pivoting).
- **Sizes:** N = 10, 50, 100.
- **Measurement:** best-of-N wall-clock runs via `time.perf_counter()`
  (best-of reduces scheduler noise). Reported in milliseconds.
- **Data:** deterministic fixed-seed (`random.seed(42)`) random matrices.

The benchmark is intentionally naive — it is a *baseline*, not a product.

## Results

| Operation | N | Reps | Best time (ms) |
|-----------|-----|------|-----------------|
| matrix_multiply | 10  | 10 | 0.0583 |
| transpose       | 10  | 10 | 0.0042 |
| linear_solve    | 10  | 10 | 0.0368 |
| matrix_multiply | 50  | 10 | 5.9701 |
| transpose       | 50  | 10 | 0.0796 |
| linear_solve    | 50  | 10 | 2.8082 |
| matrix_multiply | 100 | 3  | 53.5343 |
| transpose       | 100 | 3  | 0.4123 |
| linear_solve    | 100 | 3  | 24.6230 |

### Observations

- **Matrix multiply** dominates and grows cubically: 10→100 (~1000×) yields
  ~920× runtime, as expected for O(N³).
- **Linear solve** grows ~O(N³): 10→100 yields ~670× runtime.
- **Transpose** is O(N²) and effectively free at these sizes.
- The values are environment-specific; only the **relative scaling** and the
  methodology are portable. Re-run with the same script on a different machine
  to produce a local reference point.

## Benchmark Script (reproducible)

```python
import time
import random

random.seed(42)


def matmul(a, b, n):
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            aik = a[i][k]
            row = out[i]
            bk = b[k]
            for j in range(n):
                row[j] += aik * bk[j]
    return out


def transpose(a, n):
    return [[a[j][i] for j in range(n)] for i in range(n)]


def linsolve(a, b, n):
    a = [row[:] for row in a]
    x = [0.0] * n
    for i in range(n):
        if a[i][i] == 0.0:
            for k in range(i + 1, n):
                if a[k][i] != 0.0:
                    a[i], a[k] = a[k], a[i]
                    break
        piv = a[i][i]
        for j in range(i, n):
            a[i][j] /= piv
        for k in range(i + 1, n):
            f = a[k][i]
            for j in range(i, n):
                a[k][j] -= f * a[i][j]
    for i in range(n - 1, -1, -1):
        s = b[i]
        for j in range(i + 1, n):
            s -= a[i][j] * x[j]
        x[i] = s / a[i][i]
    return x
```

## Baseline vs. Acceleration Policy

1. Any accelerated backend must match the reference numerically (certification
   tolerances `atol=1e-12`, `rtol=1e-10`) before its speed matters.
2. A backend is adopted when it is **both** certified and faster than this
   baseline on the same machine.
3. The Python reference backend remains the scientific source of truth
   regardless of any future acceleration.
