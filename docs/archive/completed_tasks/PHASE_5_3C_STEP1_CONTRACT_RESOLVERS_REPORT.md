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

# Phase 5.3c Step 1 — Deterministic Contract Resolvers (Report)

**Status:** COMPLETE
**Scope:** Implement only the reconstruction layer required for reproduction
(contract resolvers). No LineageQueryEngine, no ReproductionEngine.
**Architecture base:** Phase 5.3c design (Lineage Query & Reproduction Engine).

---

## 1. Summary

Implemented the missing deterministic reconstruction layer needed to make the
evidence chain reproducible:
- confirmed `SimulationConfig.from_dict()` and `DatasetConfig.from_dict()`
  already provide exact, deterministic, backward-compatible round-trips, and
- added `ResearchDataset.from_payload()` as the deterministic inverse of the
  Dataset evidence emission projection.

This unblocks reproduction: given an immutable evidence payload, the engine can
now rebuild an identical `ResearchDataset`, `SimulationConfig`, and `DatasetConfig`
from the recorded content — required before a `ReproductionEngine` can re-execute
through the certified boundary.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/quant_engine/machine_learning/dataset_contracts.py` | **Updated (additive)** — added `ResearchDataset.from_payload()` classmethod. No fields removed or renamed. |
| `researchos/tests/test_reproduction_contract_resolvers.py` | **New** — 23 deterministic tests. |
| `docs/PHASE_5_3C_STEP1_CONTRACT_RESOLVERS_REPORT.md` | **New** — this report. |

**Already present and verified (no change required):**
- `SimulationConfig.from_dict()` — already in `researchos/experiments/contracts.py`.
- `DatasetConfig.from_dict()` — already in `researchos/experiments/contracts.py`.

---

## 3. Architecture Impact

### 3.1 `ResearchDataset.from_payload()`
- New classmethod on the frozen `ResearchDataset` contract (strictly additive).
- Inverse of `researchos.evidence.dataset_emission.research_dataset_payload`.
- Reconstructs `feature_names` (tuple[str]), `features` (tuple[tuple[float]]),
  `labels` (tuple[float]), `metadata` (MappingProxyType), `sample_count`,
  `feature_count`, `label_name`, `version`.
- `created_at` is set to `None` (the payload excludes it from identity by design).
- Never mutates the input payload.
- Rejects: non-mapping payloads (`TypeError`), missing required keys (`ValueError`),
  sample-count mismatch, feature-count mismatch, and inconsistent feature-row
  widths (`ValueError`).

### 3.2 SimulationConfig / DatasetConfig resolvers
- Verified the existing `from_dict()` classmethods produce exact deterministic
  round-trips: `config.to_dict() → from_dict() → to_dict()` yields identical content.
- `DatasetConfig.to_dict()` sorts `symbols`/`filters`; `from_dict` reads them back —
  deterministic and stable.
- Backward compatible: missing optional keys fall back to documented defaults
  (e.g. `symbols=[]`, `resolution="1d"`, `seed=42`, `initial_capital=100_000.0`,
  `max_positions=10`).

---

## 4. Why This Unblocks Reproduction

The Phase 5.3c design identified `M1` (no deterministic config/`from_dict`
resolvers) as the critical blocker to reproduction. With Step 1:

1. `ResearchDataset.from_payload(payload)` rebuilds the exact dataset fed to the
   experiment.
2. `DatasetConfig.from_dict(snapshot)` rebuilds the dataset binding config.
3. `SimulationConfig.from_dict(snapshot)` rebuilds the simulation config.

A `ReproductionEngine` can now take a stored Run/Experiment/Dataset payload,
rebuild the exact inputs, re-execute through the certified boundary, and compare
hashes — the payload content hashes to the identical original hash.

---

## 5. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_reproduction_contract_resolvers.py -q` | **23 passed** |
| Combined evidence + resolver suites (`researchos/tests/test_evidence_repository.py`, `test_dataset_evidence_emission.py`, `test_experiment_evidence_emission.py`, `test_run_evidence_emission.py`, `test_result_evidence_emission.py`, `test_validation_evidence_emission.py`, `test_reproduction_contract_resolvers.py`) | **200 passed** |
| `pytest researchos/ -q` (full suite) | see section 7 |
| `python -m ruff check researchos/quant_engine/machine_learning/dataset_contracts.py researchos/tests/test_reproduction_contract_resolvers.py` | **All checks passed** |

### Verification output
Round-trips verified:
- `SimulationConfig`: to_dict → from_dict → to_dict equals original to_dict.
- `DatasetConfig`: to_dict → from_dict → to_dict equals original to_dict; list
  fields deterministically sorted.
- `ResearchDataset`: `research_dataset_payload(ds) → from_payload` reconstructs
  all fields exactly; re-emitting the reconstructed dataset yields the identical
  `artifact_hash` (deterministic hash preservation).

Invalid-payload rejection verified:
- non-mapping → `TypeError`
- missing required key → `ValueError`
- sample_count mismatch → `ValueError`
- feature_count mismatch → `ValueError`
- inconsistent feature-row width → `ValueError`

Backward compatibility verified:
- Legacy `DatasetConfig.from_dict({"source": "yahoo"})` → defaults populated.
- Legacy `SimulationConfig.from_dict({"seed": 9})` → defaults populated.

---

## 6. Constraints Honored

- ✅ No LineageQueryEngine implemented.
- ✅ No ReproductionEngine implemented.
- ✅ No modification to `EvidenceEnvelope`.
- ✅ No modification to `EvidenceRepository`.
- ✅ No modification to the lineage schema.
- ✅ `ResearchDataset` contract: only an additive classmethod (no fields removed/renamed).
- ✅ No trading logic, broker integration, ML/model registry, or C++ changes.
- ✅ Append-only and deterministic identity preserved.

---

## 7. Full Suite & Pre-Existing Failures

The full `researchos/` suite result and any pre-existing unrelated failures are
reported in the completion message (the same two pre-existing `market_memory`
failures observed in prior phases are unrelated to this change; this change adds
23 new passing tests with zero new regressions).

---

*Phase 5.3c Step 1 — Deterministic Contract Resolvers.*
*Classification: Internal — Implementation Evidence*

