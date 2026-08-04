# ResearchOS Macro Intelligence Layer — Knowledge Generation Engine Architecture

**Version:** know-eng/v1.0.0
**Rules Version:** know-rules/v1.0.0
**Status:** ARCHITECTURALLY FROZEN — Ready for Macro Intelligence Synthesis
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Architecture Role](#1-architecture-role)
2. [Dependency Boundaries](#2-dependency-boundaries)
3. [Module Layout](#3-module-layout)
4. [KnowledgeObject Design](#4-knowledgeobject-design)
5. [KnowledgeType Taxonomy](#5-knowledgetype-taxonomy)
6. [Algorithms](#6-algorithms)
7. [Invariants](#7-invariants)
8. [Extension Rules](#8-extension-rules)
9. [Limitations](#9-limitations)

---

## 1. Architecture Role

The **Knowledge Generation Engine** is the final interpretation layer inside
the Macro Intelligence Layer (MIL). It converts previously computed
information into structured, explainable, deterministic knowledge artifacts.

The Knowledge Layer is **not** a prediction engine and **not** a trading
strategy engine. It is the terminal interpretation stage that answers:

> "What does the current macro environment tell us, based on validated evidence?"

### 1.1 The Interpretation Chain

```
Validated macro evidence
        ↓
Statistical relationships
        ↓
Regime understanding
        ↓
Deterministic knowledge objects
        ↓
Auditable macro intelligence
```

### 1.2 What Knowledge Is (and Is Not)

| Correct (descriptive knowledge) | Incorrect (trading/prediction) |
|---|---|
| "Inflation persistence regime detected with high confidence based on CPI trend, real yield behavior, and historical relationship patterns." | "Gold will rise tomorrow" |
| "USD strength regime is historically associated with tightening monetary conditions." | "Buy USD" |

Knowledge must remain:

- **descriptive** — states what the environment is, not what to do
- **statistical** — derived only from frozen statistical outputs
- **explainable** — every statement is human-readable and traceable
- **provenance-tracked** — every artifact references its upstream inputs
- **deterministic** — same inputs produce identical outputs and hashes
- **immutable** — once created, knowledge never changes
- **auditable** — a complete audit trail exists from source to knowledge

---

## 2. Dependency Boundaries

The Knowledge Engine **never bypasses previous layers** and **never computes
raw statistics again**.

Statistics already belong to `macro_intelligence/statistics/`.
Relationships already belong to `macro_intelligence/relationships/`.
Regime detection/classification already belong to `macro_intelligence/regime/`.

The Knowledge Engine **consumes their frozen outputs only**.

### 2.1 Strict Dependency Direction

```
contracts
    ↓
evidence
    ↓
features
    ↓
statistics
    ↓
relationships
    ↓
regime intelligence
    ↓
knowledge generation
    ↓
macro context
```

### 2.2 Consumption Contract

The generator receives a `KnowledgeInputs` object containing only:

- **Stable identifiers** of upstream artifacts (`evidence_ids`,
  `feature_vector_ids`, `relationship_ids`, `regime_classification_id`,
  `transition_id`).
- **Scalar signals** already computed by upstream layers
  (persistence periods, regime confidence, rolling stability, correlations,
  break indicators, etc.).
- **Optional confidence components** derived from upstream quality scores.

The generator never mutates these inputs. `KnowledgeInputs` is a frozen
dataclass and the generator is stateless and pure.

---

## 3. Module Layout

```
macro_intelligence/knowledge/
├── __init__.py          # Package exports
├── models.py            # KnowledgeObject, KnowledgeProvenance,
│                        #   KnowledgeType, MacroContext, ALGORITHM_VERSION
├── evidence_link.py     # EvidenceLink, EvidenceLinker (provenance binding)
├── pattern.py           # PatternFinding, PatternDetector (rule-based)
├── confidence.py        # ConfidenceComponents, ConfidenceCalculator
├── rules.py             # KnowledgeRule, RULES registry (immutable, versioned)
├── generator.py         # KnowledgeInputs, KnowledgeGenerator (pipeline)
└── context.py           # MacroContextBuilder (context aggregation)
```

### 3.1 Component Responsibilities

| Module | Responsibility |
|---|---|
| `models.py` | Immutable artifacts and taxonomy. |
| `evidence_link.py` | Connects a knowledge object to upstream evidence, features, relationships, regime classification. Mandatory provenance. |
| `pattern.py` | Deterministic rule-based pattern detection. **No ML.** |
| `confidence.py` | Deterministic weighted confidence in `[0.0, 1.0]`. |
| `rules.py` | Versioned, immutable rules. |
| `generator.py` | Orchestrates detector → confidence → provenance → knowledge objects. |
| `context.py` | Aggregates knowledge objects into an immutable `MacroContext`. |

---

## 4. KnowledgeObject Design

`KnowledgeObject` is a **frozen dataclass** (immutable intelligence artifact).

### 4.1 Fields

```
knowledge_id            # KN_{RULE_ID}_{hash}   (deterministic)
knowledge_type          # KnowledgeType enum     (classification)
statement               # human-readable, explainable, descriptive
confidence              # float in [0.0, 1.0]   (deterministic)
supporting_evidence     # tuple[str, ...]        (evidence ids)
supporting_features     # tuple[str, ...]        (feature vector ids)
supporting_relationships# tuple[str, ...]        (relationship ids)
regime_context          # str                    (regime label/id)
algorithm_version       # know-eng/v1.0.0        (permanent)
provenance              # KnowledgeProvenance   (mandatory)
created_timestamp       # datetime               (runtime metadata)
```

### 4.2 Hashing Rules

- Same inputs → same `knowledge_hash`.
- Different evidence → different `knowledge_hash` (provenance participates in the hash).
- Runtime timestamps (`created_timestamp`) **MUST NOT** affect the hash.
- Serialization uses `sort_keys=True` with compact separators for stable ordering.

### 4.3 Validation

`KnowledgeObject.validate()` requires:

- `knowledge_id` starts with `KN_`.
- `statement` is non-empty.
- `confidence` is in `[0.0, 1.0]`.
- Provenance references at least one upstream artifact (`is_complete()`).

---

## 5. KnowledgeType Taxonomy

Eight knowledge classifications — **not** trading signals:

| KnowledgeType | Meaning | Rule |
|---|---|---|
| `REGIME_PERSISTENCE` | A regime has persisted beyond threshold with high confidence. | KNOW-001 |
| `REGIME_TRANSITION` | A regime transition was detected with high confidence. | KNOW-002 |
| `PERSISTENT_RELATIONSHIP` | A correlation is stable over time with meaningful magnitude. | KNOW-003 |
| `CORRELATION_BREAK` | A structural break was detected in a relationship. | KNOW-004 |
| `ANOMALY` | A feature z-score is beyond the anomaly threshold. | KNOW-005 |
| `REGIME_PATTERN` | A dominant regime pattern is observed. | KNOW-006 |
| `RISK_OFF_SAFE_HAVEN` | Risk-off conditions with a safe-haven relationship. | KNOW-007 |
| `TIGHTENING_VOLATILITY` | Tightening monetary conditions with elevated volatility. | KNOW-008 |

Each type has a corresponding immutable rule in `rules.py`.

---

## 6. Algorithms

All algorithms are deterministic, stateless, and purely rule-based.

### 6.1 Pattern Detection (`pattern.py`)

| Pattern | Deterministic Rule |
|---|---|
| `REGIME_PERSISTENCE` | `IF persistence_periods >= 8 AND regime_confidence >= 0.60 AND continuation_probability >= 0.55 THEN REGIME_PERSISTENCE` |
| `REGIME_TRANSITION` | `IF transition_detected AND transition_confidence >= 0.60 THEN REGIME_TRANSITION` |
| `PERSISTENT_RELATIONSHIP` | `IF rolling_stability <= 0.15 AND abs(overall_correlation) >= 0.40 AND sample_size >= 20 THEN PERSISTENT_RELATIONSHIP` |
| `CORRELATION_BREAK` | `IF any structural break with confidence >= 0.50 THEN CORRELATION_BREAK` |
| `ANOMALY` | `IF |z_score| >= 2.0 AND feature_quality >= 0.60 THEN ANOMALY` |
| `REGIME_PATTERN` | `IF dominant_regime present AND regime_confidence >= 0.60 THEN REGIME_PATTERN` |
| `RISK_OFF_SAFE_HAVEN` | `IF risk regime in {risk_off, crisis} AND risk_confidence >= 0.60 AND abs(safe_haven_corr) >= 0.40 THEN RISK_OFF_SAFE_HAVEN` |
| `TIGHTENING_VOLATILITY` | `IF monetary regime in {tightening, hawkish, ...} AND volatility_elevated AND monetary_confidence >= 0.60 THEN TIGHTENING_VOLATILITY` |

No machine learning. No randomness. Every finding records its `rule_id` and
`rule_version`.

### 6.2 Confidence Calculation (`confidence.py`)

Deterministic weighted blend:

| Component | Weight |
|---|---|
| Evidence quality | 30% |
| Feature quality | 20% |
| Relationship stability | 20% |
| Regime confidence | 20% |
| Historical consistency | 10% |

- Missing components contribute `0.0`.
- Components are clamped to `[0.0, 1.0]`.
- Output is rounded to 4 decimals — always in `[0.0, 1.0]`.
- Weight set is versioned and immutable (`know-conf/v1.0.0`).

### 6.3 Provenance Linkage (`evidence_link.py`)

The `EvidenceLinker` connects:

```
KnowledgeObject
        ↓
EvidenceObject
        ↓
FeatureVector
        ↓
RelationshipResult
        ↓
RegimeClassification
```

Every knowledge object must answer **"Why does this knowledge exist?"** —
hence provenance is mandatory.

### 6.4 Generation Pipeline (`generator.py`)

```
KnowledgeInputs (frozen upstream outputs)
        ↓
PatternDetector.detect_all()
        ↓
ConfidenceCalculator.compute()
        ↓
EvidenceLinker.build_provenance()
        ↓
KnowledgeObject (frozen, provenance-tracked, deterministic)
        ↓
sorted by knowledge_id
```

### 6.5 Context Building (`context.py`)

Aggregates knowledge objects into an immutable `MacroContext` with a
deterministic `context_id`, sorted deterministically by `knowledge_id`.

---

## 7. Invariants

| ID | Invariant |
|---|---|
| MIL-KNOW-001 | Knowledge objects are immutable (frozen dataclasses). |
| MIL-KNOW-002 | Knowledge has complete provenance (provenance is mandatory). |
| MIL-KNOW-003 | Same inputs produce identical knowledge. |
| MIL-KNOW-004 | Knowledge generation is deterministic (no randomness). |
| MIL-KNOW-005 | Algorithm versions are permanent (`know-eng/v1.0.0`). |
| MIL-KNOW-006 | Knowledge never mutates source evidence/features. |

Additional derived invariants:

- Runtime timestamps never affect the deterministic hash (MIL-DET-001).
- Rules are immutable and versioned (`know-rules/v1.0.0`).
- Knowledge statements are descriptive — never trading directives.
- No dependency on ResearchOS V1 core, Quant Engine, or Experiment framework.
- No LLM dependency. No ML models.

---

## 8. Extension Rules

1. **Never modify existing rules.** Future changes create a new version
   (e.g., `know-rules/v1.1.0`) rather than mutating old rules.
2. **Never recompute statistics/relationships/regime.**
   The knowledge engine consumes only frozen outputs.
3. **Add new knowledge types via new rules** (e.g., `KNOW-009`) with the
   same deterministic pattern-detection style.
4. **New confidence weight sets** create a new version
   (e.g., `know-conf/v2.0.0`); old weights remain valid.
5. **Keep all new models frozen dataclasses** with deterministic hashing.
6. **Keep provenance mandatory** for every new knowledge object type.

---

## 9. Limitations

- **Not predictive:** knowledge describes the current environment; it does
  not forecast prices or returns.
- **Not prescriptive:** knowledge is not a trading signal. Downstream engines
  (outside this layer) decide how to use it.
- **Only as good as upstream:** knowledge is a faithful interpretation of the
  frozen statistics, relationships, and regime outputs it consumes.
- **Rule-based only:** the pattern detector intentionally does not use machine
  learning, so it cannot discover unknown patterns beyond the defined rules.
- **No LLM:** statements are template-generated for explainability and
  determinism; they are not free-form.
- **No persistence/scheduling/API:** this phase deliberately adds no storage,
  scheduler, UI, API, database, or real-time wiring.

---

*Document Version: know-eng/v1.0.0*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*

