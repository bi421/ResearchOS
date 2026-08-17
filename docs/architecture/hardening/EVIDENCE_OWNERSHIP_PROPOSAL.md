# EVIDENCE_OWNERSHIP_PROPOSAL.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation.

---

## CURRENT STATE — Four "Evidence" Concepts

| # | Type | Location | Introduced | Paradigm | Coverage | Runtime users |
|---|------|----------|------------|----------|----------|---------------|
| 1 | `Evidence` | `researchos/objects/evidence.py` | Phase 0 baseline (Articles XVI/XVII) | Mutable `BaseObject`; interpreted observation **bound to a hypothesis**; 6-factor quality model (reliability×recency×relevance×consensus×structural×quality), tier, aging multipliers | via research lifecycle tests | `researchos.pipeline`, `researchos.storage` (research reasoning lifecycle) |
| 2 | `EvidenceItem` | `researchos/reasoning_engine/contracts.py` | Phase 4.5.1 (Article X) | **Frozen** dataclass: `id, source, evidence_type (dataset/measurement/observation/document), content_hash, reliability_score ∈ [0,1]` | 89–100% (own unit tests only) | **None yet** — contracts-only foundation layer |
| 3 | `EvidenceItem` | `researchos/decision_engine/contracts.py` | Phase 7.2 (Article XVII Decision Layer) | Mutable dataclass: `source (EvidenceSource enum: MarketMemory/Experiment/Validation/MacroIntelligence/ResearchObjects/QuantEngine), source_id, direction (Bullish/Bearish/Neutral), strength, weight, confidence, description` | 83–100% | Decision pipeline: `EvidenceAggregator → EvidenceCollection → score → probability → reasoner → report` (tested end-to-end) |
| 4 | `EvidenceEnvelope` | `researchos/evidence/envelope.py` | Phase 5.3a | **Immutable, hash-contract hardened**: wraps 7 certified artifact types (Dataset/Feature/Experiment/Run/Result/Validation/Model) with canonical SHA-256 `artifact_hash` + `lineage_hash` over parent hashes; strict primitive payload validation | 83–100% | `experiments/runner`, reproduction engine, emission modules, `EvidenceRepository`, `LineageQueryEngine` |

Additionally: `EvidenceRegistry` (objects), `EvidenceRecord` (reasoning_engine/evidence.py), `EvidenceCollection`+`EvidenceAggregator`+`EvidenceValidator` (decision_engine), `EvidenceRepository` (evidence/ — SQLite store), `EvidenceRepository` (intelligence/ — graph store), `EvidenceValidator` (researchos/validation/).

## PROBLEM

1. **Name collision:** two public classes named `EvidenceItem` with incompatible schemas (frozen source-reference vs mutable directional-decision-input). Any future import of both in one module is a correctness hazard.
2. **Conceptual ambiguity:** `evidence/` (the package) does not manage "evidence" in the reasoning sense at all — it certifies **artifacts**. The name invites false unification attempts.
3. **Partial semantic overlap:** `objects.Evidence` (hypothesis-bound, quality-scored) and `reasoning_engine.EvidenceItem` (source-bound, reliability-scored) model adjacent stages of the same scientific reasoning act with different rigor paradigms (mutable lifecycle object vs frozen contract).

## EVIDENCE (why this is NOT one concept accidentally duplicated)

The four types answer **different questions** and appear at **different pipeline stages**:

```
Data ──certify──> #4 EvidenceEnvelope (WHAT artifact, WHICH hash, WHO produced it)   [certification]
              ──reference──> #2 reasoning_engine.EvidenceItem (WHICH source, HOW reliable) [reasoning input]
              ──interpret──> #1 objects.Evidence (WHAT it MEANS for a hypothesis)    [research reasoning]
              ──synthesize──> #3 decision_engine.EvidenceItem (WHICH direction, HOW strong) [decision input]
```

- #4 is **transport/certification representation** — identity = content hash. It must never carry semantics like direction.
- #2 is a **reasoning evidence reference** — identity = (source, content_hash); the reasoning layer converts verified evidence → Facts → Hypotheses.
- #1 is a **research-domain reasoning object** — the interpretation layer of the constitutional object model; participates in the Observation→Evidence→Hypothesis→Research lifecycle and SQLite persistence.
- #3 is **decision evidence** — the probabilistic synthesis input; explicitly directional, explicitly versioned (`DECISION_V1`), collected from six source modules via collectors that already act as adapters.

Therefore: **classification = (A) different lifecycle stages + (B) different bounded contexts.** Only the *name* is duplicated; the concepts are distinct. Forced unification would be an error (it would couple certification identity to decision semantics).

## TARGET STATE

```
Canonical identity/certification  : evidence/EvidenceEnvelope        (keep as-is; optionally document as "artifact certification")
Reasoning evidence reference      : reasoning_engine/EvidenceItem    (keep; rename candidate: ReasoningEvidence)
Research interpretation object    : objects/Evidence                 (keep; constitutional model, DO NOT TOUCH semantics)
Decision evidence                 : decision_engine/EvidenceItem     (keep; rename candidate: DecisionEvidenceItem)
                                   collectors = the adapter layer that already exists (decision_engine/evidence.py aggregators)
```

Minimal hardening (all low-risk, no semantic change):

1. **H1 — Disambiguate names (REQUIRES REVIEW).** Rename `decision_engine.contracts.EvidenceItem` → `DecisionEvidenceItem` and/or `reasoning_engine.contracts.EvidenceItem` → `ReasoningEvidence`. Pure aliasing first (`EvidenceItem = DecisionEvidenceItem` deprecation alias), removal later. Eliminates the collision without touching one field or formula.
2. **H2 — Document the evidence map (SAFE NOW).** Add a short "Evidence concepts" section to architecture docs stating the four roles above, so nobody "unifies" them later.
3. **H3 — Wire or explicitly park reasoning_engine (REQUIRES REVIEW).** `reasoning_engine` is a tested, covered, production-imported-by-nobody contracts layer. Decide: (a) it becomes the canonical bridge `#4 → #2` (envelope hash feeds reasoning evidence `content_hash` — note the fields already align), or (b) it is documented as reserved foundation. Do NOT delete: it is the only layer whose `content_hash` field matches the certification layer's hash contract.
4. **H4 — Single naming exception to document:** `intelligence/repository.EvidenceRepository` (graph store of evidence nodes) vs `evidence/repository.EvidenceRepository` (SQLite certification store). Same class name, two packages. Rename candidate: `intelligence` one → `EvidenceGraphStore`. (REQUIRES REVIEW)

## MIGRATION RISK

| Step | Risk | Why |
|------|------|-----|
| H2 docs | None | Documentation only |
| H1 renames | Low | Additive aliases; old names keep working; tests updated mechanically |
| H3 wiring | Medium | Creates first real dependency `reasoning_engine → evidence` (currently reasoning_engine depends on nothing); must stay one-directional |
| H4 rename | Low | `intelligence/repository.py` used only inside intelligence package + its tests |
| Any unification of #1/#2/#3 | **HIGH — DO NOT** | Changes scientific semantics; violates "scientific correctness > elegance" |

## REQUIRED TESTS (if H1/H3/H4 proceed)

- Full suite green (3,475 baseline), ruff clean, coverage ≥ 86%.
- Import smoke test proving both renamed and legacy names resolve.
- For H3: new unit test that an `EvidenceEnvelope.artifact_hash` round-trips into `reasoning_engine.EvidenceItem.content_hash` unchanged.

## DO NOT CHANGE

- The 6-factor quality formula, aging multipliers, tier weights in `objects/evidence.py` (Articles XVI §2.2/2.5/2.7 — scientific constants).
- `EvidenceEnvelope` hash scheme (`HASH_SCHEME_VERSION = "2"`, canonical JSON, parent-hash lineage) — reproducibility anchor; any change invalidates every stored artifact hash.
- `decision_engine` scoring/probability methods (`CalculationMethod`, `DECISION_V1` versioning) — versioned scientific methodology.
- Direction semantics ("collectors never infer direction; items are NEUTRAL until a source provides direction") — this is the anti-"NEWS→BUY/SELL" invariant, already correctly implemented.
