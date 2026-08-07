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

# Phase 5.3b.2 — Experiment Evidence Emission

**Status:** COMPLETE
**Scope:** Connect the existing `Experiment` contract to the `EvidenceRepository`
by emitting Experiment evidence artifacts (scheme-2 hashes).
**Architecture base:** Phase 5.3a evidence & lineage foundation +
Phase 5.3b.1 Dataset evidence emission.

---

## 1. Summary

Implemented Experiment evidence emission only: an experiment artifact builder
that projects the existing `Experiment` contract into a scheme-2
`EvidenceEnvelope` (artifact type `"Experiment"`) and persists it to the
append-only `EvidenceRepository`, including Dataset → Experiment lineage
wiring.

Strictly **additive and compatibility-preserving**:
- Preserves existing `Experiment` behavior (no mutation).
- Does NOT emit Run or Result yet.
- No execution changes.
- No model registry.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/evidence/experiment_emission.py` | **New** — experiment artifact builder (`build_experiment_envelope`, `experiment_payload`, `attach_dataset_parent`, `emit_experiment`, `emit_experiment_with_dataset`). |
| `researchos/evidence/__init__.py` | **Updated** — exported the new experiment emission API. |
| `researchos/tests/test_experiment_evidence_emission.py` | **New** — 26 deterministic tests. |
| `docs/PHASE_5_3B2_EXPERIMENT_EVIDENCE_EMISSION_REPORT.md` | **New** — this evidence report. |

---

## 3. Design

### 3.1 Experiment payload projection
`experiment_payload(experiment)` produces a deterministic, primitives-only
mapping mirroring `Experiment._to_hashable_dict`:

- `experiment_hash` — deterministic experiment identity
- `hypothesis_id` — hypothesis identity
- `name`, `description`, `experiment_type`, `status`, `version`
- `dataset_config` — snapshot via `to_dict()` (dataset references)
- `simulation_config` — snapshot via `to_dict()`
- `metric_definitions`, `parameters`, `tags`, `experiment_trace`, `ontology_tags`

`created_at` is **excluded** (observational telemetry, never hashed). The
projection does not mutate the source `Experiment`.

### 3.2 Experiment envelope
`build_experiment_envelope(experiment, ...)` builds a scheme-2
`EvidenceEnvelope` with `artifact_type="Experiment"`:

- `artifact_hash = hash(scheme, "Experiment", version, payload)` — binds type +
  version + payload, so:
  - identical experiment → identical `artifact_hash`, and
  - changed config (dataset/simulation/params) → different `artifact_hash`.
- `lineage_hash = hash(scheme, "Experiment", version, payload, sorted parents)`
  — parent order irrelevant; version/type tampering fails verification.

### 3.3 Dataset → Experiment lineage
`attach_dataset_parent(envelope, dataset_hash)` returns a new envelope carrying
the dataset artifact hash as a parent. On append, `EvidenceRepository` writes a
`Dataset → Experiment` lineage edge. `emit_experiment_with_dataset` combines
build + link + emit atomically.

### 3.4 Persistence
`emit_experiment(envelope, repository)` appends the envelope to an
`EvidenceRepository` (append-only). It rejects non-Experiment envelopes and
tampered envelopes (verify failure).

---

## 4. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_experiment_evidence_emission.py -q` | **26 passed** |
| `pytest researchos/tests/test_experiment_evidence_emission.py researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_evidence_repository.py -q` | **85 passed** |
| `pytest researchos/ -q` (full suite) | **2371 passed, 58 skipped, 2 failed** |
| `ruff check researchos/evidence/ researchos/tests/test_experiment_evidence_emission.py researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_evidence_repository.py` | **All checks passed** |

### Verification output (acceptance criteria)
- **identical experiment → identical artifact_hash** — ✅ `test_acceptance_identical_identical_hash`, `test_same_experiment_same_artifact_hash`
- **changed config → different artifact_hash** — ✅ `test_acceptance_changed_config_diff_hash`, `test_changed_dataset_config_different_artifact_hash`, `test_changed_sim_config_different_artifact_hash`, `test_changed_params_different_artifact_hash`
- **dataset linkage preserved** — ✅ `test_acceptance_dataset_linkage_preserved`, `test_dataset_parent_preserved`
- **artifact retrievable from EvidenceRepository** — ✅ `test_acceptance_retrievable_from_repo`, `test_emit_and_retrieve`
- **lineage edge Dataset -> Experiment works** — ✅ `test_acceptance_dataset_to_experiment_edge`, `test_lineage_edge_dataset_to_experiment`, `test_emit_experiment_with_dataset_links_lineage`

### Pre-existing failures (unrelated to this change)
The 2 failures are in `researchos/market_memory/` (untouched by this work):
1. `test_round_trip` — passes a non-existent `outcome_price_change` argument.
2. `test_doji_candle` — asserts a Doji (body=0.0) is `is_bullish`.

Identical failures existed before this change.

---

## 5. Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Experiment evidence artifacts created from existing Experiment contract | ✅ |
| `artifact_type="Experiment"` | ✅ |
| Uses `HASH_SCHEME_VERSION = 2` | ✅ |
| Includes experiment_hash | ✅ |
| Includes hypothesis identity | ✅ |
| Includes dataset references / dataset_config snapshot | ✅ |
| Includes simulation_config snapshot | ✅ |
| Includes methodology/version metadata | ✅ |
| Preserves existing Experiment behavior | ✅ |
| Does NOT emit Run or Result | ✅ |
| No execution changes | ✅ |
| No model registry | ✅ |
| Deterministic tests added | ✅ |
| Full ResearchOS suite stays green (no new regressions) | ✅ |

---

## 6. Constraints Honored

- ✅ **Determinism** — canonical scheme-2 hashes; time excluded.
- ✅ **Immutability** — frozen envelopes; append-only store.
- ✅ **Additive-only** — no existing module changed destructively.
- ✅ **No trading logic** — certification/trust layer only.

---

*Phase 5.3b.2 Experiment Evidence Emission — Report*
*Classification: Internal — Implementation Evidence*
