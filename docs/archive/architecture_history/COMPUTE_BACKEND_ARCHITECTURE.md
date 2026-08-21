# Document Status

Status:
ARCHIVED

Reason:
Historical record only

Superseded by:
See docs/ARCHITECTURE_FREEZE_V2.md (current constitution)

Original purpose:
See docs/DOCUMENTATION_INVENTORY_REPORT.md

---

# ResearchOS — Compute Backend Architecture & Certification

**Version:** 1.0.0
**Date:** 2026-08-04
**Status:** IMPLEMENTED (Phase 4.1)
**Classification:** Internal — Quantitative Platform
**Related:** `docs/COMPUTE_BACKEND_BASELINE.md`, `PHASE4.1_CERTIFICATION_REPORT.md`

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Trust Hierarchy](#2-trust-hierarchy)
3. [Backend Certification Contract](#3-backend-certification-contract)
4. [Numerical Validation](#4-numerical-validation)
5. [Certified Routing Flow](#5-certified-routing-flow)
6. [Deterministic Result Hashing](#6-deterministic-result-hashing)
7. [Execution Metadata & Audit](#7-execution-metadata--audit)
8. [Automatic Python Fallback](#8-automatic-python-fallback)
9. [Migration Path (Future C++)](#9-migration-path-future-c)
10. [Constraints & Boundaries](#10-constraints--boundaries)

---

## 1. Purpose

The Quant Computation Engine is a **pure-Python, standard-library-only**
numerical layer. It must be *certifiable*: every computation backend must be
able to prove determinism, statelessness, and result integrity at the trust
boundary.

Phase 4.1 adds the certification and trust-boundary layer around the existing
`QuantComputationInterface`:

| Component | File | Role |
|-----------|------|------|
| `BackendCapabilities` | `researchos/quant_engine/capabilities.py` | Machine-readable certification contract |
| `NumericalComparator` | `researchos/quant_engine/numerical_validation.py` | Certification-grade numeric validation |
| `backend_hash` | `researchos/quant_engine/backend_hash.py` | Canonical, deterministic result digests |
| `BackendRouter` | `researchos/quant_engine/router.py` | Trust-boundary routing + audit metadata |

These components **compute nothing themselves**. They certify, validate, and
audit the outputs produced by conforming backends. They make no trading,
signalling, or prediction decisions.

## 2. Trust Hierarchy

```
        ResearchOS upper layers (Experiment Framework, Market Memory, Validation)
                                   │
                                   ▼
                    QuantComputationInterface (abstract)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
         PythonQuantBackend              CppQuantAdapter (future / optional)
         (REFERENCE — source of truth)   (validated against reference)
                    │
                    ▼
            BackendRouter (Phase 4.1)
              capability check → execute → validate → audit → fallback
```

- The **Python reference backend** (`PythonQuantBackend`) is the ONLY
  scientific source of truth. Its outputs define correctness.
- A candidate backend (e.g. a future C++ kernel) may be *faster*, but its
  outputs are only trusted when they numerically match the reference within
  the certification tolerance policy.
- The `BackendRouter` sits at the boundary and enforces this relationship.

## 3. Backend Certification Contract

Every conforming backend MUST guarantee:

1. **Deterministic execution** — identical inputs → identical outputs.
2. **Statelessness** — no hidden mutable state affecting computation.
3. **No timestamps** — results never depend on wall-clock time.
4. **No randomness** — computation never consumes randomness.
5. **Explicit typing** — declared signatures, no implicit value coercion.

These guarantees are machine-checkable via `backend.capabilities()`, which
returns an immutable `BackendCapabilities` object:

```python
BackendCapabilities(
    backend_name="PythonQuantBackend",
    version="1.0.0",
    supported_operations=QUANT_OPERATIONS,  # 7 interface operations
    deterministic=True,
    stateless=True,
    no_timestamps=True,
    no_randomness=True,
    explicit_typing=True,
)
```

- `QuantComputationInterface` now provides **concrete defaults**
  `get_version()` (class name) and `capabilities()` (full trust contract),
  so existing subclasses and test doubles keep working unchanged.
- The `BackendRouter` **refuses to route work** to any backend whose
  `capabilities()` violate the contract (any guarantee `False`).

## 4. Numerical Validation

`NumericalComparator` compares a candidate output against the reference
output using the certification tolerance policy:

| Rule | Value |
|------|-------|
| Shape | identical (scalar / vector length / matrix dimensions) |
| NaN | rejected (never accepted, even on both sides) |
| ±Infinity | rejected |
| Absolute tolerance (`atol`) | `1e-12` |
| Relative tolerance (`rtol`) | `1e-10` |
| Pass criterion | `\|a - b\| <= atol + rtol * \|b\|` element-wise |

Every comparison returns a frozen, hashable `NumericalValidationResult`
with `status`, `shape_match`, `has_nan`, `has_inf`, `max_abs_error`,
`max_rel_error`, `atol`, `rtol`, and a deterministic `comparison_hash`
(SHA-256). `to_dict()` / `from_dict()` give JSON-compatible serialization.

Supported shapes: scalars, vectors (1-D), matrices (2-D).

## 5. Certified Routing Flow

`BackendRouter.execute(operation, inputs, expected=None, atol=, rtol=)`
enforces the certified flow:

```
Request
  ↓
Capability check (candidate advertises op + trust guarantees)
  ↓
Candidate backend (first conforming registered backend)
  ↓
Execute candidate
  ↓
Validation against reference (or caller-provided `expected`)
  ↓
Success → Return (fallback_used=False, error_code="ok")
  ↓ (else)
Automatic Python fallback (fallback_used=True)
```

- `expected=None` → the router executes the reference backend to produce the
  reference output for validation. A caller may supply `expected` to skip the
  reference execution (e.g. in a test).
- A candidate that fails capability, execution, or numerical validation is
  **replaced** by the reference backend's output — the caller always receives
  a certified-correct result, never an unvalidated one.

## 6. Deterministic Result Hashing

`compute_backend_result_hash` produces a 64-char SHA-256 digest over a
canonical serialization of the execution:

```
{ hash_version, operation, backend, version, input_hash, output }
```

Canonicalization rules (`backend_hash.canonicalize`):

- dict keys sorted; lists/tuples normalized to lists
- floats formatted via `stable_float` (shortest round-trip `repr`;
  explicit `"NaN"`, `"Infinity"`, `"-Infinity"`, `"0.0"` including `-0.0`)
- ints / bools / strings / `None` pass through
- objects with `to_dict()` are canonicalized via it

Consequences:

- identical logical values → identical digests (independent of container order)
- identical float values → identical digests (no representation drift)
- `compute_input_hash` provides input provenance; timings are intentionally
  **excluded** from the hash (observational metadata must not affect identity)

## 7. Execution Metadata & Audit

Every router execution returns a frozen `BackendExecutionResult`
(`metadata` + `output`). The `BackendExecutionMetadata` record is immutable:

| Field | Meaning |
|-------|---------|
| `operation` | Operation name executed |
| `backend` | Backend that produced the returned output |
| `version` | Version of that backend |
| `fallback_used` | Whether the Python reference was used |
| `validation_status` | `"passed"` / `"failed"` / `"not_required"` |
| `execution_time_ms` | Observational wall-clock time (NOT hashed) |
| `result_hash` | Deterministic canonical SHA-256 of the execution |
| `error_code` | `ok` / `unavailable` / `execution_failed` / `validation_failed` |

`to_dict()` / `from_dict()` provide deterministic, JSON-compatible audit
records suitable for persistence.

## 8. Automatic Python Fallback

The fallback path guarantees availability and correctness:

- **No candidate** registered → run on the reference (`error_code="unavailable"`).
- **Candidate execution raises** → run on the reference (`error_code="execution_failed"`).
- **Candidate output fails validation** → run on the reference
  (`error_code="validation_failed"`).
- **Candidate violates the trust contract** → not selected; reference used.
- **Capabilities unavailable** (raises) → treated as no candidate.

The caller always receives a certified result; `fallback_used=True` and the
`error_code` record exactly what happened.

## 9. Migration Path (Future C++)

The certification layer makes a future C++ backend (C++20 + CMake + pybind11)
safe to adopt incrementally:

1. Implement `QuantComputationInterface` in C++ (the abstract surface is
   unchanged — upper layers never change).
2. Override `capabilities()` to advertise the C++ version and the exact
   supported operation subset.
3. Register it with the `BackendRouter`; every call is validated against the
   Python reference before its output is returned.
4. Ship only after the parity suite (`cpp_quant_engine/python/tests/`) and
   router validation pass for all advertised operations.

`CppQuantAdapter` remains the optional/future C++ boundary; in this
environment the C++ module is not built and it falls back to Python with a
warning — the certification layer treats that fallback transparently.

## 10. Constraints & Boundaries

- **No C++** in this phase. No numpy / scipy / BLAS / LAPACK. The compute
  layer is standard-library-only; pytest is the only dev dependency.
- **No ML / AI / LLM** — the certification layer is pure validation/hashing.
- The Python reference backend remains the ONLY scientific source of truth.
- `PythonQuantBackend.get_version()` returns `"PythonQuantBackend"` (not a
  semantic version) to preserve the existing parity-test contract.
- Timestamps are never part of any hash; `execution_time_ms` is observational.

---

**See also:** `docs/COMPUTE_BACKEND_BASELINE.md` (performance baseline),
`PHASE4.1_CERTIFICATION_REPORT.md` (certification evidence).
